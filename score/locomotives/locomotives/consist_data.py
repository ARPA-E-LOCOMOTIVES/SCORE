# Copyright (c) 2022, The Pennsylvania State University
# All rights reserved.

from .models import ConsistCar

# fix this as it is copied from api api_views
KW2HP = 1.34102     # convert kw to hp
TONNE2TON = 1.10231 # convert tonne (1000 kg) to ton (2000 lbs)
def get_consist_data(consist):
    consist_data = {}
    consist_cars = ConsistCar.objects.filter(consist=consist)
    consist_data["name"] = consist.name
    consist_data["number_cars"] = len(consist_cars)
    total_mass = 0
    total_freight_mass = 0
    total_trailing_mass = 0
    total_length = 0
    total_power = 0
    max_battery_energy = 0

    for i, car in enumerate(consist_cars):
        total_length += car.car.length
        if car.car.type == 'C':
            total_power += car.car.fuelcelllocomotive.max_power
            total_mass += car.car.weight
        if car.car.type == 'D':
            total_power += car.car.diesellocomotive.max_power
            total_mass += car.car.weight
        if car.car.type == 'E':
            total_power += car.car.electriclocomotive.max_power_out
            max_battery_energy += car.car.electriclocomotive.max_usable_energy
            total_mass += car.car.weight
        if car.car.type == 'F':
            if car.loaded:
                total_trailing_mass += car.car.weight
                total_freight_mass += car.car.weight-car.car.freightcar.empty_weight
                total_mass += car.car.weight
            else:
                total_trailing_mass += car.car.freightcar.empty_weight
                total_mass += car.car.freightcar.empty_weight

    consist_data["power_hp"] = int(KW2HP*total_power)  # convert kw to hp
    consist_data["weight_tons"] = int(TONNE2TON*total_mass) # convert 1,000 kg (tonne) to 2000 lbs (ton)
    consist_data["trailing_tons"] = int(TONNE2TON*total_trailing_mass)
    consist_data["freight_tons"] = int(TONNE2TON*total_freight_mass)
    consist_data['battery_energy'] = int(max_battery_energy)
    consist_data["power_to_weight"] = 0
    if total_mass > 0: # in case a user enters a bad consist
        consist_data["power_to_weight"] = round(KW2HP*total_power/(TONNE2TON*total_freight_mass),2)
    return consist_data
