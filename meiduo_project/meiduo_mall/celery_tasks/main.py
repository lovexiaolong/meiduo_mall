from celery import Celery

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")

#用Celery创建对象
celery_app = Celery('meiduo')

celery_app.config_from_object('celery_tasks.config')

# 让 celery_app 自动捕获目标地址下的任务
celery_app.autodiscover_tasks(['celery_tasks.sms'])

