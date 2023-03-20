# Copyright (c) 2022, The Pennsylvania State University
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.

import numpy as np
import time
from scipy.optimize import linprog
from cvxopt import matrix, solvers
solvers.options['show_progress'] = False
solvers.options['maxiters'] = 100
from .exceptions import OptimalLPException
import locomotives.ltd as ltd      # want access to the constants defined here

def basic(route, consist):
    return 0.0

def optimalLP(results):

    power_total = np.array(results['power']['total'])           # power in watts
    times = results['times']                                    # time in seconds
    dist = np.array(results['distances'])                       # distance in meters
    max_battery_power = results['limits']['max_battery_power']
    max_diesel_power = results['limits']['max_diesel_power']
    max_fuelcell_power = results['limits']['max_fuelcell_power']

    # first step is to "chunk" the route
    current_chunk = 3
    chunks = []
    start_time = 0.0
    endurance = 0.0
    energy = 0.0
    num_inters = 0
    for i, (d,power) in enumerate(zip(dist[1:],power_total)):
        if power > max(max_diesel_power, max_fuelcell_power):
            new_chunk = 3  # need all power available
        elif power > 0.0:
            new_chunk = 2 # can power without battery
        else:
            new_chunk = 1 # we can regenerate
        num_inters += 1
        if new_chunk != current_chunk or num_inters >= 50:
            if endurance > 0.0:
                ave_power = energy/endurance
                chunks.append({'power': ave_power, 'endurance': endurance, 'end': d})
            current_chunk = new_chunk
            energy = 0.0
            num_inters = 0
            start_time = times[i]

        endurance = times[i+1] - start_time
        energy = energy + power * (times[i+1]-times[i])

    # we need to add the last chunk yet
    ave_power = energy/endurance
    chunks.append({'power': ave_power, 'endurance': endurance, 'end': d})

    k = len(chunks)

    int_time = np.zeros(k)
    int_power = np.zeros(k)
    int_dist = np.zeros(k)
    for i, chunk in enumerate(chunks):
        int_time[i] = chunk['endurance']
        int_power[i] = chunk['power']
        int_dist[i] = chunk['end']

    # the time lower triangular matrix
    tlt = np.tri(k)*int_time

    # setup the LP
    battEnergyMax = 1.0 * results['limits']['max_battery_energy']*1000*60*60 # convert kw-hrs to watt-secs or joules
    battEnergy0 = 1.0 * battEnergyMax # start at full-charge
    battEnergyMin = 0.0    # 0.1 * battEnergyMax - allow it to use all of the usable energy
    BEUpperBnd = np.full(k, battEnergyMax - battEnergy0)
    BELowerBnd = np.full(k, battEnergyMin  - battEnergy0)
    bvec = np.concatenate((BEUpperBnd, -1.0* BELowerBnd, -1.0*int_power))/1000000
    lb = np.concatenate((np.full(k,0.0), np.full(k, -1.0*max_battery_power)))/1000000
    ub = np.concatenate((np.full(k, max(max_diesel_power, max_fuelcell_power)), np.full(k, max_battery_power)))/1000000

    cvec = np.concatenate((4.0*int_time, 1.0*int_time), axis=None)
    ident = -1.0*np.identity(k)
    Mmat = np.array(np.bmat([[np.zeros_like(tlt), -tlt],[np.zeros_like(tlt), tlt],[ident, ident]]))

    G = np.bmat([Mmat.T, np.eye(2*k), -np.eye(2*k)]).T
    h = (np.bmat([bvec, ub, -lb]).T) # bounds for the variables

    # the workhorse is here - consider changing values of the kktsolver = ‘ldl’, ‘ldl2’, ‘qr’, ‘chol’, or ‘chol2’.
    # the defualt is 'chol'

    res2 = solvers.lp(c=matrix(cvec), G=matrix(G), h=matrix(h), kktsolver='chol')

    # check here to make sure we are 'optimal' status before continuing
    if res2['status'] == 'optimal':
        # create variables to hold ghg and fuel emissions
        ni = len(dist)-1
        diesel = np.zeros(ni+1)
        hydrogen = np.zeros(ni+1)
        ghg_co = np.zeros(ni+1)
        ghg_hc = np.zeros(ni+1)
        ghg_no = np.zeros(ni+1)
        ghg_pm = np.zeros(ni+1)
        resx = np.array(res2['x']).flatten()*1000000
        f_power = resx[:k]
        b_power = resx[-k:]
        # calculate the state of charge for the battery
        battery_charge = np.zeros(ni+1)
        battery_energy = np.zeros(ni+1)
        diesel_energy = np.zeros(ni+1)
        fuelcell_energy = np.zeros(ni+1)
        regen_energy = np.zeros(ni+1)
        lost_energy = np.zeros(ni+1)

        battery_charge[0] = (battEnergy0/1000)/(60*60)
        bp = b_power[0]
        fp = f_power[0]
        i=0
        t0 = times[0]
        for j, (x,t) in enumerate(zip(dist, times)):
            if j>0:
                if max_diesel_power > 0.0:
                    diesel_e = (fp/1000)*((t-t0)/(60*60))
                    fuelcell_e = 0.0
                else:
                    fuelcell_e = (fp/1000)*((t-t0)/(60*60))
                    diesel_e = 0.0
                battery_e = (bp/1000)*((t-t0)/(60*60))
                battery_charge[j] = battery_charge[j-1]-battery_e
                diesel[j] = diesel[j-1] + ltd.BSFC_D * diesel_e/1000    # convert from grams to kgs
                hydrogen[j] = hydrogen[j-1] + ltd.BSFC_H * fuelcell_e/1000 # convert from grams to kgs
                ghg_co[j] = ghg_co[j-1] + ltd.SCO * diesel_e
                ghg_hc[j] = ghg_hc[j-1] + ltd.SHC * diesel_e
                ghg_no[j] = ghg_no[j-1] + ltd.SNO * diesel_e
                ghg_pm[j] = ghg_pm[j-1] + ltd.SPM * diesel_e
                battery_energy[j] = battery_energy[j-1] + max(battery_e,0)
                diesel_energy[j] = diesel_energy[j-1] + diesel_e
                fuelcell_energy[j] = fuelcell_energy[j-1] + fuelcell_e
                regen_energy[j] = regen_energy[j-1] + max(-battery_e,0)



            t0 = t
            if x > int_dist[i]:
                i = i + 1
                bp = b_power[i]
                fp = f_power[i]

        results['perfs'] =  {
            'fuels': (diesel + hydrogen).tolist(),
            'fuel_diesel': diesel.tolist(),
            'fuel_hydrogen': hydrogen.tolist(),
            'fuel_cost': ltd.D_PRICE * diesel[-1] / ltd.D_KG_PER_GAL + ltd.H_PRICE * hydrogen[-1],
            'co': ghg_co.tolist(),
            'hc': ghg_hc.tolist(),
            'no': ghg_no.tolist(),
            'pm': ghg_pm.tolist(),
        }

        results['energy'] = {
            'diesel': diesel_energy.tolist(),
            'battery': battery_energy.tolist(),
            'fuelcell': fuelcell_energy.tolist(),
            'regen': regen_energy.tolist(),
            'lost': lost_energy.tolist(),
            'stored': battery_charge.tolist(),
        }

        power_total = np.zeros(ni)
        power_diesel = np.zeros(ni)
        power_fuelcell = np.zeros(ni)
        power_battery = np.zeros(ni)
        power_regen = np.zeros(ni)

        k = 0       # chunk counter
        for i,d in enumerate(dist[1:]):
            if d > int_dist[k]:
                k = min(k+1, len(chunks))
            power_total[i] = f_power[k] + b_power[k]
            if max_diesel_power > 0.0:
                power_diesel[i] = f_power[k]
            else:
                power_fuelcell[i] = f_power[k]

            if b_power[k]>0:
                power_battery[i] = b_power[k]
                power_regen[i] = 0.0
            else:
                power_battery[i] = 0.0
                power_regen[i] = -1*b_power[k]


        results['power']['total']= power_total.tolist()
        results['power']['diesel'] = power_diesel.tolist()
        results['power']['fuelcell'] = power_fuelcell.tolist()
        results['power']['battery'] = power_battery.tolist()
        results['power']['regen'] = power_regen.tolist()
        
    else:
        print(f"optimal lp failed: {res2['status']}")
        raise OptimalLPException()
        


    return results
