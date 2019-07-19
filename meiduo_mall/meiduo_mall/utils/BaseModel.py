# 增加一个模型类的基类
from django.db import models


class BaseModel(models.Model):

    # 创建时间
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    # 更新时间
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        # 抽象: true
        abstract = True