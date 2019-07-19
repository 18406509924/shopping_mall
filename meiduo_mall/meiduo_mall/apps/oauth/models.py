from django.db import models

# Create your models here.
from meiduo_mall.utils.BaseModel import BaseModel




class OauthQQUser(BaseModel):

    user = models.ForeignKey('users.Users',
                             on_delete=models.CASCADE,
                             verbose_name='用户')

    openid = models.CharField(max_length=64, db_index=True, verbose_name='openid')


    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'qq登录用户'
        verbose_name_plural = verbose_name