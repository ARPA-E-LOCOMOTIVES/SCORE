# Copyright (c) 2022, The Pennsylvania State University
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.


from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token

from locomotives import views
from locomotives import api_views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('routelist/', views.routelist, name="routelist"),
    path('route-info/<int:id>/', views.routeinfo, name='routeinfo'),
    path('consistlist/', views.consistlist, name="consistlist"),
    path('consist-info/<int:pk>', views.consistinfo, name='consistinfo'),
    path('create-consist/', views.createconsist, name='createconsist'),
    path('edit-consist/<int:pk>', views.editconsist, name='editconsist'),
    path('submit-consist/', views.submitconsist, name='submitconsist'),
    path('create-diesel-locomotive/', views.creatediesellocomotive, name='creatediesellocomotive'),
    path('edit-diesel-locomotive/<int:pk>', views.editdiesellocomotive, name='editdiesellocomotive'),
    path('show-diesel-locomotive/<int:pk>', views.showdiesellocomotive, name='showdiesellocomotive'),
    path('submit-diesel-locomotive/', views.submitdiesellocomotive, name='submitdiesellocomotive'),
    path('create-electric-locomotive/', views.createelectriclocomotive, name='createelectriclocomotive'),
    path('edit-electric-locomotive/<int:pk>', views.editelectriclocomotive, name='editelectriclocomotive'),
    path('show-electric-locomotive/<int:pk>', views.showelectriclocomotive, name='showelectriclocomotive'),
    path('show-fuelcell-locomotive/<int:pk>', views.showfuelcelllocomotive, name='showfuelcelllocomotive'),
    path('submit-electric-locomotive/', views.submitelectriclocomotive, name='submitelectriclocomotive'),
    path('analysis/', views.analysis, name='analysis'),
    path('tradestudies/', views.tradestudies, name='tradestudies'),
    path('tradespace/<str:session_id>/', views.tradespace, name='tradespace'),
    path('exporttradespace/<str:session_id>/', views.exporttradespace, name='exporttradespace'),
    path('oops/', views.restricted, name="restricted"),
    path('signup/', views.signup, name="signup"),
    path('submit_signup/', views.submit_signup, name="submit_signup"),
    path('user-requests/', views.user_requests, name="user_requests"),
    path('add-user-request/<int:pk>', views.adduserrequest, name="adduserrequest"),
    path('add-user/', views.adduser, name="adduser"),
    path('ignore-user/<int:pk>', views.ignoreuser, name="ignoreuser"),
    path('about/', views.about, name="about"),
    path('contact/', views.contact, name="contact"),
    path('datalogs/', views.datalogs, name="datalogs"),
    path('feedback/', views.feedback, name="feedback"),
    path('documentation/', views.documentation, name="documentation"),
    path('detaileddocumentation/', views.detaileddocumentation, name="detaileddocumentation"),
    path('providefeedback/', views.providefeedback, name="providefeedback"),
    path('submit_feeedback/', views.submit_feedback, name="submit_feedback"),
    path('ltd_details_summaryplot/<str:result_id>', views.ltd_details_summaryplot, name='ltd_details_summaryplot'),
    path('ltd_details/<str:result_id>', views.ltd_details, name='ltd_details'),
    path('export_ltd_details/<str:result_id>', views.export_ltd_details, name='export_ltd_details'),
    path('powerpoliciesdoc/', views.powerpoliciesdoc, name="powerpoliciesdoc"),
    path('api/evaluate/', api_views.evaluate),
    path('api/routes/', api_views.RouteList.as_view()),
    path('api/consists', api_views.ConsistList.as_view()),
    path('api/ltd-status/<str:result_id>/', api_views.ltd_status, name='ltd_status'),
    path('api/get_ltd_result/<str:result_id>/', api_views.get_ltd_result, name='get_ltd_result'),
    path('api/get_consist_info/<str:pk>/', api_views.get_consist_info, name="get_consist_info"),
    path('api/get_elevation/<str:pk>/', api_views.get_elevation, name='get_elevation'),
    path('api/get_route_list/', api_views.get_route_list, name='get_route_list'),
    path('api/get_route_data/<str:pk>/', api_views.get_route_data, name='get_route_data'),
    path('api/get_consist_list/', api_views.get_consist_list, name='get_consist_list'),
    path('api/get_consist_powers/<str:pk>/', api_views.get_consist_powers, name='get_consist_powers'),
    path('api/get_ltd_summary/<str:result_id>/', api_views.get_ltd_summary, name='get_ltd_summary')
]

