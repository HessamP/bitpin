import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bitpin.settings')
app = Celery('bitpin')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
CELERY_IMPORTS = ('blog.signals',)
app.conf.broker_connection_retry_on_startup = True

app.conf.beat_schedule = {
    'check-zscores-every-30-minute': {
        'task': 'blog.tasks.check_new_scores',
        'schedule': 30 * 60,  # secs
        'options': {
            'expires': 120,
        },
    },

}
