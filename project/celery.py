import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
app = Celery("project")
app.conf.update(timezone="Asia/Kathmandu")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_schedule = {
    "delete-expired-tokens": {
        "task": "core.tasks.remove_expired_tokens",
        "schedule": crontab(hour=22, minute=0),
        "args": ("Expired tokens removed.",),
    },
}