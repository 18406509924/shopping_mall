import json

from django.contrib.auth import login, authenticate
from django.db import DatabaseError
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection
# from django_redis.serializers import json
import logging

logger = logging.getLogger('django')
from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.view import LoginRequiredMixin
from meiduo_mall.utils.view import LoginRequiredJsonMixin
from .models import Users, Address
from django import http
from django.contrib.auth import logout



import re


# GET /register
# render()
class RegisterView(View):

    def get(self, request):
        '''
        返回注册页面
        :param request:
        :return:
        '''
        return render(request, 'register.html')

    # post
    # /register  表单
    # 接收---校验---保存---返回
    def post(self, request):
        '''
        接收数据, 保存
        :param request:
        :return:
        '''
        # 1.接收参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')
        sms_code_client = request.POST.get('sms_code')

        # 2.检验参数( 整体检验 + 单个检验)
        if not all([username, password, password2, mobile, allow]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('用户名不符合格式')

        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return http.HttpResponseForbidden('密码不符合格式')

        if password != password2:
            return http.HttpResponseForbidden('两个密码不一致')

        if not re.match(r'^1[345789]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号不符合格式')

        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')

        # 增加短信验证码逻辑:
        redis_conn = get_redis_connection('verify_code')

        sms_code_server = redis_conn.get('sms_code_%s' % mobile)
        if sms_code_server is None:
            return render(request, 'register.html', {'sms_code_errmsg': '短信验证码失效'})

        # 对比:
        if sms_code_server.decode() != sms_code_client:
            return render(request, 'register.html', {'sms_code_errmsg': '两次对比不一致'})

        # 3. 保存数据到mysql 如果出错, 报错
        try:
            user = Users.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg': "注册失败"})

        # 5. 状态保持:
        login(request, user)

        # 4. 重定向到首页
        # return http.HttpResponse('将要重定向, 代码需要改')

        # return redirect(reverse('contents:index'))
        response = redirect(reverse('contents:index'))

        # 在响应对象中设置用户名信息.
        # 将用户名写入到 cookie，有效期 15 天
        response.set_cookie('username', user.username, max_age = 3600 * 24 * 15)

        # 返回响应结果
        return response




# username
# GET
# BOOL/STATUS/int
class UsernameCountView(View):

    def get(self, request, username):
        '''
        返回用户名个数
        :param request:
        :param username:
        :return:
        '''
        # 1. 去User中查询该用户的个数
        count = Users.objects.filter(username=username).count()

        # 2. 返回 json
        return http.JsonResponse({'code': 0,
                                  'errmsg': 'ok',
                                  'count': count})


# GET
# /mobile/(?P<mobile>1[3-9]\d{9})/count
# 查询 ====> count
class MobileCountView(View):

    def get(self, request, mobile):
        '''
        查询手机号的个数,并返回
        :param request:
        :param mobile:
        :return:
        '''
        count = Users.objects.filter(mobile=mobile).count()

        return http.JsonResponse({'code': 0,
                                  'errmsg': 'ok',
                                  'count': count})


class LoginView(View):
    """用户名登录"""

    def get(self, request):
        """提供登录界面的接口"""
        # 返回登录界面
        return render(request, 'login.html')

    def post(self, request):
        """
        实现登录逻辑
        :param request: 请求对象
        :return: 登录结果
        """
        # 接受参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        # 校验参数
        # 判断参数是否齐全
        # 这里注意: remembered 这个参数可以是 None 或是 'on'
        # 所以我们不对它是否存在进行判断:
        if not all([username, password]):
            return http.HttpResponseForbidden('缺少必传参数')

        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入正确的用户名或手机号')

        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')

        # 认证登录用户
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})

        # 实现状态保持
        login(request, user)
        # 设置状态保持的周期
        if remembered != 'on':
            # 不记住用户：浏览器会话结束就过期
            request.session.set_expiry(0)
        else:
            # 记住用户：None 表示两周后过期
            request.session.set_expiry(None)

        # 响应登录结果
        # 生成响应对象
        response = redirect(reverse('contents:index'))

        # 在响应对象中设置用户名信息.
        # 将用户名写入到 cookie，有效期 15 天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)

        # 返回响应结果
        return response


class LogoutView(View):
    """退出登录"""

    def get(self, request):
        """实现退出登录逻辑"""

        # 清理 session
        logout(request)

        # 退出登录，重定向到登录页
        response = redirect(reverse('contents:index'))

        # 退出登录时清除 cookie 中的 username
        response.delete_cookie('username')

        # 返回响应
        return response


class UserInfoView(LoginRequiredMixin, View):

    def get(self, request):
        '''
        展示用户中心页面
        :param request:
        :return:
        '''

        # 从mysql中获取数据
        # 拼接
        context = {
            'username':request.user.username,
            'mobile':request.user.mobile,
            'email':request.user.email,
            'email_active':request.user.email_active
        }
        # 返回
        return render(request, 'user_center_info.html', context)


class EmailView(LoginRequiredMixin, View):

    def put(self, request):
        '''
        修改当前用户的email
        :param request:
        :return:
        '''
        # 1.接收参数
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 2.检验
        if not email:
            return http.HttpResponseForbidden('缺少必传参数')

        # TODO 正则没写:
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('email格式不对')

        # 3.更新数据库中的email
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            return http.JsonResponse({'code':RETCODE.DBERR, 'errmsg':'数据库保存出错'})

        # 4.返回
        return http.JsonResponse({'code': RETCODE.OK,
                                  'errmsg': 'ok'})


class VerifyEmailView(View):

        def get(self, request):
            '''
            验证用户邮箱是否为真
            :param request:
            :return:
            '''
            # 1.接收参数(token)
            token = request.GET.get('token')

            # 2.检验
            if not token:
                return http.HttpResponseForbidden('缺少必传参数')

            # 3.解密(token ===> user_id, email ===> user)
            user = Users.check_verify_email_url(token)
            if user is None:
                return http.HttpResponseForbidden('token无效')

            # 4.更改数据库(email_active)
            try:
                user.email_active = True
                user.save()
            except Exception as e:
                return http.HttpResponseForbidden('激活失败')

            # 5.返回(重定向到用户中心)
            return redirect(reverse('users:info'))


class AddressView(LoginRequiredMixin, View):

    def get(self, request):
        '''
        返回地址页面
        :param request:
        :return:
        '''
        # 1.获取该用户的所有没有删除的地址
        addresses = Address.objects.filter(user=request.user,
                                           is_deleted=False)

        address_model_list = []
        # 2.遍历地址: 获取每一个
        for address in addresses:
            # 3.这里格式, 把地址信息整理为dict
            address_dict = {
                    "id": address.id,
                    "title": address.title,
                    "receiver": address.receiver,
                    "province": address.province.name,
                    "city": address.city.name,
                    "district": address.district.name,
                    "place": address.place,
                    "mobile": address.mobile,
                    "tel": address.tel,
                    "email": address.email
            }

            # 4.创建一个list, 把地址信息添加到list中, 其中默认地址第一个
            default_address = request.user.default_address
            if default_address.id == address.id:
                address_model_list.insert(0, address_dict)
            else:
                address_model_list.append(address_dict)

        # 5.拼接参数
        context = {
                'default_address_id': request.user.default_address_id,
                'addresses': address_model_list
        }

        # 6.返回
        return render(request, 'user_center_site.html', context)


# Address.objects.filter()
# Address.objects.all()


class CreateAddressView(LoginRequiredJsonMixin, View):

    def post(self, request):
        '''
        接收数据, 保存到mysql, 返回
        :param request:
        :return:
        '''
        # 1.判断保存的地址个数是否大于20
        # count = request.user.addresses.count()

        # count = request.user.addresses.filter(is_deleted=False).count()
        count = request.user.addresses.model.objects.filter(is_deleted=False).count()
        if count >= 20:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR,
                                      'errmsg': '地址个数超过'})

        # 2.接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 3.检验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号格式不正确')

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')

        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 4.保存参数mysql
        try:
            address = Address.objects.create(
                user=request.user,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                title=receiver,
                receiver=receiver,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )

            # 5.判断是否有默认地址, 如果没有增加
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            logger.error(e)

            return http.JsonResponse({'code': RETCODE.DBERR,
                                      'errmsg': '数据库保存错误'})

        # 6.组织参数
        address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
        }

        # 7.返回json
        return http.JsonResponse({'code': RETCODE.OK,
                                  'errmsg': 'ok',
                                  'address': address_dict})

class UpdateDestroyAddressView(LoginRequiredJsonMixin, View):

    def put(self, request, address_id):
        '''
        修改当前id对应的地址信息, 保存到mysql
        :param request:
        :param addres_id:
        :return:
        '''
        # 1.接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 2.校验
        # 3.检验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号格式不正确')

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')

        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 3.获取id对应的地址, 然后更新
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                title=receiver,
                receiver=receiver,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)

            return http.JsonResponse({'code': RETCODE.DBERR,
                                      'errmsg': '数据库保存错误'})

        address = Address.objects.get(id=address_id)
        # 6.组织参数
        address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
        }

        # 7.返回json
        return http.JsonResponse({'code': RETCODE.OK,
                                  'errmsg': 'ok',
                                  'address': address_dict})

    def delete(self, request, address_id):
        '''
        根据id逻辑删除对应的地址
        :param request:
        :param address_id:
        :return:
        '''
        # 1.根据id获取对应的地址
        try:
            address = Address.objects.get(id=address_id)

            # 2.调用地址的is_deleted字段, 修改, 形成逻辑删除
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)

            return http.JsonResponse({'code': RETCODE.DBERR,
                                      'errmsg': '数据库保存错误'})

        # 3.返回
        return http.JsonResponse({'code': RETCODE.OK,
                                  'errmsg': 'ok'})


class DefaultAddressView(LoginRequiredJsonMixin, View):

    def put(self, request, address_id):
        '''
        根据id修改当前id对应的地址为默认地址
        :param request:
        :param address_id:
        :return:
        '''
        # 1.根据id获取对应的地址
        try:
            address = Address.objects.get(id=address_id)

            # 2.把默认地址换为获取的地址
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)

            return http.JsonResponse({'code': RETCODE.DBERR,
                                      'errmsg': '数据库保存错误'})

        # 3.返回
        return http.JsonResponse({'code': RETCODE.OK,
                                  'errmsg': 'ok'})


class UpdateTitleAddressView(LoginRequiredJsonMixin, View):

    def put(self, request, address_id):
        '''
        根据id修改对应地址的标题
        :param request:
        :param address_id:
        :return:
        '''
        # 0. 接收参数:
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        # 1.根据id获取对应的地址
        try:
            address = Address.objects.get(id=address_id)

            # 2.把默认地址换为获取的地址
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)

            return http.JsonResponse({'code': RETCODE.DBERR,
                                      'errmsg': '数据库保存错误'})

        # 3.返回
        return http.JsonResponse({'code': RETCODE.OK,
                                  'errmsg': 'ok'})


class ChangePasswordView(LoginRequiredMixin, View):

    def get(self, request):
        '''
        返回修改密码页面
        :param request:
        :return:
        '''
        return render(request, 'user_center_pass.html')

    def post(self, request):
        '''
        检验老密码, 增加新密码
        :param request:
        :return:
        '''
        # 1.接收参数(3个)
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        new_password2 = request.POST.get('new_password2')

        # 2.校验(整体检验 + 检验老密码 + 格式检验)
        if not all([old_password, new_password, new_password2]):
            return http.HttpResponseForbidden("缺少必传参数")

        # 检验老密码
        try:
            result = request.user.check_password(old_password)
            if not result:
                raise Exception()
        except Exception as e:
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码不对'})

        # 格式检验
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', new_password):
            return http.HttpResponseForbidden("新密码格式不对")

        if new_password != new_password2:
            return http.HttpResponseForbidden("两次输入密码不一致")

        # 3.更新密码(mysql)
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            logger.error(e)

            return render(request, 'user_center_pass.html', {'change_pwd_errmsg': '修改密码错误'})

        # 4.清除状态(session + cookie)
        logout(request)

        response = redirect(reverse('users:login'))

        response.delete_cookie('username')

        # 5.返回(重定向到登录页面)
        return response
