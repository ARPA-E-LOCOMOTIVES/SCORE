# Copyright (c) 2022, The Pennsylvania State University
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.


from django.contrib import admin
from functools import partial
from .models import CarType, FreightCar, DieselLocomotive, FuelCellLocomotive, ElectricLocomotive, PowerToWheels, ConsistCar, Consist, Route, UserRequest
from .models import Policy, Segment, Tier, LocomotiveModel, Emission, LAR, Fuel, Session, LTDResults

class PowerInline(admin.TabularInline):
    model = PowerToWheels

# Register your models here.
class DieselLocomotiveAdmin(admin.ModelAdmin):
    list_display = ('name','description', 'aar_type')
    fields = ('name', 'description', 'aar_type', 'length', 'width', 'height', 'weight', 'number_axles', 'max_power','fuel_capacity', 'acquisition_cost', 'parent_id', 'most_recent_version', 'user', 'group')

    inlines = [
        PowerInline,
    ]

    def get_changeform_initial_data(self, request):
        return {
            'number_axles': 6,
            'length': 22,
            'width': 3.12,
            'height': 4.72,
            'weight': 190.51,
        }

admin.site.register(DieselLocomotive, DieselLocomotiveAdmin)

class FuelCellLocomotiveAdmin(admin.ModelAdmin):
    list_display = ('name','description', 'aar_type')
    fields = ('name', 'description', 'aar_type', 'length', 'width', 'height', 'weight', 'number_axles', 'max_power','fuel_type', 'fuel_capacity', 'acquisition_cost', 'parent_id', 'most_recent_version', 'user', 'group')

    inlines = [
        PowerInline,
    ]

    def get_changeform_initial_data(self, request):
        return {
            'number_axles': 6,
            'length': 22,
            'width': 3.12,
            'height': 4.72,
            'weight': 190.51,
        }

admin.site.register(FuelCellLocomotive, FuelCellLocomotiveAdmin)

class ElectricLocomotiveAdmin(admin.ModelAdmin):
    list_display = ('name', 'acquisition_cost', 'max_power_out')
    fields = ('name', 'description', 'aar_type', 'length', 'width', 'height', 'weight', 'number_axles', 'efficiency_in', 'efficiency_out', 'max_power_in', 'max_power_out', 'max_usable_energy', 'acquisition_cost', 'parent_id', 'most_recent_version', 'user', 'group')

admin.site.register(ElectricLocomotive, ElectricLocomotiveAdmin)

class FreightCarAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'aar_type')
    fields = ('name', 'description', 'aar_type', 'length', 'width', 'height', 'weight', 'empty_weight', 'number_axles', 'user', 'group')

    def get_changeform_initial_data(self, request):
        return {
            'number_axles': 4,
            'length': 20,
            'width': 3,
            'height': 4,
            'weight': 85,
            'empty_weight': 35
        }

admin.site.register(FreightCar, FreightCarAdmin)

class CarTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'description', 'type' )

admin.site.register(CarType, CarTypeAdmin)

class ConsistCarInline(admin.TabularInline):
    model = ConsistCar

    fields = ('position', 'car')


class ConsistAdmin(admin.ModelAdmin):
    list_display = ('name',)
    field = ('name', 'acquisition_cost', 'parent_id', 'most_recent_version', 'user', 'group')

    inlines = [
        ConsistCarInline,
    ]

admin.site.register(Consist, ConsistAdmin)

class RouteAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(Route, RouteAdmin)

class PolicyAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(Policy, PolicyAdmin)

class SegmentAdmin(admin.ModelAdmin):
    list_display = ('route', 'segment_order',)

admin.site.register(Segment, SegmentAdmin)

class UserRequestAdmin(admin.ModelAdmin):
    list_display = ('first_name','last_name','email','phone','company','created', 'ignored')

admin.site.register(UserRequest, UserRequestAdmin)


class TierAdmin(admin.ModelAdmin):
    list_display = ('tier',)

admin.site.register(Tier, TierAdmin)

class LocomotiveModelAdmin(admin.ModelAdmin):
    list_display = ('model', 'manufacturer',)

admin.site.register(LocomotiveModel, LocomotiveModelAdmin)

class EmissionInline(admin.TabularInline):
    model = Emission

class LARAdmin(admin.ModelAdmin):
    list_display = ('unit_name', 'model', 'tier', )

    inlines = [
        EmissionInline,
    ]

admin.site.register(LAR, LARAdmin)

class FuelAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(Fuel, FuelAdmin)

class SessionAdmin(admin.ModelAdmin):
    list_display = ('short_desc', 'date',)

admin.site.register(Session, SessionAdmin)

class LTDResultsAdmin(admin.ModelAdmin):
    list_display = ('session', 'analysis_date',)

admin.site.register(LTDResults, LTDResultsAdmin)