from celery import Celery
import sys
sys.setrecursionlimit(100000)
# 为 celery 使用 django 配置文件进行设置
import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'

# 创建 celery 实例
celery_app = Celery('meiduo')

# 加载 celery 配置
celery_app.config_from_object('celery_tasks.config')

# 自动注册 celery 任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email'])