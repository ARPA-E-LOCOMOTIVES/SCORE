# Copyright (c) 2022, The Pennsylvania State University
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.

from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('locomotives')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
# app.config_from_object('celeryconfig')
app.conf.update(
    task_serializer = 'json',
    result_serializer = 'json',
    accept_content = ['json'],
    broker_url = settings.CELERY_BROKER_URL,
    result_backend = settings.CELERY_RESULT_BACKEND ,
    imports = ('locomotives.tasks', ),
)

# app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))