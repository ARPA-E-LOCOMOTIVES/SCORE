# Copyright (c) 2022, The Pennsylvania State University
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.


import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d
from scipy.optimize import brentq
import time

from .models import Segment, ConsistCar, PowerToWheels, Route, Route2, Line


# the following constants are for fuel and ghg emissions
# they are in units of grams/kw-hr
SHC = 0.5
SCO = 1.15
SNO = 14.0
SPM = 0.1
BSFC_D = 240
BSFC_H = 64

D_KG_PER_GAL = 3.22     # density of diesel kg/gal
D_PRICE = 5.10          # cost of diesel $/gal
H_PRICE = 6.5          # cost of liquid hydrogen $/kg
E_PRICE = 0.15          # cost of electric per kw-hr

G = 9.81            # acceleration of gravity
MU = 0.30           # coefficient of friction

MPH2MPS = 0.44704   # convert MPH to m/s

def get_segments(route):
    segment_list = Segment.objects.filter(route=route).order_by('segment_order')

    # modify the data to be closer to what is needed by the LTD model
    segment_data = []
    total_length = 0.0
    for segment in segment_list:
        degrees = 0
        total_length = total_length + segment.arc_distance
        if segment != 0 and segment.turn_type != 0:
            degrees = 5728.6/(segment.radius_curvature*3.28084)
        else:
            degrees = 0.0

        seg = {
            'length': segment.arc_distance,
            'degrees' : degrees,
            'gradient': segment.gradient,
            'max_speed': segment.max_speed,
            'order': segment.segment_order,
            'distance': total_length
        }
        segment_data.append(seg)

    route_data = {
        'segments': segment_data,
        'total_length': total_length
    }

    return route_data


def get_lines(route):
    # this will get the lines for a route
    # it will also add the starting elevation
    route = Route2.objects.get(pk=route)
    # we take the path and get line segments in order
    # to do this we select a line segment that has two consecutive points as to and fr
    path = route.path
    segment_data = []
    total_length = 0.0
    order = 0
    start_elevation = -1.0
    print(len(path))
    for i in range(len(path)-1):
        nodes = [path[i],path[i+1]]
        lines = Line.objects.filter(from_node__in=nodes, to_node__in=nodes).order_by('length')
        if lines.count() > 0:
            line = lines[0]
            d = np.array(line.distance)
            # print(line.fra_id, line.distance)
            if line.from_node==nodes[0]:
                # forward travel - maintain order
                for j in range(len(d)):
                    if i==0 and j==0:
                        start_elevation = line.elevation[0]
                    total_length=total_length+d[j]
                    seg = {'length': d[j],
                           'degrees' : line.curvature[j],
                           'gradient': line.gradient[j],
                           'distance': total_length,
                           'max_speed': line.max_speed[j],
                           'elevation': line.elevation[j+1],
                           'order': order
                    }
                    order=order+1
                    segment_data.append(seg)
            else:
                # reverse travel
                for j in range(len(d)):
                    k = len(d)-(j+1)
                    if i==0 and j==0:
                        start_elevation = line.elevation[-1]
                    total_length=total_length+d[k]
                    print(i, j, k, len(line.elevation))
                    seg = {'length': d[k],
                           'degrees': line.curvature[k],
                           'gradient': -line.gradient[k],
                           'distance': total_length,
                           'max_speed': line.max_speed[k],
                           'elevation': line.elevation[k+1],
                           'order': order
                    }
                    order=order+1
                    segment_data.append(seg)

    route_data = {
        'segments': segment_data,
        'start_elevation': start_elevation,
        'total_length': total_length
    }

    return route_data

def get_elevations(route):
    route = Route2.objects.get(pk=route)
    # we take the path and get line segments in order
    # to do this we select a line segment that has two consecutive points as to and fr
    path = route.path
    elevations = []    

    for i in range(len(path)-1):
        nodes = [path[i],path[i+1]]
        lines = Line.objects.filter(from_node__in=nodes, to_node__in=nodes).order_by('length')
        if lines.count() > 0:
            line = lines[0]
            d = np.array(line.distance)
            # print(line.fra_id, line.distance)
            if line.from_node==nodes[0]:
                # forward travel - maintain order
                for j in range(len(d)):
                    elevations.append(line.elevations[j])
                if i == (len(path)-2):
                    elevations.append(line.elevations[j+1])
                
                

            else:
                # reverse travel
                for j in range(len(d)):
                    k = len(d)-(j+1)
                    elevations.append(line.elevations[k])
                if i == (len(path)-2):
                    elevations.append(line.elevations[k+1])

    elevation_data = {'elevations': elevations}
    return elevation_data

def update_elevations(route, elevations, gradients):
    r = Route2.objects.get(pk=route)

    # this routine needs to go through each Line segment and update the elevations in it
    # This is a tedious process that requires very careful book-keeping on the list of values
    path = r.path
    start = 0
    for i in range(len(path)-1):
        nodes = [path[i],path[i+1]]
        lines = Line.objects.filter(from_node__in=nodes, to_node__in=nodes).order_by('length')
        if lines.count() > 0:
            line = lines[0]
            ld = len(line.distance)
            # print(start, ld, len(elevations), len(gradients))
            # print(line.fra_id, line.distance)
            if line.from_node==nodes[0]:
                # forward travel - maintain order
                eles = elevations[start:start+ld+1]
                grads = gradients[start:start+ld]
            else:
                # reverse travel
                eles = elevations[start:start+ld+1][::-1]
                grads = list(-np.array(gradients[start:start+ld][::-1]))
            start = start + ld
            line.elevation=eles
            line.gradient=grads
            # print(i, ld, len(grads), len(eles))
            # lets not save it to start - don't want to mess things up
            line.save()
            # print(line)

    return 1


def get_ltd_input(route, consist, policy):

    # route_data = get_segments(route)
    route_data = get_lines(route)

    consist_list = ConsistCar.objects.filter(consist=consist).order_by('position')

    element_list = []
    distance = 0
    max_power = 0
    max_diesel_power = 0
    max_fuelcell_power = 0
    max_storage_power = 0
    max_regen_power = 0
    max_db_power = 0
    traction_mass = 0
    for car in consist_list:
        if car.car.type == 'D':
            loco = car.car.diesellocomotive
            # non-leading locomotive
            max_power += loco.max_power*1000
            max_diesel_power += loco.max_power*1000
            max_db_power += loco.max_power*1000/0.85
            traction_mass += loco.weight
            car_type = 14
            if car.position == 1:
                car_type = 13
            p2w = PowerToWheels.objects.filter(car=loco).order_by('power_level')
            l = p2w.count()
            power_level = np.zeros(l)
            fuel_consumption = np.zeros(l)
            ghg_hc_emissions = np.zeros(l)
            ghg_co_emissions = np.zeros(l)
            ghg_no_emissions = np.zeros(l)
            ghg_pm_emissions = np.zeros(l)

            for i, row in enumerate(p2w):
                power_level[i]=row.power_level
                fuel_consumption[i] = row.fuel_consumption
                ghg_hc_emissions[i] = row.ghg_hc_emissions
                ghg_co_emissions[i] = row.ghg_co_emissions
                ghg_no_emissions[i] = row.ghg_no_emissions
                ghg_pm_emissions[i] = row.ghg_pm_emissions

            element = {
                'name': loco.name,
                'id': loco.id,
                'car_type': car_type,
                'type': loco.type,
                'mass': loco.weight,
                'num_axles': loco.number_axles,
                'max_power': loco.max_power*1000,
                'brake_efficiency': 0.85,
                'max_db_power': loco.max_power*1000/ 0.85,
                'length': loco.length,
                'distance': distance,
                'power_to_wheels': {
                    'power_level' : power_level,
                    'fuel_consumption': fuel_consumption,
                    'ghg_hc_emissions': ghg_hc_emissions,
                    'ghg_co_emissions': ghg_co_emissions,
                    'ghg_no_emissions': ghg_no_emissions,
                    'ghg_pm_emissions': ghg_pm_emissions
                }
            }
        elif car.car.type == 'E':
            loco = car.car.electriclocomotive
            # non-leading locomotive
            max_power += loco.max_power_out*1000
            max_storage_power += loco.max_power_in*1000
            max_regen_power += loco.max_power_in*1000/(loco.efficiency_in/100)
            traction_mass += loco.weight
            car_type = 14
            if car.position == 0:
                car_type = 13
            element = {
                'name': loco.name,
                'id': loco.id,
                'car_type': car_type,
                'type': loco.type,
                'mass': loco.weight,
                'num_axles': loco.number_axles,
                'max_power': loco.max_power_out*1000,
                'max_regen_power': loco.max_power_out*1000/(loco.efficiency_in/100),
                'efficiency_in': loco.efficiency_in,
                'efficiency_out': loco.efficiency_out,
                'max_usable_energy': loco.max_usable_energy,
                'length': loco.length,
                'power_in': loco.power_in,
                'power_out': loco.power_out,
                'distance': distance
            }
        elif car.car.type == 'C':  # fuel cell
            loco = car.car.fuelcelllocomotive
            max_power += loco.max_power*1000
            max_fuelcell_power += loco.max_power*1000
            traction_mass += loco.weight
            car_type = 14
            if car.position == 1:
                car_type = 13
            element = {
                'name': loco.name,
                'id': loco.id,
                'car_type': car_type,
                'type': loco.type,
                'mass': loco.weight,
                'num_axles': loco.number_axles,
                'max_power': loco.max_power*1000,
                'max_db_power': loco.max_power*1000/ 0.85,
                'length': loco.length,
                'distance': distance
            }
        elif car.car.type == 'F':
            freight = car.car.freightcar
            weight = freight.empty_weight
            if car.loaded:
                weight = freight.weight
            element = {
                'name': freight.name,
                'id': freight.id,
                'car_type': 4,
                'type': freight.type,
                'mass': weight,
                'length': freight.length,
                'num_axles': freight.number_axles,
                'distance': distance
            }
        else:
            print("car","error", car.id)
            element = None

        if element is not None:
            element_list.append(element)
        distance + element['length']

    mass = 0
    length = 0
    for car in element_list:
        mass = mass + car['mass']
        length = length + car['length']

    consist_data = {
        'elements': element_list,
        'max_power': max_power,
        'max_diesel_power': max_diesel_power,
        'max_fuelcell_power': max_fuelcell_power,
        'max_db_power': max_db_power,
        'max_storage_power': max_storage_power,
        'max_regen_power': max_regen_power,
        'traction_mass': traction_mass,
        'mass': mass,
        'length': length
    }

    policy_data = {
        'type': policy.type,
        'power_order': policy.power_order,
        'braking': policy.braking,
        'max_speed': policy.max_speed,
    }

    return route_data, consist_data, policy_data


def get_coefs(consist):
    # Calculate coeffients for the second order equation of train resistance
    # This seems to be the most computationally efficient approach
    Cd = [4.9, 5.3, 12.0, 4.2, 12.0, 7.1, 5.5, 5.0, 5.0, 5.5, 3.5, 2.0, 24.0, 5.0, 12.3, 7.1]
    area = [140, 140, 140, 105, 105, 125, 95, 25, 125, 145, 130, 110, 160, 160, 150, 170]
    A = 0.0
    B = 0.0
    C = 0.0
    for car in consist['elements']:
        tons = car['mass'] * 1.10231
        type = car['car_type'] - 1
        A += (1.5 + 18 * car['num_axles']/tons)*tons
        B += 0.03 * tons
        C += Cd[type]*area[type]/10000
    return A, B, C
    

def get_limits(consist, policy):
    max_power = 0.0
    max_diesel_power = 0.0
    max_fuelcell_power = 0.0
    max_dynamic_braking = 0.0
    max_battery_power = 0.0
    max_regenerative_braking = 0.0
    max_battery_energy = 0.0


    # look for all of the locomotives in the consist
    # create a list of power sources 
    for car in consist['elements']:
        if car['type'] == 'D':  # diesel
            max_power = max_power + car['max_power']
            max_diesel_power = max_diesel_power + car['max_power']
            max_dynamic_braking = max_dynamic_braking + car['max_db_power']
        elif car['type'] == 'E': # battery
            max_battery_energy = max_battery_energy + car['max_usable_energy']
            # these values can be assigned no matter the policy - if there is not energy storage the battery is not used
            max_power = max_power + car['max_power']
            max_battery_power = max_battery_power + car['max_power']
            max_dynamic_braking = max_dynamic_braking + car['max_regen_power']
            max_regenerative_braking = max_regenerative_braking + car['max_regen_power']
        elif car['type'] == 'C':  # fuel cell
            max_power = max_power + car['max_power']
            max_fuelcell_power = max_fuelcell_power + car['max_power']
            max_dynamic_braking = max_dynamic_braking + car['max_db_power']

    if policy['braking'] == 'maximum_braking':
        max_braking = max_dynamic_braking
    elif policy['braking'] == 'maximum_regen':
        max_braking = max_regenerative_braking
    else:    # coasting policy
        max_braking = 0.0

    limits = {
        'max_power': max_power,
        'max_diesel_power': max_diesel_power,
        'max_battery_power': max_battery_power,
        'max_fuelcell_power': max_fuelcell_power,
        'max_battery_energy': max_battery_energy,
        'max_braking': max_braking,
        'max_dynamic_braking': max_dynamic_braking,
        'max_regenerative_braking': max_regenerative_braking,
    }

    return limits

# This routine creates the intervals, calculates the gradiant and curvature drags,
# and sets the target_speeds for each interval that can satisfy the max_speed constraints
# for the segments in the route

def create_intervals(consist, route, deltaX=100):
    mass = consist['mass']
    length = consist['length']

    # generate intervals for the segments that are more uniform
    intervals = []
    start = 0
    for segment in route['segments']:
        if segment['length']>0:  # ignore zero length segments
            num_intervals = int(np.floor(segment['length']/deltaX))
            dx = segment['length']/(num_intervals+1)
            for x in range(num_intervals+1):
                interval = {
                    'start': start,
                    'length': dx,
                    'end': start+dx,
                    'target_speed': segment['max_speed'],
                    'segment_number': segment['order']
                }
                intervals.append(interval)
                start = start + dx

    # total number of intervals
    ns = len(intervals)

    # we need to calculate the track drag for the consist
    # this is done at each interval to create an interpolating function
    # there may be faster ways of doing this, but for now we use nested loops

    # additionally, we need to calculate the "dialated" max speeds as a result of
    # the length of the consist
    lead_num = 0
    segment_num = lead_num
    lead_segment = route['segments'][lead_num]
    current_segment = route['segments'][segment_num]
    for i in range(ns):
        # location of the start of the consist
        interval = intervals[i]
        x = interval['start']
        if x > lead_segment['distance']:
            # move the lead into the next segment
            lead_num += 1
            segment_num = lead_num
            lead_segment = route['segments'][lead_num]
            current_segment = route['segments'][segment_num]

        # loop through all the cars of the consist
        drag = 0
        gdrag = 0
        cdrag = 0
        for car in consist['elements']:
            car_ton = car['mass'] * 1.10231   # convert from tonnes to tons
            # we need to figure out which segment we are in
            if (x-car['distance']) < current_segment['distance']:
                segment_num -= 1
            if segment_num < 0:
                # we are at the beginning so reset segment_num and don't estimate a drag
                segment_num = 0
                car_gdrag = 0.0
                car_cdrag = 0.0
            else:
                current_segment = route['segments'][segment_num]
                # the first element is the gradient drag, the second is curvature drag * should use 0.4 for curves
                if abs(current_segment['gradient'])>0.02:
                    print(current_segment)
                car_gdrag = 1000*car['mass']*G*current_segment['gradient']
                car_cdrag = 0.8*car_ton*current_segment['degrees']*4.44822
                # modify target speed for the interval if necessary
                interval['target_speed'] = min(interval['target_speed'], current_segment['max_speed'])

            cdrag = cdrag + car_cdrag
            gdrag = gdrag + car_gdrag
        interval['curve_drag'] = cdrag
        interval['gradient_drag'] = gdrag

    # we want to end the route with a stop so add a very short element with a zero target speed at the end
    interval = intervals[-1]
    dx = 1.0
    end_interval = {
        'start': interval['end'],
        'length': dx,
        'end': interval['end']+dx,
        'target_speed': 1.0,  # not sure why 1.0 instead of 0.0 to stop
        'segment_number': interval['segment_number'],
        'curve_drag': interval['curve_drag'],
        'gradient_drag': interval['gradient_drag']
    }
    intervals.append(end_interval)

    return intervals

def get_elevations(route_id):
    route = Route.objects.get(id=route_id)
    # route_data = get_segments(route)
    # segments = route_data['segments']
    segments = Segment.objects.filter(route=route).order_by('segment_order').all()
    route_dist_seg = 0
    elevation_data = []
    elevation_gain = 0.0
    elevation_loss = 0.0
    for i, seg in enumerate(segments):
        route_dist_seg += seg.arc_distance
        elevation_data.append([route_dist_seg, seg.locations.all()[1].smooth_elev_m])
    last_elevation = elevation_data[0][1]
    for x,z in elevation_data:
        elevation_change = z - last_elevation
        if elevation_change < 0:
            elevation_loss += abs(elevation_change)
        else:
            elevation_gain += elevation_change
        last_elevation = z
    return elevation_data, elevation_gain, elevation_loss




def create_perf_func(consist):
    # create a dictionary of functions for the consist
    # it is assumed that the power levels start with -1 for DB
    # have a 0 level for idle and 8 notch levels
    # we add them together for all diesel engines to held at the same power
    # levels
    diesel_data = {
        'power': np.zeros(10),
        'fuel': np.zeros(10),
        'co': np.zeros(10),
        'hc': np.zeros(10),
        'no': np.zeros(10),
        'pm': np.zeros(10),
    }

    battery_data = {
        'SOC': np.zeros(10),
        'power': np.zeros(10),
        'in': np.zeros((10,10)),
        'out': np.zeros((10,10)),
    }

    for car in consist['elements']:
        if car['type']=='D':
            p2w = car['power_to_wheels']
            diesel_data['power'] = diesel_data['power'] + p2w['power_level']
            diesel_data['fuel'] = diesel_data['fuel'] + p2w['fuel_consumption']
            diesel_data['co'] = diesel_data['co'] + p2w['ghg_co_emissions']
            diesel_data['hc'] = diesel_data['hc'] + p2w['ghg_hc_emissions']
            diesel_data['no'] = diesel_data['no'] + p2w['ghg_no_emissions']
            diesel_data['pm'] = diesel_data['pm'] + p2w['ghg_pm_emissions']

    # set the first power level to -1 no matter what - it is a flag for any dynamic braking
    diesel_data['power'][0]=-1.0
    # create a linear intperpolating function for the table of values
    # fill with the dynamic braking level for all values outside of the table
    # this should handle braking at any level. The max power should limit the other end.
    diesel = {'data': diesel_data}
    if diesel_data['power'][2]>0:
        diesel.update({
            'fuel': interp1d(diesel_data['power'], diesel_data['fuel'], bounds_error=False, fill_value=diesel_data['fuel'][0]),
            'co': interp1d(diesel_data['power'], diesel_data['co'],  bounds_error=False, fill_value=diesel_data['co'][0]),
            'hc': interp1d(diesel_data['power'], diesel_data['hc'],  bounds_error=False, fill_value=diesel_data['hc'][0]),
            'no': interp1d(diesel_data['power'], diesel_data['no'],  bounds_error=False, fill_value=diesel_data['no'][0]),
            'pm': interp1d(diesel_data['power'], diesel_data['pm'],  bounds_error=False, fill_value=diesel_data['pm'][0]),
        })

    battery = {
        'data': battery_data,
    }

    return {
        'diesel': diesel,
        'battery': battery,
        'fuel_cell': {},
    }

