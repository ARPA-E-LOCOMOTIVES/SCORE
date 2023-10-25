# Copyright (c) 2022, The Pennsylvania State University
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.


from re import T
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.urls import reverse
from django.db.models.signals import post_init
from django.contrib.auth.models import User, Group
from django.core.serializers.json import DjangoJSONEncoder
from pytz import timezone
import datetime

class Route(models.Model):
    name = models.CharField(max_length=1000)
    group = models.ForeignKey(Group, default=None, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, default=None, null=True, on_delete=models.CASCADE)
    cached_route_line = models.JSONField(null=True, blank=True) # cache route line for faster display

    def get_absolute_url(self):
        return reverse('route-detail', kwargs={'pk': self.pk})

class RouteSchedule(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

class Location(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    x = models.FloatField()
    y = models.FloatField()
    elev_m = models.FloatField()
    smooth_elev_m = models.FloatField(null=True, blank=True)

class Locality(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    net = models.CharField(max_length=1, null=True, blank=True)
    tracks = models.CharField(max_length=1, null=True, blank=True)
    city_fips = models.IntegerField(null=True, blank=True)
    state_fips = models.IntegerField(null=True, blank=True)
    state_abbrev = models.CharField(max_length=2, null=True, blank=True)
    time_zone = models.CharField(max_length=1, null=True, blank=True)
    avg_winter_temp = models.FloatField(null=True, blank=True)
    avg_spring_temp = models.FloatField(null=True, blank=True)
    avg_summer_temp = models.FloatField(null=True, blank=True)
    avg_fall_temp = models.FloatField(null=True, blank=True)
    avg_winter_pressure = models.FloatField(null=True, blank=True)
    avg_spring_pressure = models.FloatField(null=True, blank=True)
    avg_summer_pressure = models.FloatField(null=True, blank=True)
    avg_fall_pressure = models.FloatField(null=True, blank=True)

class Segment(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    locations = models.ManyToManyField(Location)                                # 2 locations
    locality = models.ForeignKey(Locality, on_delete=models.CASCADE, null=True, blank=True)
    gradient = models.FloatField()
    arc_distance = models.FloatField()
    radius_curvature = models.FloatField()
    turn_type = models.IntegerField(null=True, blank=True)
    max_speed = models.FloatField(null=True, blank=True)
    segment_order = models.IntegerField(null=True)

class SpeedRestriction(models.Model):
    route_schedule = models.ForeignKey(RouteSchedule, on_delete=models.CASCADE)
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE)
    max_speed = models.FloatField(null=True, blank=True)
    stop_duration = models.FloatField(null=True, blank=True)

class Railroad(models.Model):
    code = models.CharField(max_length=4)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.code

class Line(models.Model):
    fra_id = models.IntegerField()    
    from_node = models.IntegerField()
    to_node = models.IntegerField()
    rights = models.ManyToManyField(Railroad)
    segment = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    geometry = models.JSONField(encoder=DjangoJSONEncoder,  null=True, blank=True)

    def __str__(self):
        return self.fra_id

class Yard(models.Model):
    code = models.CharField(max_length=4)
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=2)
    location = models.ForeignKey(Line, on_delete=models.CASCADE, null=True, blank=True)
    owner = models.ForeignKey(Railroad, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name
    
class Route2(models.Model):
    origin = models.ForeignKey(Yard, on_delete=models.CASCADE, related_name='origin')
    destination = models.ForeignKey(Yard, on_delete=models.CASCADE, related_name='destinaton')
    owner = models.ForeignKey(Railroad, on_delete=models.CASCADE, null=True, blank=True)
    line = models.ManyToManyField(Line, through='RouteLine')

    def __str__(self):
        return self.origin.name + ' - ' + self.destination.name
    
class RouteLine(models.Model):
    line = models.ForeignKey(Line, on_delete=models.CASCADE)
    route = models.ForeignKey(Route2, on_delete=models.CASCADE)
    order = models.IntegerField()

class CarType(models.Model):
    code = models.CharField(max_length=1)
    description = models.CharField(max_length=100)
    type = models.IntegerField(null=True)

    def __str__(self):
        return self.description

class Car(models.Model):
    TYPE_CHOICES = [
        ( 'F', "FreightCar"),
        ( 'D', "DieselLocomotive"),
        ( 'E', "ElectricLocomotive"),
        ( 'C', "FuelCellLocomotive"),
    ]
    name = models.CharField(max_length=50, null=True, blank=True)
    aar_type = models.ForeignKey(CarType, null=True, on_delete=models.CASCADE)
    type = models.CharField(max_length=1, null=True, choices=TYPE_CHOICES)
    description = models.CharField(max_length=50, null=True, blank=True)
    length = models.FloatField(null=True, blank=True)
    width = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    number_axles = models.IntegerField(null=True, blank=True)
    air_braking_max_force = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    parent_id = models.IntegerField(null=True, blank=True)
    most_recent_version = models.BooleanField(default=False)

    group = models.ForeignKey(Group, default=None, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, default=None, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


# Consist schema
class Consist(models.Model):
    name = models.CharField(max_length=100)
    acquisition_cost = models.FloatField(null=True, blank=True)
    parent_id = models.IntegerField(null=True, blank=True)
    most_recent_version = models.BooleanField(default=False)

    group = models.ForeignKey(Group, default=None, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, default=None, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class ConsistCar(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    consist = models.ForeignKey(Consist, on_delete=models.CASCADE)
    position = models.IntegerField()
    loaded = models.BooleanField(default=True)

def initConsistCar(**kwargs):
    instance = kwargs.get('instance')
    # may want to put something in here later, but nothing for now, can't increment here

post_init.connect(initConsistCar, ConsistCar)


class FreightCar(Car):
    empty_weight = models.FloatField(null=True, blank=True)

def initFreightCar(**kwargs):
    instance = kwargs.get('instance')
    instance.type = 'F'

post_init.connect(initFreightCar, FreightCar)

class DieselLocomotive(Car):
    fuel_capacity = models.FloatField(null=True, blank=True)
    acquisition_cost = models.FloatField(null=True, blank=True)
    max_power = models.FloatField(null=True, blank=True)

def initDieselLocomotive(**kwargs):
    instance = kwargs.get('instance')
    instance.type = 'D'


post_init.connect(initDieselLocomotive, DieselLocomotive)

class LocomotiveModel(models.Model):
    model = models.CharField(max_length=20)
    manufacturer = models.CharField(max_length=10)

    def __str__(self):
        return self.model

class Tier(models.Model):
    tier = models.CharField(max_length=20)

    def __str__(self):
        return self.tier

class Fuel(models.Model):
    name = models.CharField(max_length=40)

    def __str__(self):
        return self.name

class LAR(models.Model):
    unit_name = models.CharField(max_length=50)
    model = models.ForeignKey(LocomotiveModel, on_delete=models.CASCADE)
    tier = models.ForeignKey(Tier, on_delete=models.CASCADE)
    fuel = models.ForeignKey(Fuel, null=True, on_delete=models.CASCADE)
    build_date = models.DateField(null=True, blank=True)
    rebuild_date = models.DateField(null=True, blank=True)
    test_data = models.DateField(null=True, blank=True)

POWER_LEVELS = {
    ('LI', 'idle'),
    ('DB', 'dynamic brake'),
    ('N1', 'notch 1'),
    ('N2', 'notch 2'),
    ('N3', 'notch 3'),
    ('N4', 'notch 4'),
    ('N5', 'notch 5'),
    ('N6', 'notch 6'),
    ('N7', 'notch 7'),
    ('N8', 'notch 8')
    }

class Emission(models.Model):
    LAR = models.ForeignKey(LAR, on_delete=models.CASCADE)
    power_level= models.CharField(max_length=20, choices=POWER_LEVELS)
    power = models.FloatField(null=True, blank=True)
    fuel_consumption = models.FloatField(null=True, blank=True)
    ghg_hc_emissions = models.FloatField(null=True, blank=True)
    ghg_co_emissions = models.FloatField(null=True, blank=True)
    ghg_no_emissions = models.FloatField(null=True, blank=True)
    ghg_pm_emissions = models.FloatField(null=True, blank=True)
    ghg_co2_emissions = models.FloatField(null=True, blank=True)

class ElectricLocomotive(Car):
    efficiency_in = models.FloatField(null=True, blank=True)
    efficiency_out = models.FloatField(null=True, blank=True)
    max_power_in = models.FloatField(null=True, blank=True)
    max_power_out = models.FloatField(null=True, blank=True)
    max_usable_energy = models.FloatField(null=True, blank=True)
    acquisition_cost = models.FloatField(null=True, blank=True)
    power_in = models.JSONField(null=True)
    power_out = models.JSONField(null=True)

class Cell(models.Model):
    model = models.CharField(max_length=50, null=True, blank=True)
    manufacturer = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=50, null=True, blank=True)
    #nominal_voltage = models.FloatField(null=True, blank=True)
    max_voltage = models.FloatField(null=True, blank=True)
    min_operating_temperature = models.FloatField(null=True, blank=True)
    max_operating_temperature = models.FloatField(null=True, blank=True)
    cutoff_discharge_voltage = models.FloatField(null=True, blank=True)
    cutoff_charge_voltage = models.FloatField(null=True, blank=True)
    standard_current = models.FloatField(null=True, blank=True)
    internal_resistance = models.FloatField(null=True, blank=True)
    maximum_discharging_current = models.FloatField(null=True, blank=True)
    minimum_charging_current = models.FloatField(null=True, blank=True)
    capacity = models.FloatField(null=True, blank=True)
    size_x = models.FloatField(null=True, blank=True)
    size_y = models.FloatField(null=True, blank=True)
    size_z = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    ocv_curve = models.JSONField(null=True)

class BatteryModule(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)
    electric_locomotive = models.ForeignKey(ElectricLocomotive, null=True, on_delete=models.CASCADE)
    cell = models.ForeignKey(Cell, null=True, on_delete=models.CASCADE)
    number_series_cells = models.IntegerField(null=True, blank=True)
    number_parallel_cells = models.IntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    bus_voltage = models.FloatField(null=True, blank=True)
    max_voltage = models.FloatField(null=True, blank=True)

def initElectricLocomotive(**kwargs):
    instance = kwargs.get('instance')
    instance.type = 'E'

post_init.connect(initElectricLocomotive, ElectricLocomotive)

class FuelCellLocomotive(Car):
    fuel_type = models.CharField(max_length=50, null=True, blank=True)
    fuel_capacity = models.FloatField(null=True, blank=True)
    max_power = models.FloatField(null=True, blank=True)
    acquisition_cost = models.FloatField(null=True, blank=True)


def initFuelCellLocomotive(**kwargs):
    instance = kwargs.get('instance')
    instance.type = 'C'

post_init.connect(initFuelCellLocomotive, FuelCellLocomotive)

class PowerToWheels(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, null=True, blank=True)
    power_level = models.FloatField(null=True, blank=True)
    fuel_consumption = models.FloatField(null=True, blank=True)
    ghg_hc_emissions = models.FloatField(null=True, blank=True)
    ghg_co_emissions = models.FloatField(null=True, blank=True)
    ghg_no_emissions = models.FloatField(null=True, blank=True)
    ghg_pm_emissions = models.FloatField(null=True, blank=True)
    ghg_co2_emissions = models.FloatField(null=True, blank=True)

class Policy(models.Model):
    type = models.CharField(max_length=50, null=True, blank=True)
    power_order = ArrayField(models.CharField(max_length=50, blank=True), size=3, null=True)
    braking = models.CharField(max_length=50, null=True, blank=True)
    max_speed = models.FloatField(default=26.8224)   # in units of m/s - this is 60 MPH
    description = models.CharField(max_length=500, null=True, blank=True)

    def name(self):
        s = "automatic with " + self.braking
        if self.type == 'user_fixed':
            str = ""
            for p in self.power_order:
                if p is not None:
                    str += p + ", " 
            s = str[:-2]
            s += " with " + self.braking
        return s

# Results  schema - this can be remvoed soon
class ConsistRouteEvaluation(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    consist = models.ForeignKey(Consist, on_delete=models.CASCADE)
    power_order = models.CharField(max_length=100, null=True, blank=True)
    braking = models.CharField(max_length=50, null=True, blank=True)
    analysis_date = models.DateField(null=True, blank=True)
    distance_travelled = models.FloatField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)
    avg_speed = models.FloatField(null=True, blank=True)
    energy_cost = models.FloatField(null=True, blank=True)
    operating_cost = models.FloatField(null=True, blank=True)
    total_work = models.FloatField(null=True, blank=True)
    fuel_consumed = models.FloatField(null=True, blank=True)
    ghg_hc_emissions = models.FloatField(null=True, blank=True)
    ghg_co_emissions = models.FloatField(null=True, blank=True)
    ghg_no_emissions = models.FloatField(null=True, blank=True)
    ghg_pm_emissions = models.FloatField(null=True, blank=True)
    ltd_analysis = models.BooleanField(default=True)
    result_code = models.IntegerField(null=True, blank=True)

    group = models.ForeignKey(Group, default=None, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, default=None, null=True, on_delete=models.CASCADE)


class Session(models.Model):
    short_desc = models.CharField(max_length=300, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(Group, default=None, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, default=None, null=True, on_delete=models.CASCADE) 

class LTDResults(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    consist = models.ForeignKey(Consist, on_delete=models.CASCADE)
    policy = models.ForeignKey(Policy, default=None, on_delete=models.CASCADE)
    analysis_date = models.DateField(null=True, blank=True)
    rapid = models.BooleanField(default=True)
    status = models.IntegerField(default=0)
    result_code = models.IntegerField(default=-1)
    result = models.JSONField(null=True)
    session = models.ForeignKey(Session, default=None, null=True, on_delete=models.CASCADE)


# results per Segment
class PerformanceWithEmissions(models.Model):
    consist_route_evaluation = models.ForeignKey(ConsistRouteEvaluation, on_delete=models.CASCADE, null=True, blank=True)
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, null=True, blank=True)
    start_distance = models.FloatField(null=True, blank=True)
    start_time = models.FloatField(null=True, blank=True)
    interval_length =  models.FloatField(null=True, blank=True)
    interval_duration = models.FloatField(null=True, blank=True)
    ending_speed = models.FloatField(null=True, blank=True)
    power = models.FloatField(null=True, blank=True)
    energy_cost = models.FloatField(null=True, blank=True)
    operating_cost = models.FloatField(null=True, blank=True)
    fuel_consumed = models.FloatField(null=True, blank=True)
    ghg_hc_emissions =  models.FloatField(null=True, blank=True)
    ghg_co_emissions =  models.FloatField(null=True, blank=True)
    ghg_no_emissions =  models.FloatField(null=True, blank=True)
    ghg_pm_emissions =  models.FloatField(null=True, blank=True)

# user request
class UserRequest(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    company = models.CharField(max_length=50)
    created = models.BooleanField(default=False)
    ignored = models.BooleanField(default=False)

# data log object
class DataLog(models.Model):
    group = models.ForeignKey(Group, default=None, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, default=None, null=True, on_delete=models.CASCADE)
    route = models.ForeignKey(Route, null=True, on_delete=models.CASCADE)
    consist = models.ForeignKey(Consist, null=True, on_delete=models.CASCADE)
    site = models.CharField(max_length=50)
    description = models.CharField(max_length=50)
    meta_data = models.JSONField(null=True, blank=True)
    log_time = models.DateTimeField()

class Feedback(models.Model):
    user = models.ForeignKey(User, default=None, null=True, on_delete=models.CASCADE)
    description = models.CharField(max_length=4000)
    log_time = models.DateTimeField()
