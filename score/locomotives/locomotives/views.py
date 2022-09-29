# Copyright (c) 2022, The Pennsylvania State University
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from .serializers import RouteSerializer, RouteScheduleSerializer, LocationSerializer, SegmentSerializer, LocalitySerializer, SpeedRestrictionSerializer, ConsistSerializer, ConsistCarSerializer, FreightCarSerializer,  DieselLocomotiveSerializer, ElectricLocomotiveSerializer, FuelCellLocomotiveSerializer, PowerToWheelsSerializer, ConsistRouteEvaluationSerializer, PerformanceWithEmissionsSerializer
from .models import Route, RouteSchedule, Location, Segment, Locality, SpeedRestriction, Consist, ConsistCar, Car, CarType, FreightCar, DieselLocomotive, PowerToWheels, ElectricLocomotive, FuelCellLocomotive, ConsistRouteEvaluation, PerformanceWithEmissions, Cell, BatteryModule, Policy, UserRequest, DataLog, Feedback
from .models import ConsistCar, PowerToWheels, LTDResults, Session
from datetime import datetime, timedelta
import json

from django.contrib.auth.decorators import login_required
import numpy as np
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import redirect
from scipy.interpolate import interp2d

from django.core.mail import send_mail
from pytz import timezone

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.core.paginator import Paginator
from django.contrib.auth.models import User, Group


# from scipy.interpolate import interp1d

from itertools import permutations
from locomotives.consist_data import get_consist_data

import csv

# Create your views here.
@login_required
def home(request):

    admin_user_account_badge = 0

    if request.user.is_superuser:
        user_requests = UserRequest.objects.all()
        for user_request in user_requests:
            if not user_request.created and not user_request.ignored:
                admin_user_account_badge += 1

    context = default_context(request)
    context['admin_user_account_badge'] = admin_user_account_badge

    log_action(request, 'home.html')
    return render(request, 'home.html', context)


def default_context(request):
    context = {
        'title': 'GET Page Template View',
        'path': request.path,
        'received_headers': request.headers.items(),
        'client_cookies': request.COOKIES,
    }
    return context

@login_required
def restricted(request):
    log_action(request, 'restricted.html')
    context = default_context(request)
    context['error_message'] = ''
    return render(request, 'restricted.html', context)

def signup(request):
    log_action(request, 'signup.html')
    return render(request, 'signup.html', default_context(request))

def about(request):
    log_action(request, 'about.html')
    return render(request, 'about.html', default_context(request))

def contact(request):
    log_action(request, 'contact.html')
    return render(request, 'contact.html', default_context(request))

def feedback(request):
    all_feedback = Feedback.objects.all()
    context = default_context(request)
    context['feedback'] = all_feedback
    log_action(request, 'feedback.html')
    return render(request, 'feedback.html', context)

def providefeedback(request):
    log_action(request, 'provide-feedback.html')
    return render(request, 'provide-feedback.html', default_context(request))

def powerpoliciesdoc(request):
    log_action(request, 'powerpoliciesdoc.html')
    return render(request, 'powerpoliciesdoc.html', default_context(request))

@api_view(['POST'])
@login_required
def submit_feedback(request):
    feedback = Feedback()
    feedback.user = request.user
    feedback.description = request.data['feedback']
    feedback.log_time = datetime.now(timezone('EST')) - timedelta(hours=5, minutes=0)
    feedback.save()

    email_msg = "User : " + request.user.username + ", Feedback : " + request.data['feedback']
    from_account = 'garymstump@gmail.com'
    to_account = ['gms158@arl.psu.edu', 'jdm111@arl.psu.edu', 'lab27@arl.psu.edu']
    send_mail(
        'SCORE Feedback',
        email_msg,
        from_account,
        to_account,
        fail_silently=False,
    )

    return render(request, 'received-feedback.html', default_context(request))


@login_required
def user_requests(request):

    if not request.user.is_superuser:
        log_action(request, 'user-requests.html', 'Restricted Access')
        return redirect(restricted)

    user_requests = UserRequest.objects.all()
    context = default_context(request)
    context['user_requests'] = user_requests

    log_action(request, 'user-requests.html')
    return render(request, 'user-requests.html', context)


@login_required
def adduserrequest(request, pk):

    if not request.user.is_superuser:
        log_action(request, 'add-user-request.html', 'Restricted Access')
        return redirect(restricted)

    user_request = UserRequest.objects.filter(id=pk).first()
    groups = Group.objects.all()

    context = default_context(request)
    context['user_request'] = user_request
    context['groups'] = groups

    return render(request, 'add-user-request.html', context)


@login_required
@api_view(['POST'])
def adduser(request):
    username = request.data['username']
    email = request.data['email']
    first_name = request.data['first_name']
    last_name = request.data['last_name']
    password0 = request.data['password0']
    password1 = request.data['password1']
    user_request_id = int(request.data['user_request_id'])

    groups = []
    for key in request.data:
        if 'checkbox_' in key:
            group = Group.objects.filter(id=int(key.split("_")[1])).first()
            groups.append(group)

    if 'newgroup' in request.data:
        group, created = Group.objects.get_or_create(name=request.data['group_name'])
        groups.append(group)

    if password0 == password1:
        user = User();
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.set_password(password0)
        user.save()

        for group in groups:
            user.groups.add(group.id)
        user.save()

        user_request = UserRequest.objects.filter(id=user_request_id).first()
        user_request.created = True
        user_request.save()

        return redirect(user_requests)

    else:
        print("----------- passwords do not match -----------")
        return redirect(restricted)


@login_required
def ignoreuser(request, pk):
    user_request = UserRequest.objects.filter(id=pk).first()
    user_request.ignored = True
    user_request.save()
    return redirect(user_requests)


@api_view(['POST'])
@permission_classes([])
def submit_signup(request):

    user_request = UserRequest()
    # if password reset, tested by email tag for now, may want to change this
    user_requests = UserRequest.objects.filter(email=request.data['email'])
    if len(user_requests) > 0:
        user_request = user_requests.first()
    user_request.first_name = request.data['first_name']
    user_request.last_name = request.data['last_name']
    user_request.email = request.data['email']
    user_request.phone = request.data['phone']
    user_request.company = request.data['company']
    user_request.created = False
    user_request.ignored = False
    user_request.save()

    email_msg = "First Name : " + user_request.first_name + " , Last Name : " + user_request.last_name + " , Email : " + user_request.email + " , Phone : " + user_request.phone + " , company : " + user_request.company
    from_account = 'garymstump@gmail.com'
    to_account = ['gms158@arl.psu.edu', 'jdm111@arl.psu.edu', 'lab27@arl.psu.edu']
    send_mail(
        'SCORE Account Request',
        email_msg,
        from_account,
        to_account,
        fail_silently=False,
    )

    context = {
        'title': 'GET Page Template View',
        'path': request.path,
        'received_headers': request.headers.items(),
        'client_cookies': request.COOKIES,
    }

    log_action(request, 'signup_complete.html', email_msg[:50])
    return render(request, 'signup_complete.html', context)

@login_required
def datalogs(request):

    if not request.user.is_superuser:
        log_action(request, 'datalogs.html', 'Restricted Access')
        return redirect(restricted)

    page_num = 1
    request_page_num = request.GET.get('page')
    if request_page_num:
        page_num = request_page_num

    datalogs = DataLog.objects.all().order_by('-log_time')
    datalogs_paginator = Paginator(datalogs, 100)
    datalogs_page = datalogs_paginator.get_page(page_num)

    context = default_context(request)
    context['datalogs'] = datalogs
    context['datalogs_page'] = datalogs_page
    context['datalogs_page_count'] = datalogs_paginator.count

    return render(request, 'datalogs.html', context)

def get_visible(user, objs):
    all_visible = []
    for obj in objs:
        if is_object_visible(user, obj):
            all_visible.append(obj)
    return all_visible

def is_object_visible(user, obj):
    if obj.group is None:
        return False;
    else:
        return user.groups.filter(name=obj.group.name).exists()

# assume each user has one group
def get_user_group_for_save(user):
    return user.groups.exclude(name='public').first()

@login_required
def routelist(request):

    route_info = {}
    cached_info = {}
    routes = get_visible(request.user,Route.objects.all())
    for route in routes:
        route_info[route.id] = route.name
        if route.cached_route_line is not None:
            cached_info[route.id] = route.cached_route_line

    # show all routes not cached as points
    location_data = []

    context = default_context(request)
    context['route_info'] = route_info
    context['locations'] = json.dumps(location_data)
    context['cached_route_lines'] = json.dumps(cached_info)

    log_action(request, 'route-list.html')
    return render(request, 'route-list.html', context)

# Create your views here.
@login_required
def routeinfo(request, id):

    #RESOLUTION_M = 804.672   # every half mi
    RESOLUTION_M = 100

    lines = []
    meta_data = {}
    route = Route.objects.filter(id=id).first()
    if route is not None:
        if is_object_visible(request.user, route):
            route_dist_seg = 0
            route_dist = 0

            line_json = None
            if route.cached_route_line is None:
                line_json = []

            segs = Segment.objects.filter(route=route).order_by('segment_order').all();
            if len(segs) > 0:
                current_position = [segs[0].locations.all()[0].longitude, segs[0].locations.all()[0].latitude]
                for i, seg in enumerate(segs):
                    route_dist_seg += seg.arc_distance
                    route_dist += seg.arc_distance
                    degrees_curve_100 = 0
                    if seg.turn_type != 0:
                        #degrees_curve_100 = (100/(seg.arc_distance*3.28084))*(180/math.pi)*2*(math.asin(50/(3.28084*seg.radius_curvature)))
                        degrees_curve_100 = 5728.6/(seg.radius_curvature*3.28084)

                    if route_dist_seg > RESOLUTION_M:
                        end_loc = seg.locations.all()[1]
                        lines.append([current_position[0], current_position[1], end_loc.longitude, end_loc.latitude, route_dist, end_loc.smooth_elev_m, seg.gradient, seg.radius_curvature, end_loc.elev_m, degrees_curve_100, seg.max_speed])
                        if line_json is not None:
                            line_json.append({"type": "LineString", "coordinates": [[current_position[0], current_position[1]], [end_loc.longitude, end_loc.latitude]]});
                        current_position = [end_loc.longitude, end_loc.latitude]
                        route_dist_seg = 0

            if line_json is not None:
                route.cached_route_line = line_json
                route.save()

            context = default_context(request)
            context['data'] = json.dumps(lines)
            context['route'] = route
            context['meta_data'] = json.dumps(meta_data)

            log_action(request, 'route-info.html', "", "", route, None)
            return render(request, 'route-info.html', context)
        else:
            log_action(request, 'route-info.html', "Restricted Access", "", route, None)
            return redirect(restricted)


def get_consist_info(pk):

    consist_info = {}
    consist_common_info = []
    consist = Consist.objects.filter(id=pk).first()
    consist_cars = ConsistCar.objects.filter(consist_id=consist.id)
    consist_info["name"] = consist.name
    consist_info["number_cars"] = len(consist_cars)
    total_mass = 0
    total_freight_mass = 0
    total_length = 0
    total_power = 0

    for i, car in enumerate(consist_cars):
        total_mass += car.car.weight
        total_length += car.car.length
        meta_data = ""
        loaded = ""
        if car.car.type == 'D':
            total_power += car.car.diesellocomotive.max_power
            meta_data = "Max Power (hp) = " + str(int(1.34102*car.car.diesellocomotive.max_power))
        if car.car.type == 'E':
            total_power += car.car.electriclocomotive.max_power_out
            meta_data = "Max Power (hp) = " + str(int(1.34102*car.car.electriclocomotive.max_power_out))
        if car.car.type == 'C':
            total_power += car.car.fuelcelllocomotive.max_power
            meta_data = "Max Power (hp) = " + str(int(1.34102*car.car.fuelcelllocomotive.max_power))
        if car.car.type == 'F':
            if car.loaded:
                total_freight_mass += car.car.weight
            else:
                total_freight_mass += car.car.freightcar.empty_weight
            if car.loaded:
                loaded = "Full"
            else:
                loaded = "Empty"
        consist_common_info.append([str(i+1),
            car.car.aar_type,
            car.car.name,
            car.car.description,
            str(round(3.28*car.car.length,2)),
            str(round(3.28*car.car.height,2)),
            str(car.car.number_axles),
            str(round(1.10231*car.car.weight,2)),
            loaded,
            meta_data])

    consist_info["power_hp"] = str(int(1.34102*total_power))
    consist_info["weight_tons"] = str(int(1.10231*total_mass))
    consist_info["trailing_tons"] = str(int(1.10231*total_freight_mass))
    consist_info["power_to_weight"] = 0
    if total_mass > 0: # in case a user enters a bad consist
        consist_info["power_to_weight"] = str(round(1.34102*total_power/(1.10231*total_freight_mass),2))
    consist_info["length_mi"] = str(round(0.621371*total_length/1000,2))

    consist_locomotive_types = get_locomotive_type(consist)
    return consist, consist_info, consist_common_info, consist_locomotive_types

@login_required
def consistlist(request):

    consist_info_list = []
    consists = get_visible(request.user,Consist.objects.filter(most_recent_version=True))
    for consist in consists:
        consist, consist_info, consist_common_info, consist_locomotive_types = get_consist_info(consist.id)
        consist_info_list.append([consist_info, consist.id])

    diesel_locomotives = get_visible(request.user,DieselLocomotive.objects.filter(most_recent_version=True))
    diesel_info_list = []
    for diesel_locomotive in diesel_locomotives:
        diesel_locomotive_info = {}
        diesel_locomotive_info['name'] = diesel_locomotive.name
        diesel_locomotive_info['description'] = diesel_locomotive.description
        diesel_locomotive_info['max_power'] = 0
        power_levels_filter = PowerToWheels.objects.filter(car=diesel_locomotive).order_by('-power_level')
        if len(power_levels_filter) > 0:
            diesel_locomotive_info['max_power'] = round(1.34102*power_levels_filter.first().power_level,1) # convert to hp
        diesel_locomotive_info['length'] = round(3.28084*diesel_locomotive.length,1) # convert to feet
        diesel_locomotive_info['width'] = round(3.28084*diesel_locomotive.width,1)   # convert to feet
        diesel_locomotive_info['height'] = round(3.28084*diesel_locomotive.height,1) # convert to feet
        diesel_info_list.append([diesel_locomotive_info, diesel_locomotive.id])

    electric_locomotives = get_visible(request.user, ElectricLocomotive.objects.filter(most_recent_version=True))
    electric_info_list = []
    for electric_locomotive in electric_locomotives:
        electric_locomotive_info = {}
        electric_locomotive_info['name'] = electric_locomotive.name
        electric_locomotive_info['description'] = electric_locomotive.description
        electric_locomotive_info['max_power'] = round(1.34102*electric_locomotive.max_power_out,1)
        electric_locomotive_info['length'] = round(3.28084*electric_locomotive.length,1) # convert to feet
        electric_locomotive_info['width'] = round(3.28084*electric_locomotive.width,1)   # convert to feet
        electric_locomotive_info['height'] = round(3.28084*electric_locomotive.height,1) # convert to feet
        electric_info_list.append([electric_locomotive_info, electric_locomotive.id])

    fuel_cell_locomotives = get_visible(request.user, FuelCellLocomotive.objects.filter(most_recent_version=True))
    fuel_cell_info_list = []
    for fuel_cell_locomotive in fuel_cell_locomotives:
        fuel_cell_locomotive_info = {}
        fuel_cell_locomotive_info['name'] = fuel_cell_locomotive.name
        fuel_cell_locomotive_info['description'] = fuel_cell_locomotive.description
        fuel_cell_locomotive_info['max_power'] = round(1.34102*fuel_cell_locomotive.max_power,1)
        fuel_cell_locomotive_info['length'] = round(3.28084*fuel_cell_locomotive.length,1) # convert to feet
        fuel_cell_locomotive_info['width'] = round(3.28084*fuel_cell_locomotive.width,1)   # convert to feet
        fuel_cell_locomotive_info['height'] = round(3.28084*fuel_cell_locomotive.height,1) # convert to feet
        fuel_cell_info_list.append([fuel_cell_locomotive_info, fuel_cell_locomotive.id])

    context = default_context(request)
    context['consist_info_list'] = consist_info_list
    context['diesel_locomotive_info_list'] = diesel_info_list
    context['electric_locomotive_info_list'] = electric_info_list
    context['fuel_cell_locomotive_info_list'] = fuel_cell_info_list

    log_action(request, 'consist-list.html')
    return render(request, 'consist-list.html', context)

def consistinfo(request, pk):

    consist, consist_info, consist_common_info, consist_locomotive_types = get_consist_info(pk)
    if is_object_visible(request.user, consist):
        context = {
            'title': 'GET Page Template View',
            'path': request.path,
            'received_headers': request.headers.items(),
            'client_cookies': request.COOKIES,
            'consist_info' : consist_info,
            'consist_common_info' : consist_common_info
        }
        log_action(request, 'consist-info.html', "", "", None, consist)
        return render(request, 'consist-info.html', context)
    else:
        log_action(request, 'consist-info.html', "Restricted Access", "", None, consist)
        return redirect(restricted)

@login_required
def createconsist(request):
    log_action(request, 'create-consist.html')
    return redirect(editconsist, pk=0)

@login_required
def editconsist(request, pk):

    car_types = get_visible(request.user, Car.objects.filter(most_recent_version=True).order_by('name'))
    all_car_types = []
    all_loaded_ids = []
    all_freigt_ids = []
    for car_type in car_types:
        all_car_types.append({"value" : car_type.id, "label" : car_type.name})
        all_loaded_ids.append(car_type.id)
        if car_type.type == 'F':
            all_freigt_ids.append(car_type.id)

    edit_data = {}
    edit_data['pk'] = -1;
    edit_data['name'] = "";
    edit_data['types'] = [];

    if pk != 0:
        consist = Consist.objects.filter(id=pk).first()
        if is_object_visible(request.user, consist):
            consist_cars = ConsistCar.objects.filter(consist_id=consist.id).order_by('position')
            types = []
            last_key = -1
            last_loaded = None
            for consist_car in consist_cars:
                current_key = consist_car.car.id
                current_loaded = consist_car.loaded
                if (current_key != last_key) or (last_loaded is None or last_loaded != current_loaded):
                    types.append([0,consist_car.car.id,current_loaded])
                types[len(types) - 1][0] += 1
                last_key = current_key
                last_loaded = current_loaded

                if consist_car.car.id not in all_loaded_ids:
                    all_loaded_ids.append(consist_car.car.id)
                    all_car_types.append({"value" : consist_car.car.id, "label" : consist_car.car.name + "_prev_v" + str(consist_car.car.id)})

            edit_data['pk'] = pk;
            edit_data['name'] = consist.name;
            edit_data['types'] = types;
            log_action(request, 'edit-consist.html', "", "", None, consist)
        else:
            log_action(request, 'edit-consist.html', "Restricted Access", "", None, consist)
            return redirect(restricted)

    context = default_context(request)
    context['car_types'] = json.dumps(all_car_types)
    context['freight_ids'] = json.dumps(all_freigt_ids)
    context['edit_mode_data'] = json.dumps(edit_data)

    return render(request, 'create-consist.html', context)

@login_required
@api_view(['POST'])
def submitconsist(request):

    consist_name = request.data['consist_name']
    consist_data = request.data['data']
    edit_mode_id = request.data['edit_mode_id']
    clone = request.data['clone']

    # if clone, remove edit history by setting edit_mode_id to -1 or removing the previous consist key
    if clone:
        edit_mode_id = -1

    group_save = get_user_group_for_save(request.user)

    consist = Consist()
    if edit_mode_id != -1:
        previous_consist = Consist.objects.filter(id=edit_mode_id).first()
        if group_save.id == previous_consist.group.id:
            previous_consist.most_recent_version = False
        else:
            consist_name += ":" + group_save.name + "(group)"
        previous_consist.save()
        consist.parent_id = previous_consist.id
    consist.most_recent_version = True

    consist.name = consist_name
    consist.user = request.user
    consist.group = group_save
    consist.save()

    pos = 0
    for car_data in consist_data:
        for i in range(int(car_data[0])):
            pos += 1
            consist_car = ConsistCar()
            consist_car.consist = consist
            consist_car.position = pos
            car = Car.objects.filter(id=car_data[1]).first()
            consist_car.car = car
            consist_car.loaded = car_data[2]
            consist_car.save()

    log_action(request, 'submit_consist', "", "", None, consist)
    return redirect(consistlist)


@login_required
def editdiesellocomotive(request, pk):

    car_types = get_visible(request.user, Car.objects.all())
    all_car_types = []
    for car_type in car_types:
        all_car_types.append({"value" : car_type.id, "label" : car_type.name})

    edit_data = {}
    edit_data['pk'] = 0
    edit_data['name'] = "Enter name"
    edit_data['description'] = ""
    edit_data['length'] = 0
    edit_data['width'] = 0
    edit_data['height'] = 0
    edit_data['number_axles'] = 0
    edit_data['braking_force'] = 0
    edit_data['fuel_capacity'] = 0
    edit_data['weight'] = 0
    edit_data['cost'] = 0
    edit_data['max_power'] = 0
    edit_data['power_to_wheels'] = []

    if pk != 0:
        diesel_locomotive = DieselLocomotive.objects.filter(id=pk).first()
        if is_object_visible(request.user, diesel_locomotive):
            edit_data['pk'] = diesel_locomotive.id
            edit_data['name'] = diesel_locomotive.name
            edit_data['description'] = diesel_locomotive.description
            edit_data['length'] = diesel_locomotive.length
            edit_data['width'] = diesel_locomotive.width
            edit_data['height'] = diesel_locomotive.height
            edit_data['number_axles'] = diesel_locomotive.number_axles
            edit_data['braking_force'] = diesel_locomotive.air_braking_max_force
            edit_data['fuel_capacity'] = diesel_locomotive.fuel_capacity
            edit_data['weight'] = diesel_locomotive.weight
            edit_data['cost'] = diesel_locomotive.acquisition_cost
            edit_data['max_power'] = diesel_locomotive.max_power
            edit_data['power_to_wheels'] = []
            diesel_locomotive_ptw = PowerToWheels.objects.filter(car=diesel_locomotive)
            for ptw in diesel_locomotive_ptw:
                edit_data['power_to_wheels'].append([ptw.power_level, ptw.fuel_consumption, ptw.ghg_hc_emissions, ptw.ghg_co_emissions, ptw.ghg_no_emissions, ptw.ghg_pm_emissions])
            log_action(request, 'edit-diesel-locomotive.html', str(diesel_locomotive.id) + ":" + diesel_locomotive.name)
        else:
            log_action(request, 'edit-diesel-locomotive.html', "Restricted Access", str(diesel_locomotive.id) + ":" + diesel_locomotive.name, None, consist)
            return redirect(restricted)

    context = default_context(request)
    context['edit_mode_data'] = json.dumps(edit_data)

    return render(request, 'create-diesel-locomotive.html', context)

@login_required
def creatediesellocomotive(request):
    log_action(request, 'create-diesel-locomotive.html')
    return redirect(editdiesellocomotive, pk=0)

@login_required
def showdiesellocomotive(request, pk):

    car_types = get_visible(request.user, Car.objects.all())
    all_car_types = []
    for car_type in car_types:
        all_car_types.append({"value" : car_type.id, "label" : car_type.name})

    edit_data = {}
    edit_data['pk'] = 0
    edit_data['name'] = "Enter name"
    edit_data['description'] = ""
    edit_data['length'] = 0
    edit_data['width'] = 0
    edit_data['height'] = 0
    edit_data['number_axles'] = 0
    edit_data['braking_force'] = 0
    edit_data['fuel_capacity'] = 0
    edit_data['weight'] = 0
    edit_data['cost'] = 0
    edit_data['max_power'] = 0
    edit_data['power_to_wheels'] = []

    if pk != 0:
        diesel_locomotive = DieselLocomotive.objects.filter(id=pk).first()
        if is_object_visible(request.user, diesel_locomotive):
            edit_data['pk'] = diesel_locomotive.id
            edit_data['name'] = diesel_locomotive.name
            edit_data['description'] = diesel_locomotive.description
            edit_data['length'] = diesel_locomotive.length
            edit_data['width'] = diesel_locomotive.width
            edit_data['height'] = diesel_locomotive.height
            edit_data['number_axles'] = diesel_locomotive.number_axles
            edit_data['braking_force'] = diesel_locomotive.air_braking_max_force
            edit_data['fuel_capacity'] = diesel_locomotive.fuel_capacity
            edit_data['weight'] = diesel_locomotive.weight
            edit_data['cost'] = diesel_locomotive.acquisition_cost
            edit_data['max_power'] = diesel_locomotive.max_power
            edit_data['power_to_wheels'] = []
            diesel_locomotive_ptw = PowerToWheels.objects.filter(car=diesel_locomotive)
            for ptw in diesel_locomotive_ptw:
                edit_data['power_to_wheels'].append([ptw.power_level, ptw.fuel_consumption, ptw.ghg_hc_emissions, ptw.ghg_co_emissions, ptw.ghg_no_emissions, ptw.ghg_pm_emissions])
            log_action(request, 'show-diesel-locomotive.html', str(diesel_locomotive.id) + ":" + diesel_locomotive.name)
        else:
            log_action(request, 'show-diesel-locomotive.html', "Restricted Access", str(diesel_locomotive.id) + ":" + diesel_locomotive.name, None, consist)
            return redirect(restricted)

    print(edit_data)
    context = default_context(request)
    context['edit_mode_data'] = json.dumps(edit_data)

    return render(request, 'show-diesel-locomotive.html', context)

@login_required
@api_view(['POST'])
def submitdiesellocomotive(request):

    # get the car type
    car_types = CarType.objects.all()
    diesel_locomotive_car_type = None
    for car_type in car_types:
        if car_type.description == "Locomotive":
            diesel_locomotive_car_type = car_type

    # get edit mode value
    edit_mode_id = request.data['edit_mode_id']

    # get the save group
    group_save = get_user_group_for_save(request.user)

    locomotive_name = request.data['locomotive_name']

    # diesel locomotive
    diesel_locomotive = DieselLocomotive()
    if edit_mode_id != 0:
        previous_diesel_locomotive = DieselLocomotive.objects.filter(id=edit_mode_id).first()
        if group_save.id == previous_diesel_locomotive.group.id:
            previous_diesel_locomotive.most_recent_version = False
        else:
            locomotive_name += ":" + group_save.name + "(group)"
        previous_diesel_locomotive.save()
        diesel_locomotive.parent_id = previous_diesel_locomotive.id
    diesel_locomotive.most_recent_version = True

    # set empty value to '0' to avoid errors
    for key in request.data:
        if request.data[key] == '':
            request.data[key] = '0'

    # create the diesel locomotive
    diesel_locomotive.name = locomotive_name
    diesel_locomotive.aar_type = diesel_locomotive_car_type
    diesel_locomotive.type = 'D'
    diesel_locomotive.description = request.data['locomotive_description']
    diesel_locomotive.length = request.data['locomotive_length']
    diesel_locomotive.width = request.data['locomotive_width']
    diesel_locomotive.height = request.data['locomotive_height']
    diesel_locomotive.number_axles = request.data['locomotive_number_axles']
    diesel_locomotive.air_braking_max_force = request.data['locomotive_braking_force']
    diesel_locomotive.weight = request.data['locomotive_weight']
    diesel_locomotive.acquisition_cost = request.data['locomotive_cost']
    diesel_locomotive.fuel_capacity = request.data['locomotive_fuel_capacity']
    diesel_locomotive.max_power = request.data['locomotive_max_power']
    diesel_locomotive.user = request.user
    diesel_locomotive.group = group_save
    diesel_locomotive.save()

    # add power to wheels table
    for power_data in request.data['data']:
        ptw = PowerToWheels()
        ptw.car = diesel_locomotive
        ptw.power_level = power_data[0]
        ptw.fuel_consumption = power_data[1]
        ptw.ghg_hc_emissions = power_data[2]
        ptw.ghg_co_emissions = power_data[3]
        ptw.ghg_no_emissions = power_data[4]
        ptw.ghg_pm_emissions = power_data[5]
        ptw.ghg_co2_emissions = power_data[6]
        ptw.save()

    log_action(request, 'submit-diesel-locomotive', str(diesel_locomotive.id) + ":" + diesel_locomotive.name)
    return redirect(consistlist)


@login_required
def createelectriclocomotive(request):
    log_action(request, 'create-electric-locomotive.html')
    return redirect(editelectriclocomotive, pk=0)

@login_required
def editelectriclocomotive(request, pk):

    edit_data = {}
    edit_data['pk'] = 0
    edit_data['name'] = "Enter name"
    edit_data['description'] = ""
    edit_data['length'] = 0
    edit_data['width'] = 0
    edit_data['height'] = 0
    edit_data['number_axles'] = 0
    edit_data['braking_force'] = 0
    edit_data['fuel_capacity'] = 0
    edit_data['weight'] = 0
    edit_data['cost'] = 0
    edit_data['efficiency_in'] = 0
    edit_data['efficiency_out'] = 0
    edit_data['max_power_in'] = 0
    edit_data['max_power_out'] = 0
    edit_data['max_usable_energy'] = 0
    edit_data['power_in'] = {}
    edit_data['power_out'] = {}
    if pk != 0:
        electric_locomotive = ElectricLocomotive.objects.filter(id=pk).first()
        if is_object_visible(request.user, electric_locomotive):
            edit_data['pk'] = electric_locomotive.id
            edit_data['name'] = electric_locomotive.name
            edit_data['description'] = electric_locomotive.description
            edit_data['length'] = electric_locomotive.length
            edit_data['width'] = electric_locomotive.width
            edit_data['height'] = electric_locomotive.height
            edit_data['number_axles'] = electric_locomotive.number_axles
            edit_data['braking_force'] = electric_locomotive.air_braking_max_force
            edit_data['weight'] = electric_locomotive.weight
            edit_data['cost'] = electric_locomotive.acquisition_cost
            edit_data['efficiency_in'] = electric_locomotive.efficiency_in
            edit_data['efficiency_out'] = electric_locomotive.efficiency_out
            edit_data['max_power_in'] = electric_locomotive.max_power_in
            edit_data['max_power_out'] = electric_locomotive.max_power_out
            edit_data['max_usable_energy'] = electric_locomotive.max_usable_energy
            edit_data['power_in'] = electric_locomotive.power_in
            edit_data['power_out'] = electric_locomotive.power_out
            log_action(request, 'edit-electric-locomotive.html', str(electric_locomotive.id) + ":" + electric_locomotive.name)
        else:
            log_action(request, 'edit-electric-locomotive.html', 'Restricted Access', str(electric_locomotive.id) + ":" + electric_locomotive.name)
            return redirect(restricted)

    # no csv files loaded yet
    if edit_data['power_in'] is None:
        edit_data['power_in'] = {}
    if edit_data['power_out'] is None:
        edit_data['power_out'] = {}

    context = default_context(request)
    context['edit_mode_data'] = json.dumps(edit_data)

    return render(request, 'create-electric-locomotive.html', context)


@login_required
def showelectriclocomotive(request, pk):

    edit_data = {}
    edit_data['pk'] = 0
    edit_data['name'] = "Enter name"
    edit_data['description'] = ""
    edit_data['length'] = 0
    edit_data['width'] = 0
    edit_data['height'] = 0
    edit_data['number_axles'] = 0
    edit_data['braking_force'] = 0
    edit_data['fuel_capacity'] = 0
    edit_data['weight'] = 0
    edit_data['cost'] = 0
    edit_data['efficiency_in'] = 0
    edit_data['efficiency_out'] = 0
    edit_data['max_power_in'] = 0
    edit_data['max_power_out'] = 0
    edit_data['max_usable_energy'] = 0
    edit_data['power_in'] = {}
    edit_data['power_out'] = {}
    if pk != 0:
        electric_locomotive = ElectricLocomotive.objects.filter(id=pk).first()
        if is_object_visible(request.user, electric_locomotive):
            edit_data['pk'] = electric_locomotive.id
            edit_data['name'] = electric_locomotive.name
            edit_data['description'] = electric_locomotive.description
            edit_data['length'] = electric_locomotive.length
            edit_data['width'] = electric_locomotive.width
            edit_data['height'] = electric_locomotive.height
            edit_data['number_axles'] = electric_locomotive.number_axles
            edit_data['braking_force'] = electric_locomotive.air_braking_max_force
            edit_data['weight'] = electric_locomotive.weight
            edit_data['cost'] = electric_locomotive.acquisition_cost
            edit_data['efficiency_in'] = electric_locomotive.efficiency_in
            edit_data['efficiency_out'] = electric_locomotive.efficiency_out
            edit_data['max_power_in'] = electric_locomotive.max_power_in
            edit_data['max_power_out'] = electric_locomotive.max_power_out
            edit_data['max_usable_energy'] = electric_locomotive.max_usable_energy
            edit_data['power_in'] = electric_locomotive.power_in
            edit_data['power_out'] = electric_locomotive.power_out
            log_action(request, 'show-electric-locomotive.html', str(electric_locomotive.id) + ":" + electric_locomotive.name)
        else:
            log_action(request, 'show-electric-locomotive.html', 'Restricted Access', str(electric_locomotive.id) + ":" + electric_locomotive.name)
            return redirect(restricted)

    # no csv files loaded yet
    if edit_data['power_in'] is None:
        edit_data['power_in'] = {}
    if edit_data['power_out'] is None:
        edit_data['power_out'] = {}

    context = default_context(request)
    context['edit_mode_data'] = json.dumps(edit_data)

    return render(request, 'show-electric-locomotive.html', context)

@login_required
@api_view(['POST'])
def submitelectriclocomotive(request):

    # get the car type
    car_types = CarType.objects.all()
    electric_locomotive_car_type = None
    for car_type in car_types:
        if car_type.description == "Locomotive":
            electric_locomotive_car_type = car_type

    # get edit mode value
    edit_mode_id = request.data['edit_mode_id']

    # get the save group
    group_save = get_user_group_for_save(request.user)

    locomotive_name = request.data['locomotive_name']

    # diesel locomotive
    electric_locomotive = ElectricLocomotive()
    if edit_mode_id != 0:
        previous_electric_locomotive = ElectricLocomotive.objects.filter(id=edit_mode_id).first()
        if group_save.id == previous_electric_locomotive.group.id:
            previous_electric_locomotive.most_recent_version = False
        else:
            locomotive_name += ":" + group_save.name + "(group)"
        previous_electric_locomotive.save()
        electric_locomotive.parent_id = previous_electric_locomotive.id
    electric_locomotive.most_recent_version = True

    # set empty value to '0' to avoid errors
    for key in request.data:
        if request.data[key] == '':
            request.data[key] = '0'

    # create the diesel locomotive
    electric_locomotive.name = locomotive_name
    electric_locomotive.aar_type = electric_locomotive_car_type
    electric_locomotive.type = 'D'
    electric_locomotive.description = request.data['locomotive_description']
    electric_locomotive.length = request.data['locomotive_length']
    electric_locomotive.width = request.data['locomotive_width']
    electric_locomotive.height = request.data['locomotive_height']
    electric_locomotive.number_axles = request.data['locomotive_number_axles']
    electric_locomotive.air_braking_max_force = request.data['locomotive_braking_force']
    electric_locomotive.weight = request.data['locomotive_weight']
    electric_locomotive.acquisition_cost = request.data['locomotive_cost']
    electric_locomotive.efficiency_in = request.data['locomotive_efficiency_in']
    electric_locomotive.efficiency_out = request.data['locomotive_efficiency_out']
    electric_locomotive.max_power_in = request.data['locomotive_max_power_in']
    electric_locomotive.max_power_out = request.data['locomotive_max_power_out']
    electric_locomotive.max_usable_energy = request.data['locomotive_max_usable_energy']
    if "SOC" in request.data['locomotive_power_in_text']:
        electric_locomotive.power_in = parse_battery_data(request.data['locomotive_power_in_text'])
    elif len(request.data['locomotive_power_in_text'].keys()) > 0:
        electric_locomotive.power_in = request.data['locomotive_power_in_text']
    if "SOC" in request.data['locomotive_power_out_text']:
        electric_locomotive.power_out = parse_battery_data(request.data['locomotive_power_out_text'])
    elif len(request.data['locomotive_power_out_text'].keys()) > 0:
        electric_locomotive.power_out = request.data['locomotive_power_out_text']

    electric_locomotive.user = request.user
    electric_locomotive.group = group_save
    electric_locomotive.save()

    log_action(request, 'submit-electric-locomotive', str(electric_locomotive.id) + ":" + electric_locomotive.name)
    return redirect(consistlist)

@login_required
def showfuelcelllocomotive(request, pk):

    car_types = get_visible(request.user, Car.objects.all())
    all_car_types = []
    for car_type in car_types:
        all_car_types.append({"value" : car_type.id, "label" : car_type.name})

    edit_data = {}
    edit_data['pk'] = 0
    edit_data['name'] = "Enter name"
    edit_data['description'] = ""
    edit_data['length'] = 0
    edit_data['width'] = 0
    edit_data['height'] = 0
    edit_data['number_axles'] = 0
    edit_data['fuel_capacity'] = 0
    edit_data['fuel_type'] = 0
    edit_data['cost'] = 0
    edit_data['max_power'] = 0
    edit_data['power_to_wheels'] = []

    if pk != 0:
        fuelcell_locomotive = FuelCellLocomotive.objects.filter(id=pk).first()
        if is_object_visible(request.user, fuelcell_locomotive):
            edit_data['pk'] = fuelcell_locomotive.id
            edit_data['name'] = fuelcell_locomotive.name
            edit_data['description'] = fuelcell_locomotive.description
            edit_data['length'] = fuelcell_locomotive.length
            edit_data['width'] = fuelcell_locomotive.width
            edit_data['height'] = fuelcell_locomotive.height
            edit_data['number_axles'] = fuelcell_locomotive.number_axles
            edit_data['fuel_capacity'] = fuelcell_locomotive.fuel_capacity
            edit_data['fuel_type'] = fuelcell_locomotive.fuel_type
            edit_data['weight'] = fuelcell_locomotive.weight
            edit_data['cost'] = fuelcell_locomotive.acquisition_cost
            edit_data['max_power'] = fuelcell_locomotive.max_power
            edit_data['power_to_wheels'] = []
            fuelcell_locomotive_ptw = PowerToWheels.objects.filter(car=fuelcell_locomotive)
            for ptw in fuelcell_locomotive_ptw:
                edit_data['power_to_wheels'].append([ptw.power_level, ptw.fuel_consumption])
            log_action(request, 'show-fuelcell-locomotive.html', str(fuelcell_locomotive.id) + ":" + fuelcell_locomotive.name)
        else:
            log_action(request, 'show-fuelcell-locomotive.html', "Restricted Access", str(fuelcell_locomotive.id) + ":" + fuelcell_locomotive.name, None, consist)
            return redirect(restricted)

    context = default_context(request)
    context['edit_mode_data'] = json.dumps(edit_data)

    return render(request, 'show-fuelcell-locomotive.html', context)

def parse_battery_data(power_text):
    data = power_text.split("\n")
    for i,row in enumerate(data):
        if i==0:
            # ignore the first row
            pass
        elif i==1:
            tokens = row.split(',')[1:] # all but the first element
            commands = np.array(tokens, dtype=np.float32)
            socs = []
            outs = []
        elif len(row) > 0:
            tokens = row.split(',')
            socs.append(tokens[0]) # the current soc is the first element
            outs.append(np.array(tokens[1:], dtype=np.float32))

    socs = np.array(socs, dtype=np.float32)

    outs = np.array(outs)

    cmd_func = interp2d(commands, socs, outs)

    data_out = {
        'commands': commands.tolist(),
        'socs': socs.tolist(),
        'outs': outs.tolist()
    }

    return data_out


def get_locomotive_type(consist):
    consist_locomotive_types = [False, False, False]
    consist_list = ConsistCar.objects.filter(consist=consist).order_by('position')
    for car in consist_list:
        if car.car.type == 'D':
            consist_locomotive_types[0] = True
        if car.car.type == 'E':
            consist_locomotive_types[1] = True
        if car.car.type == 'C':
            consist_locomotive_types[2] = True
    return consist_locomotive_types


def get_analysis_info(request):

    route_info = {}
    routes = get_visible(request.user, Route.objects.all())
    for route in routes:
        route_info[route.id] = route.name

    consist_info = {}
    consist_locomotive_types = {}

    consists = get_visible(request.user, Consist.objects.filter(most_recent_version=True))
    for consist in consists:
        consist_info[consist.id] = consist.name
        consist_locomotive_types[consist.id] = get_locomotive_type(consist)

    return route_info, consist_info, consist_locomotive_types


@login_required
def analysis(request):
    context = default_context(request)

    log_action(request, 'analysis.html')
    return render(request, 'analysis-setup.html', context)


@login_required
def tradestudies(request):
    context = default_context(request)
    group_save = get_user_group_for_save(request.user)
    session = Session(user=request.user, group=group_save)
    session.save()
    context['session_id'] = session.id
    log_action(request, 'trade-studies.html')
    return render(request, 'trade-studies.html', context)

@login_required
def ltd_details(request, result_id):
    context = default_context(request)
    print("result id: ", result_id)
    context['result_id'] = result_id

    return render(request, 'ltd-results.html', context)

@login_required
def ltd_details_summaryplot(request, result_id):
    context = default_context(request)
    print("result id: ", result_id)
    context['result_id'] = result_id

    return render(request, 'ltd-results-summary-plot.html', context)


@login_required
def export_ltd_details(request, result_id):
    result = list(LTDResults.objects.filter(id=result_id).values())
    response = JsonResponse(result, safe=False)
    response['Content-Type'] = 'application/force-download'
    response['Content-Disposition'] = 'attachment; filename="analysis_results_' + str(result_id) + '.json"'
    return response

@login_required
def tradespace(request, session_id):
    print('trying to load tradspace: ' + session_id)
    print('number of results: ', LTDResults.objects.filter(session_id=session_id).count())
    result_ids = LTDResults.objects.filter(session_id=session_id).values_list('id', flat=True)
    context = default_context(request)
    context['result_ids'] = list(result_ids)
    print("sending the resultids: ", context['result_ids'])

    return render(request, 'trade-results.html', context)

@login_required
def exporttradespace(request, session_id):

    titles = ['duration_hrs',
        'diesel_consumed_kg',
        'hydrogen_consumed_kg',
        'max_speed',
        'route',
        'consist',
        'policy',
        'braking',
        'rapid',
        'status',
        'total_weight_tons',
        'number_cars',
        'trailing_weight_tons',
        'max_power_hp',
        'max_battery_energy_kw',
        'result_code',
        'ghg_co_kg',
        'ghg_hc_kg',
        'ghg_no_kg',
        'ghg_pm_kg']
    results = LTDResults.objects.filter(session_id=session_id)

    response = HttpResponse()
    response['Content-Type'] = 'application/force-download'
    response['Content-Disposition'] = 'attachment; filename="data_session.txt"'
    writer = csv.writer(response, delimiter='\t')
    writer.writerow(titles)
    for result in results:
        if result.result_code == 0:
            # we have a completed ltd analysis get the stored out put from the analysis
            output = result.result
            perfs = output['perfs']
            s = "automatic"
            if result.policy.type == 'user_fixed':
                str = ""
                for p in result.policy.power_order:
                    if p is not None:
                        str += p + ", "
                s = str[:-2]
            consist_info = get_consist_data(result.consist)
            values = [output['duration']/3600,
                perfs['fuel_diesel'][-1],
                perfs['fuel_hydrogen'][-1],
                result.policy.max_speed,
                result.route.name,
                result.consist.name,
                s,
                result.policy.braking,
                result.rapid,
                result.status,
                consist_info['weight_tons'],
                consist_info['number_cars'],
                consist_info['trailing_tons'],
                consist_info['power_hp'],
                consist_info['battery_energy'],
                result.result_code,
                round(perfs['co'][-1]/1000,1),
                round(perfs['hc'][-1]/1000,1),
                round(perfs['no'][-1]/1000,1),
                round(perfs['pm'][-1]/1000,1)]
            writer.writerow(values)

    return response


@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR')
    log_action(request, 'login', str(ip))

@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR')
    log_action(request, 'logout', str(ip))

@receiver(user_login_failed)
def user_login_failed_callback(sender, credentials, **kwargs):
    log_action(None, 'failed_login', credentials.get('username', None))

def log_action(request, site, description="", meta_data=None, route=None, consist=None):
    datalog = DataLog()
    if request is not None:
        if not request.user.is_anonymous:
            datalog.user = request.user
    datalog.site = site
    datalog.description = description
    datalog.meta_data = meta_data
    datalog.route = route
    datalog.consist = consist
    # eastern time zone is 4 hours off so subtracting 5 hours for now
    datalog.log_time = datetime.now(timezone('EST')) - timedelta(hours=5, minutes=0)
    datalog.save()
