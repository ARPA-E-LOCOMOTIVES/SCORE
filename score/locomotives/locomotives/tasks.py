# Copyright (c) 2022, The Pennsylvania State University
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.

from celery import shared_task
from config.celery import app
import locomotives.ltd as ltd      # want access to the constants defined here
import locomotives.policies as policies # load optimal LP code
from .models import Route, Consist, Policy, LTDResults
import numpy as np
import math
from .exceptions import OptimalLPException
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d
from scipy.optimize import brentq

@app.task(bind=True)
def eval_ltd(self, results_id):
    # get the route, consist, and policy to be evaluated
    # print("Hello from the tack eval_ltd")
    results = LTDResults.objects.get(id=results_id)
    rapid = results.rapid 
    results.result_code = 1     # update result to indicate running
    results.save()
    # place the query set data into dictionaries
    print("in tasks we have route: ", results.route)
    route, consist, policy = ltd.get_ltd_input(results.route, results.consist, results.policy)
    # determine maximum limits on power, energy storage, and braking
    limits = ltd.get_limits(consist, policy)
    max_final_battery = 0.02*limits['max_battery_energy']
    if policy['type']=='hybrid_lp':
        max_final_battery = policy['charge']*limits['max_battery_energy']

    V0 = 0.0

    A, B, C = ltd.get_coefs(consist)

    self.update_state(state='RUNNING',
                      meta={'current': 5, 'total': 100 })

    def train_resistance(speed):
        V = speed * 2.23694                # convert from m/s to mph
        return (A + B*V + C*V*V) * 4.44822 # convert from lbs to Newtons

    # this function is used to end the integration   
    def end_segment(t, x, power, end):
        return end - x[0]
    end_segment.terminal = True

    # this function is used to begin (end) the integration
    def begin_segment(t, x, power, begin):
        return x[0] - begin
    begin_segment.terminal = True

    # this function returns the force applied by the wheels to the track
    def traction_force(v, power):
        if abs(power)< 1.0:
            res = 0.0
        else:
            # if power is negative we aren't going to constrain force since we will be using air brakes?
            if power<0.0:
                res = power/v
            else:
                res = consist['traction_mass']* ltd.G * ltd.MU * 1000
                if v>1.0:
                    res = min(power/v, consist['traction_mass']* ltd.G * ltd.MU * 1000)
        return res

    # define a function for the train dynamics
    # this may change a lot during development, for now it takes in power, eventually it may take in force
    def dynamics(t, x, p, end):
        s = x[0]
        v = x[1]

        s_dot = v
        # need to test that the resistance isn't larger than the traction force if we are nearly stopped
        resistance = train_resistance(v) + track_resistance(s)
        traction = traction_force(v, p)
        # may want to put in a better check here
        if abs(v) <= 0.1:
            force = max(0.0, traction-resistance)
        else:
            force = traction - resistance
        v_dot = force/(consist['mass']*1000)

        return [s_dot, v_dot]

    # define a function that will integrate motion over backward time for each segment.
    def back_est(state, p, begin):
        x1 = state[0]
        v1 = max(0.0, state[1])
        max_time = 100 # we should never have to integrate a single segment for longer than this?
        result = solve_ivp(dynamics, [max_time, 0], [x1, v1], method='RK45', events = begin_segment, args=(p, begin))
        v = result.y[1,-1]
        t = result.t[-1]

        return v


    # define a function that will integrate motion over time for each segment. It is termed cost since it can be used
    # for Decision Processes also
    def cost(state, p, end):
        x0 = state[0]
        v0 = max(0.0, state[1])
        max_time = 100 # we should never have to integrate a single segment for longer than this?
        result = solve_ivp(dynamics, [0, max_time], [x0, v0], method='RK45', events = end_segment, args=(p, end))
        t = result.t[-1]
        v = result.y[1,-1]
        x = result.y[0,-1]
        e = p * t / (1000 * 60 * 60) # convert from joules to kw-hrs

        return (e, t, v)



    iter = True

    route_max_speed = results.policy.max_speed
    high_speed = route_max_speed
    low_speed = 0
    num_iters = 0

    # need to start iterations here to handle changes in route_max_speed
    # stop iterating after 10 loops
    while iter and num_iters<10:
        num_iters=num_iters+1
        # estabilish the intervals for integration
        intervals = ltd.create_intervals(consist, route)
        ni = len(intervals)
        node_distance = np.zeros(ni+1)
        # determine the target speeds
        track_drag = np.zeros(ni+1)
        max_speed = np.zeros(ni+1)
        for i in range(ni):
            interval = intervals[i]
            node_distance[i] = interval['start']
            track_drag[i] = interval['curve_drag'] + interval['gradient_drag']
            max_speed[i] = min(route_max_speed, interval['target_speed'])
            interval['target_speed'] = max_speed[i]
        node_distance[-1] = intervals[-1]['end']
        track_drag[-1] = track_drag[-2]
        track_resistance = interp1d(node_distance, track_drag, bounds_error=False, fill_value=0.0, assume_sorted=True)
        results.status= 10
        results.save()

        # print(limits)
        
        # generate target speeds that include maximum braking constraints
        # these will change depending on powering/braking policy policy
        for i in range(ni-1):
            int0 = intervals[i] # speed we are
            int1 = intervals[i+1] # speed we want in the end
            # check to see if we are slowing down
            j = i
            # we are slowing down and haven't run past the beginning
            while ((int1['target_speed']<int0['target_speed']) and (j>0)):
                state1 = [int1['start'], int1['target_speed']] # ending or beginning state for backward integration
                # apply maximum dynamic braking
                braking_force = traction_force(int1['target_speed'], limits['max_braking'])
                # need to determine if we are "steep" - is the drag + gradient + braking < 0
                speed1 = int1['target_speed']
                drag = int0['curve_drag'] + int0['gradient_drag'] + train_resistance(speed1)
                steep = drag + 0.95 * braking_force               
                if steep < 0.0:
                    # print(f"braking {braking_force} drag: {drag} location {int1['start']} speed {int1['target_speed']}")
                    # we need even more braking add 10% to the minimum required
                    braking_force = -1.1*drag
                    # print(f"braking: {braking} position at start {int1['start']}")

                if rapid:
                    # (de)acceleration
                    acc =  0.95 * braking_force/(consist['mass']*1000)
                    if (acc * 2 * int0['length'] + speed1*speed1)<0.0:
                        # print(f"acc: {acc}, speed1: {speed1} braking_force: {braking_force}")
                        speed0=1.0
                    else:
                        speed0 = math.sqrt(acc * 2 * int0['length'] + speed1*speed1)

                else:
                    braking_power = -0.95*braking_force*speed1
                    # print(f"braking power: {braking_power}")
                    speed0 = back_est(state1, braking_power, int0['start'])

                # print(f"speed1: {speed1} speed0: {speed0} location: {int1['start']}")

                if speed0<int0['target_speed']:
                    # need to move back an interval to slow down sooner
                    int0['target_speed'] = speed0
                    int1 = int0
                    j = j-1
                    int0 = intervals[j]
                else:
                    # enough braking so stop
                    break
        results.status = 40     # we are 40% done running
        results.save()

        # allocate variables required to store results over the simulation run
        # most of these parameter collection variables start at 0 and the record the end of the current interval
        speeds = V0*np.ones(ni+1)
        times = np.zeros(ni+1)
        energy = np.zeros(ni+1)
        stored_energy = np.zeros(ni+1)
        battery_energy = np.zeros(ni+1)
        diesel_energy = np.zeros(ni+1)
        fuelcell_energy = np.zeros(ni+1)
        regen_energy = np.zeros(ni+1)
        lost_energy = np.zeros(ni+1)
        xs = np.zeros(ni+1)
        targets = np.zeros(ni+1)
        diesel = np.zeros(ni+1)
        hydrogen = np.zeros(ni+1)
        # ghg_co2 = np_zeros(ni+1)
        ghg_co = np.zeros(ni+1)
        ghg_hc = np.zeros(ni+1)
        ghg_no = np.zeros(ni+1)
        ghg_pm = np.zeros(ni+1)

        # these are recorded for each interval
        powers = np.zeros(ni)
        diesel_p = np.zeros(ni)
        battery_p = np.zeros(ni)
        fuelcell_p = np.zeros(ni)
        regen_p = np.zeros(ni)
        track_p = np.zeros(ni)
        resist_p = np.zeros(ni)
        lost_p = np.zeros(ni)
        accel_p = np.zeros(ni)

        # capture total stored energy - state with a percentage of max charge
        stored_energy[0] = policy['charge']*limits['max_battery_energy']

        max_power = limits['max_power']

        # perform analysis over the route
        # determine the power required or the speed if at max (or minimum) power
        for i in range(ni):
            interval = intervals[i]
            dist = interval['end']

            x0 = [node_distance[i], speeds[i]]
            
            # what is the desired speed at the end of the interval
            if i < ni-1:
                t_speed = intervals[i+1]['target_speed']
            else:
                # we want to stop at the end
                t_speed = 0.0

            ave_speed = (x0[1]+t_speed)/2.0

            # estimate drag at end of interval if target speed of next interval is achieved
            # maybe use ave_speed
            drag1 = interval['curve_drag'] + interval['gradient_drag'] + train_resistance(ave_speed)
            # what is the force required to accelerate or decelerate from starting state to ending
            acc = (t_speed * t_speed - x0[1] * x0[1])/(2*interval['length'])
            
            p_required = (drag1 + acc * consist['mass'] * 1000) * ave_speed

            if t_speed < 0.1: # we want to stop
                p_required = -limits['max_braking']

            # lets keep this realy simple - either constrained to max power
            # or we put on all the brakes that we need - we can determine where this power flows later
            if p_required > max_power:
                p = max_power
            else:
                p = p_required
                
            if rapid:
                # drag at start of interval
                drag0 = interval['curve_drag'] + interval['gradient_drag'] + train_resistance(x0[1])
                speed0 = x0[1]
                acc = (traction_force(x0[1], p) - drag0)/(consist['mass']*1000)
                if (acc * 2 * interval['length'] + speed0*speed0)<0.1:
                    speed = 0.1
                else:
                    speed = math.sqrt(acc * 2 * interval['length'] + speed0*speed0)
                t = 2 * interval['length']/ (speed0 + speed) # time to travel distance with average speed
                e = p * t

            else:
                # now that we have a power, lets move forward along the route - time integration method
                (e, t, speed) = cost(x0, p, dist)
    
            # lets record the results for the interval

            targets[i] = interval['target_speed']
            speeds[i+1] = speed
            times[i+1] = times[i] + t
            energy[i+1] = energy[i] + e
            xs[i+1] = dist
            powers[i] = p
            # we need to distribute the power between the battery and the diesel
            # test to see if we have energy in the battery before it gets used
            diesel_power = 0.0
            battery_power = 0.0
            fuelcell_power = 0.0
            lost_power = 0.0
            regen_power = 0.0
            # check to see if we can regenerate power from diesel and/or fuelcell
            if policy['type'] in ['score_lp', 'hybrid_lp']:   
                    # we are in optimal lp policy - need to determine if we can stuff energy in battery
                    p_avail = limits['max_diesel_power'] + limits['max_fuelcell_power']
                    if p < p_avail and stored_energy[i]<limits['max_battery_energy']:
                        regen_power = min(p_avail - p, limits['max_regenerative_braking'])

            # applying power to tracks or regen
            if p + regen_power > 0.0:
                p_remain = p + regen_power
                diesel_power = 0.0
                fuelcell_power = 0.0
                battery_power = 0.0
                for source in policy['power_order']:
                    if source == 'diesel':
                        diesel_power = min(limits['max_diesel_power'], p_remain)
                        p_remain = p_remain - diesel_power
                    elif source == 'fuelcell':
                        fuelcell_power = min(limits['max_fuelcell_power'], p_remain)
                        p_remain = p_remain - fuelcell_power
                    elif source == 'battery' and (stored_energy[i]>0.0*limits['max_battery_energy'] or policy['type']=='score_lp'):
                        battery_power = min(limits['max_battery_power'], p_remain)
                        p_remain = p_remain - battery_power

                # we always have diesel and/or fuelcell available
                max_power = limits['max_diesel_power'] + limits['max_fuelcell_power']
                # we only have battery when we have charge OR when we are determining power settings for lp
                # without some limitations this has the possibility of blowing up -> failing the lp
                if stored_energy[i]>0.0*limits['max_battery_energy'] or policy['type'] in ['score_lp', 'hybrid_lp']:
                    max_power = max_power + limits['max_battery_power']

            else:
                # braking - always regenerate when we can - we are not differentiating between dynamic braking and air brakes here - both are lost energy
                if stored_energy[i]<limits['max_battery_energy']:
                    if abs(p) > limits['max_regenerative_braking']:
                        regen_power = limits['max_regenerative_braking']
                        lost_power = abs(p) - regen_power
                    else:
                        regen_power = abs(p)
                        lost_power = 0.0
                else:
                    regen_power = 0.0
                    lost_power = abs(p)


            # calculate energy consumed during the interval
            diesel_e = (diesel_power/1000)*(t/(60*60))  # energy in kw-hr
            fuelcell_e = (fuelcell_power/1000)*(t/(60*60))
            battery_energy[i+1] = battery_energy[i] + (battery_power/1000)*(t/(60*60))
            diesel_energy[i+1] = diesel_energy[i] + diesel_e
            fuelcell_energy[i+1] = fuelcell_energy[i] + fuelcell_e
            regen_energy[i+1] = regen_energy[i] + (regen_power/1000)*(t/(60*60))
            lost_energy[i+1] = lost_energy[i] + (lost_power/1000)*(t/(60*60))
            stored_energy[i+1] = stored_energy[i] - ((battery_power - regen_power)/1000)*(t/(60*60))

            # record the power sources and sinks
            diesel_p[i] = diesel_power
            battery_p[i] = battery_power
            fuelcell_p[i] = fuelcell_power
            regen_p[i] = regen_power
            lost_p[i] = lost_power

            # determine the average speed and position for the interval
            ave_speed = (speeds[i] + speeds[i+1])/2
            ave_pos =(xs[i] + xs[i+1])/2
            resist_p[i] = train_resistance(ave_speed) * ave_speed
            track_p[i] = track_resistance(ave_pos) * ave_speed
            accel_p[i] =((speeds[i+1]-speeds[i])/t)*(consist['mass']*1000) * ave_speed

            # calculate diesel emissions and fuel consumption
            # this should be updated to include actual look ups to the diesel engine data tables
            if limits['max_diesel_power']>0:
                diesel[i+1] = diesel[i] + ltd.BSFC_D * diesel_e/1000    # convert from grams to kgs
                hydrogen[i+1] = hydrogen[i]
                ghg_co[i+1] = ghg_co[i] + ltd.SCO * diesel_e
                ghg_hc[i+1] = ghg_hc[i] + ltd.SHC * diesel_e
                ghg_no[i+1] = ghg_no[i] + ltd.SNO * diesel_e
                ghg_pm[i+1] = ghg_pm[i] + ltd.SPM * diesel_e
            else:
                diesel[i+1] = diesel[i]
                hydrogen[i+1] = hydrogen[i] + ltd.BSFC_H * fuelcell_e/1000
                ghg_co[i+1] = ghg_co[i]
                ghg_hc[i+1] = ghg_hc[i]
                ghg_no[i+1] = ghg_no[i]
                ghg_pm[i+1] = ghg_pm[i]

        results.result = {
            'energy': {
                'diesel': diesel_energy.tolist(),
                'battery': battery_energy.tolist(),
                'fuelcell': fuelcell_energy.tolist(),
                'regen': regen_energy.tolist(),
                'lost': lost_energy.tolist(),
                'stored': stored_energy.tolist(),
            },
            'times': times.tolist(),
            'power': {
                'total': powers.tolist(),
                'diesel': diesel_p.tolist(),
                'battery': battery_p.tolist(),
                'fuelcell': fuelcell_p.tolist(),
                'regen': regen_p.tolist(),
                'track': track_p.tolist(),
                'train': resist_p.tolist(),
                'lost': lost_p.tolist(),
                'accel': accel_p.tolist(),
            },
            'speeds': speeds.tolist(),
            'limits': limits,
            'perfs': {
                'fuels': (diesel + hydrogen).tolist(),  # only one of these will be non-zero
                'fuel_diesel': diesel.tolist(),
                'fuel_hydrogen': hydrogen.tolist(),
                'fuel_cost': ltd.D_PRICE * diesel[-1] / ltd.D_KG_PER_GAL + ltd.H_PRICE * hydrogen[-1] + stored_energy[0] * ltd.E_PRICE,
                'co': ghg_co.tolist(),
                'hc': ghg_hc.tolist(),
                'no': ghg_no.tolist(),
                'pm': ghg_pm.tolist(),
            },
            'targets': targets.tolist(),
            'max': max_speed.tolist(),
            'distances': xs.tolist(),
            'duration': times[-1]
        }

        # we only need perform the analysis once for the user_fixed policy or we have no battery locomotive      
        if policy['type']=='user_fixed' or limits['max_battery_energy']<0.1:
            iter = False
            
        else:
            # test to see if we can even maintain a minum speed at max power
            if min(speeds[5:-5])<2.0:
                iter = False
            else:
                # otherwise we need to check the battery energy constraint
                # for the optimal lp - ie plug-in hybrid option, we need to confirm that
                # the battery is never depleted while taking every opportunity to charge it

                energy_goal = min(stored_energy)-0.08*limits['max_battery_energy'] 

                # end_energy_goal = abs(stored_energy[-1]-max_final_battery)
                end_energy_goal = stored_energy[-1]-1.05*max_final_battery
                # check to see if we every drop below minimum stored energy
                min_test = energy_goal >0
                # check to see if the stored energy at end is near desired - currently +/- 5%
                # end_test = end_energy_goal < 0.05*limits['max_battery_energy']
                end_test = end_energy_goal > 0
                # end_test_2 = abs(end_energy_goal)/limits['max_battery_energy']<0.05
                end_test_2 = end_test and (end_energy_goal < 0.05*limits['max_battery_energy'])

                if low_speed <1.0:
                    # couple of tests to see if we can succeed at max speed
                    if policy['type']=='score_lp' and min_test:
                        # first time through low_speed should be "zero"
                        # if we have energy in the battery throughout we are good to go
                        iter = False
                    # elif policy['type']=='hybrid_lp' and ((min_test and energy_goal<.02*limits['max_battery_energy'] and stored_energy[-1]>max_final_battery) or (min(stored_energy)>0 and end_test)):
                    elif policy['type']=='hybrid_lp' and (min_test and  end_test):
                        # this one is much more complicated - two combined conditions need to be tested
                        iter = False

                    else:
                        # first time through - we need to go slower
                        # need to select a speed to bound the response
                        # print('first time through, adding 10mph to low speed')
                        high_speed = route_max_speed
                        route_max_speed = 10 * ltd.MPH2MPS # set low to 10 mph
                        low_speed = route_max_speed  # should keep us from coming back here
                        iter = True
                else: 
                    # not the first time through - so determine which bounds to move
                    # print('changing speed bounds ', energy_goal, end_energy_goal)
                    if policy['type']=='score_lp' and min_test:
                        # we have energy at new speed - move lower bound
                        # print(('changing low speed - score', energy_goal))
                        low_speed = route_max_speed
                    # elif policy['type']=='hybrid_lp' and ((min_test and stored_energy[-1]>max_final_battery) or (min(stored_energy)>0 and end_test)):
                    elif policy['type']=='hybrid_lp' and (min_test and end_test):
                        low_speed = route_max_speed
                        # print('changing low speed - hybrid', energy_goal, end_energy_goal)
                    else:
                        # need a check to see if the route_max_speed is already at low
                        # speed and we still can't meet criterion for iteration
                        if route_max_speed < 11 * ltd.MPH2MPS:
                            # we can't do it - stop iteration
                            iter = False
                        else:
                            # we need to move upper bound
                            # print('changing high speed')
                            high_speed = route_max_speed

                    # need to determine the next speed setting to test
                    # this should make sure it is positive to not have lp fail afterwards
                    if policy['type']=='score_lp' and energy_goal<50 and energy_goal>0:
                        # we are done
                        # this drives the energy_goal down to zero which should also be maximizing speed
                        iter = False
                    # elif policy['type']=='hybrid_lp' and  ((min_test and energy_goal<.02*limits['max_battery_energy'] and stored_energy[-1]>max_final_battery) or (min(stored_energy)>0 and end_test)):
                    elif policy['type']=='hybrid_lp' and (min_test and end_test_2):
                        # we are also done
                        # this seems to be a little too simple - want to find the maximum speed that satifies these coditions
                        # there are two separate constraints to deal with here. The first is if we are
                        # print((min_test, min(stored_energy), end_test_2, stored_energy[-1], route_max_speed))
                        iter = False
                    else:
                        # the relationship between speed and min stored energy is not very linear - this may not perform very well
                        # may want to consider simpler bisection method - this current method is the Secant method and may nto converge
                        # in some instances
                        # Bisection method
                        # print('changing route_max_speed')
                        route_max_speed = (low_speed+high_speed)/2.0
                        iter = True
            # print((iter, policy['type'], low_speed, high_speed, route_max_speed, energy_goal, stored_energy[-1], min(stored_energy)))  


    # take off the first and last 5 elements of the speed array
    test_speeds = speeds[5:-5]
    # if the minimum speed is less than 2 m/s call the simulation a failure
    # or if the route max speed is too low (probably failed above iteration)
    if min(test_speeds)<2.0 or route_max_speed < 11 * ltd.MPH2MPS:
        results.result_code = 2
    else:  
        if policy['type'] in ['score_lp', 'hybrid_lp'] and limits['max_battery_energy']>0.0: # have a hybrid system with a battery
            results.status = 80
            results.save()
            if num_iters<10:
                try:
                    results.result = policies.optimalLP(results.result, policy)
                    results.result_code = 0
                except OptimalLPException:
                    results.result_code = 2
            else:
                results.result_code = 3
        else:
            results.result_code = 0

    results.status=100
    results.save()

    return