from django import http
from django.contrib.auth.decorators import login_required

# 检验用户是否登录的一个Mixin扩展类:
from meiduo_mall.utils.response_code import RETCODE


class LoginRequiredMixin(object):

    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super().as_view(*args, **kwargs)
        return login_required(view)



# 判断用户是否登录, 如果登录, 正常调用, 如果没有登录, 返回json
def login_required_json(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        else:
            return http.JsonResponse({'code':RETCODE.SESSIONERR,
                                      'errmsg':'用户未登录'})
    return wrapper




class LoginRequiredJsonMixin(object):

    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super().as_view(*args, **kwargs)
        return login_required_json(view)