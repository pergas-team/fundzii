from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# تنظیمات دجانگو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SLIMS.envs.common')

app = Celery('celery')

# بارگذاری تنظیمات از فایل تنظیمات دجانگو
app.config_from_object('django.conf:settings', namespace='CELERY')

# خودکار کشف کردن تسک‌ها در برنامه‌های Django
app.autodiscover_tasks()