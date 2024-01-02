# Copyright (c) 2022, The Pennsylvania State University
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.


from locomotives.models import Consist, Route, Policy, LTDResults, ConsistCar, Segment, Session, Line, Railroad, Yard, Route2
from locomotives.serializers import ConsistSerializer, Route2Serializer, LineSerializer, RailroadSerializer, YardSerializer
from locomotives.ltd import MPH2MPS, get_segments
from locomotives.views import get_visible, get_consist_info
from locomotives.consist_data import get_consist_data

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import api_view, renderer_classes, permission_classes

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from .tasks import eval_ltd
from celery.result import AsyncResult
from .ltd import get_elevations, get_lines, update_elevations

import json

KW2HP = 1.34102     # convert kw to hp
TONNE2TON = 1.10231 # convert tonne (1000 kg) to ton (2000 lbs)
MPH2MPS = 0.44704   # convert MPH to m/s
MI2M = 1609.34      # convert mile to meter

class ConsistList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Consist.objects.all()
    serializer_class = ConsistSerializer

class ConsistDetail(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Consist.objects.all()
    serializer_class = ConsistSerializer

class RouteList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Route.objects.all()
    serializer_class = Route2Serializer

class RouteDetail(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Route.objects.all()
    serializer_class = Route2Serializer

class LineList(generics.ListCreateAPIView):
    # permission_classes = [IsAuthenticated]
    queryset = Line.objects.all()
    serializer_class = LineSerializer

class RailroadList(generics.ListAPIView):
    queryset = Railroad.objects.all()
    serializer_class = RailroadSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def add_line(request):
    data = request.data
    fra_id = int(data.get('fra_id'))
    from_node = int(data.get('from_node'))
    to_node = int(data.get('to_node'))
    length = float(data.get('length'))
    net = data.get('net')
    rights = data.getlist('rights')
    # convert the strings in the array to integers
    # this is a single dimension array of strings that represent floats
    # we will convert them to floats, but maintain the single dimension
    elevation = [float(f) for f in data.getlist('elevation')]
    xy = [float(f) for f in data.getlist('xy')]
    lnglat = [float(f) for f in data.getlist('lnglat')]
    distance = [float(f) for f in data.getlist('distance')]
    gradient = [float(f) for f in data.getlist('gradient')]
    curvature = [float(f) for f in data.getlist('curvature')]

    temp_speed = data.getlist('max_speed')
    # if no speed was included then max speed is a function of curvature for each segment in the line.
    if len(temp_speed)==0:
        max_speed = []
        for curve in curvature:
            if curve <= 2.0:
                speed = 60
            elif curve <= 3.0:
                speed = 55
            elif curve <= 4.0:
                speed = 50
            elif curve <= 5.0:
                speed = 45
            elif curve <= 6.0:
                speed = 40
            elif curve <= 8.0:
                speed = 35
            elif curve <= 9.0:
                speed = 30
            elif curve <= 10.0:
                speed = 25
            else:
                speed = 20
            max_speed.append(speed)

    else:
        max_speed = [float(f) for f in temp_speed]
        
    try:
        obj = Line.objects.get(fra_id=fra_id)
        obj.from_node=from_node
        obj.to_node=to_node
        obj.length=length
        obj.rights=rights
        obj.net=net
        obj.max_speed=max_speed
        obj.xy=xy
        obj.lnglat=lnglat
        obj.elevation=elevation
        obj.distance=distance
        obj.gradient=gradient
        obj.curvature=curvature
        obj.save()
        print('udpated: ', obj.fra_id )
    except Line.DoesNotExist:
        obj = Line(fra_id=fra_id, from_node=from_node, to_node=to_node, length=length, net=net, max_speed=max_speed, rights=rights, elevation=elevation, xy=xy, lnglat=lnglat, distance=distance, gradient=gradient, curvature=curvature)
        obj.save()
        print('added: ', obj.fra_id)

    return JsonResponse({'results':1}, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def get_railroad_lines(request, code):
    print(code)
    try:
        status = 200
        lines = Line.objects.filter(rights__contains=code)
        print(lines.count())
        all_lines = Line.objects.all()
        print(all_lines.count())
        results = LineSerializer(lines, many=True).data
    except Railroad.DoesNotExist:
        status = 204
        results = {}
    
    return JsonResponse({'results': results}, status=status)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def get_line(request, fra_id):
    try:
        obj = Line.objects.get(fra_id=fra_id)
        status = 200
        results = LineSerializer(obj).data
    except Line.DoesNotExist:
        status = 204
        results = {}
    
    return JsonResponse({'results': results}, status=status)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def delete_line(request, fra_id):
    try:
        obj = Line.objects.get(fra_id=fra_id)
        status = 200
        obj.delete()
    except:
        status = 404
    
    return JsonResponse({}, status=status)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def add_route(request):
    data = request.data
    origin = Yard.objects.get(pk=data.get('origin'))
    destination = Yard.objects.get(pk=data.get('destination'))  
    owner = Railroad.objects.get(pk=data.get('owner'))
    path = [int(i) for i in data.getlist('path')]

    try:
        obj = Route2.objects.get(origin=origin, destination=destination)
        obj.owner=owner
        obj.path=path
        obj.save()
        print('updated route')
    except Route2.DoesNotExist:
        obj = Route2(origin=origin, destination=destination, owner=owner, path=path)
        obj.save()
        print('added route')

    return JsonResponse({'results': obj.id}, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def get_route_detail(request, pk):

    lines = get_lines(pk)


    # this isn't doing anything at this point other than to query the database
    return JsonResponse({'results': lines}, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def get_route_elevations(request, pk):

    elevations = get_elevations(pk)


    # this isn't doing anything at this point other than to query the database
    return JsonResponse({'results': elevations}, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def update_route_elevations(request):

    data = request.data
    route = data.get('route')
    elevations = [float(i) for i in data.getlist('elevations')]
    gradients = [float(i) for i in data.getlist('gradients')]
    
    result = update_elevations(route, elevations, gradients)

    # this isn't doing anything at this point other than to query the database
    return JsonResponse({'results': 1}, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def add_yard(request):
    data = request.data

    print(data)

    return JsonResponse({'results': 1}, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def all_yard(request):
    yard_list = Yard.objects.all()
    results=[]
    for yard in yard_list:
        results.append({'id': yard.pk, 'name': yard.name})

    return JsonResponse({'results': results}, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def get_yard(request, yard_id):
    try:
        obj = Yard.objects.get(pk=yard_id)
        status = 200
        results = YardSerializer(obj).data
    except Yard.DoesNotExist:
        status = 204
        results = {}
    
    return JsonResponse({'results': results}, status=status)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def evaluate(request):
    data = request.data
    # print('data: ', request.data)
    route_id = data.getlist('routes', [27])[0]
    consist_id = data.getlist('consists', [16])[0]
    policy_type = data.get('policy_type', ['user_fixed'])
    power_order = data.getlist('power_order[]')
    braking = data.get('braking', ['maximum_braking'])
    max_speed = float(data.get('max_speed', 60)) * MPH2MPS
    session_id = data.get('session_id', 0)
    if session_id != 0:
        session = Session.objects.get(id=session_id)
    else:
        session = None

    if data.get('rapid', 'true') == "true":
        rapid = True
    else:
        rapid = False

    r = Route.objects.get(id=route_id)
    c = Consist.objects.get(id=consist_id)
    # we can change the max speed later on in the interface
    p, created = Policy.objects.get_or_create(type=policy_type, power_order=power_order, braking=braking, max_speed=max_speed)
    
    print("about to get an LTDResults object with session: ", session)

    result, created = LTDResults.objects.get_or_create(
       route = r,
       consist = c,
       policy = p,
       rapid = rapid,
       session = session
    )

    # temporarily force the evaluation till things are working properly
    result.status = 0
    result.result_code = -1
    result.save()

    task = eval_ltd.delay(result.id)

    print("new LTDResult: ", created, result.id)

    # return JsonResponse({'result_id': result.id}, status=202)
    return JsonResponse({'result_id': result.id}, status=202)

def home(request):
    return render(request, 'api_home.html')

def task_status(request, task_id):
    task = AsyncResult(task_id)

    if task.state == 'FAILURE' or task.status == 'PENDING':
        response = {
            'task_id': task_id,
            'state': task.state,
            'progression': "None",
            'info':str(task.info)
        }
        return JsonResponse(response, status=200)
    current = task.info.get('current', 0)
    total = task.info.get('total', 1)
    progression = (int(current) / int(total)) * 100 # to display a percentage of progression
    response = {
        'task_id': task_id,
        'state': task.state,
        'progression': progression,
        'info': task.info.get('result_id', "None")
    }
    return JsonResponse(response, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ltd_status(request, result_id):
    result = LTDResults.objects.get(id = result_id)
    response = {
        'result_id': result.id,
        'state': result.result_code,
        'progression': result.status,
        'route': result.route.name,
        'consist': result.consist.name,
        'policy': result.policy.name(),
        'max_speed': round(result.policy.max_speed/MPH2MPS),  # convert back to MPH
        'rapid': result.rapid,
    }
    return JsonResponse(response, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ltd_result(request, result_id):
    result = LTDResults.objects.get(id = result_id)
    response = {
        'route': {
            'name': result.route.name,
            'id' : result.route.id
        },
        'consist': {
            'name' : result.consist.name,
            'id' : result.consist.id
        },
        'policy': result.policy.name(),
        'max_speed': result.policy.max_speed/MPH2MPS,
        'rapid': result.rapid,
        'data': result.result,
        'superuser': request.user.is_superuser,
    }
    return JsonResponse(response, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_consist_data(request, pk):
    # consist = Consist.objects.get(id = pk)
    consist, consist_info, consist_common_info, consist_locomotive_types = get_consist_info(pk)
    return JsonResponse(consist_info, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_elevation(request, pk):
    # route = Route.objects.get(id=pk)
    # segments = Segment.objects.filter(route=route).order_by('segment_order').all()
    # route_dist_seg = 0
    # elevation_data = []
    # for i, seg in enumerate(segments):
    #     route_dist_seg += seg.arc_distance
    #    elevation_data.append([route_dist_seg, seg.locations.all()[1].smooth_elev_m])
    elevation_data, elevation_gain, elevation_loss = get_elevations(pk)
    elevation_lines = { 'data': elevation_data}
    return JsonResponse(elevation_lines, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_route_list(request):
    route_info = {}
    routes = get_visible(request.user, Route.objects.all())
    for route in routes:
        route_info[route.id] = route.name

    return JsonResponse(route_info, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_route_data(request, pk):
    route = Route.objects.get(id=pk)
    route_data = get_segments(route)
    return JsonResponse(route_data, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_consist_list(request):
    consist_info = {}

    consists = get_visible(request.user, Consist.objects.filter(most_recent_version=True))
    for consist in consists:
        consist_info[consist.id] = consist.name

    return JsonResponse(consist_info, status=200)

def get_locomotive_type(consist):
    consist_locomotive_types = []
    consist_list = ConsistCar.objects.filter(consist=consist)
    for car in consist_list:
        if car.car.type == 'D':
            consist_locomotive_types.append('diesel')
        if car.car.type == 'E':
            consist_locomotive_types.append('battery')
        if car.car.type == 'C':
            consist_locomotive_types.append('fuelcell')
    return consist_locomotive_types

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_consist_powers(request, pk):

    consist = Consist.objects.get(id=pk)
    results = {'data': get_locomotive_type(consist)}

    return JsonResponse(results, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ltd_summary(request, result_id):
    # this function will return a dictionary of values for a design in the tradespace
    # it will only return values if the analysis has completed successfully
    # print('checking result: ' + result_id)
    result = LTDResults.objects.get(id = result_id)
    data = {}
    if result.result_code in [0, 2]:
        # we have a completed ltd analysis get the stored out put from the analysis
        output = result.result
        data['constant'] = 1
        data['duration_hrs'] = output['duration']/3600      # convert from seconds to hrs
        perfs = output['perfs']
        consist_info = get_consist_data(result.consist)
        data['diesel_consumed_kg'] = perfs['fuel_diesel'][-1]
        data['hydrogen_consumed_kg'] = perfs['fuel_hydrogen'][-1]
        data['energy_cost'] = perfs['fuel_cost']
        data['cost_per_ton_mile'] = perfs['fuel_cost']/(consist_info['freight_tons']*output['distances'][-1]/MI2M)
        data['max_speed_mph'] = result.policy.max_speed/MPH2MPS
        data['route_id'] = result.route.id
        data['route_name'] = result.route.name
        data['consist_id'] = result.consist.id
        data['consist_name'] = result.consist.name
        s = "automatic"
        if result.policy.type == 'user_fixed':
            str = ""
            for p in result.policy.power_order:
                if p is not None:
                    str += p + ", "
            s = str[:-2]
        data['power_order'] = s
        data['braking'] = result.policy.braking
        data['total_weight_tons'] = consist_info['weight_tons']
        data['number_of_cars'] = consist_info['number_cars']
        data['trailing_weight_tons'] =  consist_info['trailing_tons']
        data['max_power_hp'] = consist_info['power_hp']
        data['max_battery_energy_kw-hr'] = consist_info['battery_energy']
        data['diesel_power_hp'] = consist_info['diesel_power_hp']
        data['battery_power_kw'] = consist_info['battery_power_kw']
        data['fuelcell_power_kw'] = consist_info['fuelcell_power_kw']
        data['tonmileperhour'] = consist_info['trailing_tons']*(output['distances'][-1]/MI2M)/data['duration_hrs']
        data['actual_max_speed_mph'] = max(output['max'])/MPH2MPS  
        
        total_diesel_energy = sum(output['energy']['diesel'])
        total_battery_energy = sum(output['energy']['battery'])
        total_regen_energy = sum(output['energy']['regen'])
        total_fuelcell_energy = sum(output['energy']['fuelcell'])
        total_energy = total_diesel_energy + total_fuelcell_energy + total_battery_energy + total_regen_energy

        data['diesel_proportion'] = total_diesel_energy/total_energy
        data['battery_proportion'] = total_battery_energy/total_energy
        data['regen_proportion'] = total_regen_energy/total_energy
        data['fuelcell_proportion'] = total_fuelcell_energy/total_energy

        data['status'] = result.result_code

    return JsonResponse(data, status=200)
