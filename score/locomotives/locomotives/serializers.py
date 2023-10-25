# Copyright (c) 2022, The Pennsylvania State University
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.

from rest_framework import serializers
from .models import Route, RouteSchedule, Location, Locality, Segment, SpeedRestriction, Consist, ConsistCar, Car, FreightCar
from .models import DieselLocomotive, ElectricLocomotive, FuelCellLocomotive, PowerToWheels, ConsistRouteEvaluation, PerformanceWithEmissions
from .models import Line

class RouteSerializer(serializers.ModelSerializer):
    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = Route
        # fields = ['id', 'url', 'name']
        fields = '__all__'

class Route2Serializer(serializers.ModelSerializer):

    class Meta:
        model = Route
        fields = ['id', 'name']

class RouteScheduleSerializer(serializers.ModelSerializer):

    route = RouteSerializer(read_only=True)
    route_id = serializers.PrimaryKeyRelatedField(source='route', write_only=True, queryset=Route.objects.all())

    class Meta:
        model = RouteSchedule
        fields = ['id', 'route', 'route_id', 'name']

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'latitude', 'longitude', 'x', 'y', 'elev_m', 'smooth_elev_m']

class LocalitySerializer(serializers.ModelSerializer):

    route = RouteSerializer(read_only=True)
    route_id = serializers.PrimaryKeyRelatedField(source='route', write_only=True, queryset=Route.objects.all())

    class Meta:
        model = Locality
        fields = ['id', 'route', 'route_id', 'net', 'tracks', 'city_fips', 'state_fips', 'state_abbrev', 'time_zone', 'avg_winter_temp', 'avg_spring_temp', 'avg_summer_temp', 'avg_fall_temp', 'avg_winter_pressure', 'avg_spring_pressure', 'avg_summer_pressure', 'avg_fall_pressure']


class SegmentSerializer(serializers.ModelSerializer):

    route = RouteSerializer(read_only=True)
    route_id = serializers.PrimaryKeyRelatedField(source='route', write_only=True, queryset=Route.objects.all())

    locality = LocalitySerializer(read_only=True)
    locality_id = serializers.PrimaryKeyRelatedField(source='locality', write_only=True, queryset=Locality.objects.all(), allow_null=True)

    class Meta:
        model = Segment
        locations = LocationSerializer(read_only=True, many=True)
        fields = ['id', 'route', 'route_id', 'locality', 'locality_id', 'locations', 'gradient', 'arc_distance', 'radius_curvature', 'max_speed']


class SpeedRestrictionSerializer(serializers.ModelSerializer):

    route_schedule = RouteScheduleSerializer(read_only=True)
    route_schedule_id = serializers.PrimaryKeyRelatedField(source='route_schedule', write_only=True, queryset=RouteSchedule.objects.all())

    segment = SegmentSerializer(read_only=True)
    segment_id = serializers.PrimaryKeyRelatedField(source='segment', write_only=True, queryset=Segment.objects.all())

    class Meta:
        model = SpeedRestriction
        fields = ['id', 'route_schedule', 'route_schedule_id', 'segment', 'segment_id', 'max_speed', 'stop_duration']

class ConsistSerializer(serializers.ModelSerializer):

    class Meta:
        model = Consist
        fields = ['id', 'name', 'most_recent_version', 'parent_id']

class CarSerializer(serializers.ModelSerializer):

    class Meta:
        model = Car
        fields = ['id', 'name', 'aar_type', 'type', 'description', 'length', 'width', 'height', 'number_axles', 'air_braking_max_force', 'weight', 'most_recent_version', 'parent_id']


class ConsistCarSerializer(serializers.ModelSerializer):

    consist = ConsistSerializer(read_only=True)
    consist_id = serializers.PrimaryKeyRelatedField(source='consist', write_only=True, queryset=Consist.objects.all())

    car = CarSerializer(read_only=True)
    car_id = serializers.PrimaryKeyRelatedField(source='car', write_only=True, queryset=Car.objects.all())

    class Meta:
        model = ConsistCar
        fields = ['id', 'position', 'consist', 'consist_id', 'car', 'car_id']

class FreightCarSerializer(serializers.ModelSerializer):

    class Meta:
        model = FreightCar
        fields = ['id', 'name', 'aar_type', 'type', 'description', 'length', 'width', 'height', 'number_axles', 'air_braking_max_force', 'weight', 'most_recent_version', 'parent_id']

class DieselLocomotiveSerializer(serializers.ModelSerializer):

    class Meta:
        model = DieselLocomotive
        fields = ['id', 'fuel_capacity', 'acquisition_cost', 'max_power', 'most_recent_version', 'parent_id']

class ElectricLocomotiveSerializer(serializers.ModelSerializer):

    class Meta:
        model = ElectricLocomotive
        fields = ['id', 'efficiency_in', 'efficiency_out', 'max_power_in', 'max_power_out', 'max_usuable_energy', 'acquisition_cost', 'most_recent_version', 'parent_id']

class FuelCellLocomotiveSerializer(serializers.ModelSerializer):

    class Meta:
        model = FuelCellLocomotive
        fields = ['id', 'fuel_type', 'fuel_capacity', 'acquisition_cost', 'consist_car', 'consist_car_id', 'most_recent_version', 'parent_id']

class PowerToWheelsSerializer(serializers.ModelSerializer):

    diesel_locomotive = DieselLocomotiveSerializer(read_only=True)
    diesel_locomotive_id = serializers.PrimaryKeyRelatedField(source='diesel_locomotive', write_only=True, queryset=DieselLocomotive.objects.all())

    fuel_cell_locomotive = FuelCellLocomotiveSerializer(read_only=True)
    fuel_cell_locomotive_id = serializers.PrimaryKeyRelatedField(source='fuel_cell_locomotive', write_only=True, queryset=FuelCellLocomotive.objects.all())

    class Meta:
        model = PowerToWheels
        fields = ['id', 'power', 'fuel_consumption', 'ghg_hc_emissions', 'ghg_co_emissions', 'ghg_no_emissions', 'ghg_pm_emissions', 'diesel_locomotive', 'diesel_locomotive_id', 'fuel_cell_locomotive', 'fuel_cell_locomotive_id']



class ConsistRouteEvaluationSerializer(serializers.ModelSerializer):

    route = RouteSerializer(read_only=True)
    route_id = serializers.PrimaryKeyRelatedField(source='route', write_only=True, queryset=Route.objects.all())

    consist = ConsistSerializer(read_only=True)
    consist_id = serializers.PrimaryKeyRelatedField(source='consist', write_only=True, queryset=Consist.objects.all())

    class Meta:
        model = ConsistRouteEvaluation
        fields = ['id', 'analysis_date', 'distance_travelled' , 'duration', 'avg_speed', 'energy_cost', 'operating_cost', 'total_work', 'fuel_consumed', 'ghg_hc_emissions', 'ghg_co_emissions', 'ghg_no_emissions', 'ghg_pm_emissions', 'route', 'route_id', 'consist', 'consist_id']


class PerformanceWithEmissionsSerializer(serializers.ModelSerializer):

    consist_route_evaluation = ConsistRouteEvaluationSerializer(read_only=True)
    consist_route_evaluation_id = serializers.PrimaryKeyRelatedField(source='consist_route_evaluation', write_only=True, queryset=ConsistRouteEvaluation.objects.all(), allow_null=True)

    segment = SegmentSerializer(read_only=True)
    segment_id = serializers.PrimaryKeyRelatedField(source='segment', write_only=True, queryset=Segment.objects.all())
    class Meta:
        model = PerformanceWithEmissions
        fields = ['id', 'start_distance', 'start_time', 'interval_length', 'interval_duration', 'ending_speed', 'power', 'energy_cost', 'fuel_consumed', 'ghg_hc_emissions', 'ghg_co_emissions', 'ghg_no_emissions', 'ghg_pm_emissions', 'consist_route_evaluation', 'consist_route_evaluation_id', 'segment', 'segment_id']

class LineSerializer(serializers.ModelSerializer):

    class Meta:
        model = Line
        fields = '__all__'
