from django.views import View
from django_redis import get_redis_connection
from django import http
import random

from celery_tasks.yuntongxun.ccp_sms import CCP
from meiduo_mall.libs.captcha.captcha import captcha
import logging

from verifications import crons

logger = logging.getLogger('django')
# logger.error()
# logger.info()


# get
# /image_codes/uuid
# 接收参数  --- 生成图形验证码 ---  保存 ---- 返回
from meiduo_mall.utils.response_code import RETCODE


class ImageCodeView(View):

    def get(self, request, uuid):
        '''
        生成图形验证码, 返回
        :param request:
        :param uuid:
        :return:
        '''
        # 1.生成图形验证码
        text, image = captcha.generate_captcha()

        # 2.链接redis, 生成一个链接对象
        redis_conn = get_redis_connection('verify_code')

        # 3.保存到redis
        # redis_conn.setex('key', 'time', 'value')
        redis_conn.setex('image_code_%s' % uuid, 300, text)

        # 4.返回图片
        return http.HttpResponse(image, content_type='image/jpg')



# get
class SMSCodeView(View):

    def get(self, request, mobile):
        '''
        检验图形验证码,发送短信验证码
        :param request:
        :param mobile:
        :return:
        '''
        # 1.接收参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 2.验证参数
        if not all([image_code_client, uuid]):
            return http.JsonResponse({'code':RETCODE.NECESSARYPARAMERR,
                                      'errmsg':'参数不能为空'})

        # 3.链接redis
        redis_conn = get_redis_connection('verify_code')

        # 4.从redis的2号库取出图形验证吗
        image_code_server = redis_conn.get('image_code_%s' % uuid)
        if image_code_server is None:
            return http.JsonResponse({'code':RETCODE.IMAGECODEERR,
                                      'errmsg':'图形验证码失效'})

        # 5.删除redis中的图形验证吗
        try:
            redis_conn.delete('image_code_%s' % uuid)
        except Exception as e:
            logger.error(e)

        # 6.对比
        if image_code_client.lower() != image_code_server.decode().lower():
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR,
                                      'errmsg': '两个图形验证码不一致'})

        # 7. 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        print(sms_code)

        # 8. 保存到redis
        redis_conn.setex('sms_code_%s' % mobile, crons.SMS_CODE_REDIS_EXPIRES, sms_code)

        # 9. 发送(容联云)
        CCP().send_template_sms(mobile, [sms_code, 5], 1)

        # 10. 返回
        return http.JsonResponse({'code':RETCODE.OK,
                                  'errmsg':'ok'})



















