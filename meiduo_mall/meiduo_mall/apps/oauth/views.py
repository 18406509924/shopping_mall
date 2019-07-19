from QQLoginTool.QQtool import OAuthQQ
from django.shortcuts import render
from django import http

# Create your views here.
from django.conf import settings
from django.views import View

from meiduo_mall.utils.response_code import RETCODE
import logging

logger = logging.getLogger('django')


class QQURLView(View):
    """提供QQ登录页面网址
    https://graph.qq.com/oauth2.0/authorize?
    response_type=code&
    client_id=xxx&
    redirect_uri=xxx&
    state=xxx
    """

    def get(self, request):
        # next 表示从哪个页面进入到的登录页面，将来登录成功后，就自动回到那个页面
        next = request.GET.get('next')

        # 获取 QQ 登录页面网址
        # 创建 OAuthQQ 类的对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        # 调用对象的获取 qq 地址方法
        login_url = oauth.get_qq_url()

        # 返回登录地址
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})


class QQUserView(View):
    """用户扫码登录的回调处理"""

    def get(self, request):
        """Oauth2.0 认证"""
        # 提取code请求参数
        code = request.GET.get('code')
        if not code:
            return http.HttpResponseForbidden('缺少code')

        # 创建工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)

        try:
            # 携带 code 向 QQ服务器 请求 access_token
            access_token = oauth.get_access_token(code)

            # 携带 access_token 向 QQ服务器 请求 openid
            openid = oauth.get_open_id(access_token)

        except Exception as e:
            # 如果上面获取 openid 出错, 则验证失败
            logger.error(e)
            # 返回结果
            return http.HttpResponseServerError('OAuth2.0认证失败')

