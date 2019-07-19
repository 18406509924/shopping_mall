from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer
from django.conf import settings
from itsdangerous import BadData

# Create your models here.
from meiduo_mall.utils.BaseModel import BaseModel


class Users(AbstractUser):
    # 添加一个记录手机号的字段
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')

    email_active = models.BooleanField(default=False, verbose_name='是否激活')

    # 记录默认地址的字段
    default_address = models.ForeignKey('Address',
                                        related_name='users',
                                        null=True,
                                        blank=True,
                                        on_delete=models.SET_NULL,
                                        verbose_name='默认地址')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def generate_verify_email_url(self):
        '''
        拼接生成一个验证链接
        :return:
        '''
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=3600)

        dict = {
            'user_id': self.id,
            'email': self.email
        }

        token = serializer.dumps(dict).decode()  # bytes

        verify_url = settings.EMAIL_VERIFY_URL + '?token=' + token

        return verify_url

    @classmethod
    def check_verify_email_url(cls, token):
        '''
        把token解密===> 返回user
        :return:
        '''
        # 1.获取工具类对象
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=3600)

        # 2.解密
        try:
            data = serializer.loads(token)
        except BadData:
            return None

        # 3.根据user_id email ===> user
        user_id = data.get('user_id')
        email = data.get('email')

        try:
            user = Users.objects.get(id=user_id, email=email)
        except Exception as e:
            # 5.如果没有user 返回None
            return None
        else:
            # 4.返回
            return user


# user = Users()
# user.generate_verify_email_url()


class Address(BaseModel):
    user = models.ForeignKey(Users,
                             on_delete=models.CASCADE,
                             related_name='addresses',
                             verbose_name='用户')

    province = models.ForeignKey('areas.Area',
                                 on_delete=models.PROTECT,
                                 related_name='province_areas',
                                 verbose_name='省')

    city = models.ForeignKey('areas.Area',
                             on_delete=models.PROTECT,
                             related_name='city_areas',
                             verbose_name='市')

    district = models.ForeignKey('areas.Area',
                                 on_delete=models.PROTECT,
                                 related_name='district_areas',
                                 verbose_name='区')

    title = models.CharField(max_length=20, verbose_name='标题')

    receiver = models.CharField(max_length=20, verbose_name='收货人')

    place = models.CharField(max_length=50, verbose_name='收货地址')

    mobile = models.CharField(max_length=11, verbose_name='手机号')

    tel = models.CharField(max_length=20,
                           null=True,
                           blank=True,
                           default='',
                           verbose_name='电话号码')

    email = models.CharField(max_length=20,
                             null=True,
                             blank=True,
                             default='',
                             verbose_name='email')

    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '地址'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']
