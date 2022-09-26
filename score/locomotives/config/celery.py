from __future__ import absolute_import
import os
from celery import Celery

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
    broker_url = 'redis://localhost:6379',
    result_backend = 'redis://localhost:6379',
    imports = ('locomotives.tasks', ),
)

# app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))