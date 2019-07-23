from django import http
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render

# Create your views here.
from django.utils import timezone
from django.utils.datetime_safe import datetime
from django.views import View

from goods.models import GoodsCategory, SKU, GoodsVisitCount
from goods.utils import get_categories, get_breadcrumb, get_goods_and_spec
from meiduo_mall.utils.response_code import RETCODE


class ListView(View):

    def get(self, request, category_id, page_num):
        '''
        接收参数, 获取商品列表页数据, 返回
        :param request:
        :param category_id: 该类别商品id
        :param page_num:
        :return:
        '''
        # 1.根据category_id获取对应的类别
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return http.HttpResponseForbidden('从数据库取数据出错')

        # 2.获取商品分类
        categories = get_categories()

        # 3.把类别传给工具类, 获取对赢的面包屑数据
        breadcrumb = get_breadcrumb(category)

        # 6. 排序:
        # 6.1 获取前端传递的排序方式
        sort = request.GET.get('sort', 'default')

        # 6.2 判断, 是哪一种排序方式
        if sort == 'price':
            sortkind = 'price'
        elif sort == 'hot':
            # 高到低:
            sortkind = '-sales'
        else:
            sort = 'default'
            sortkind = 'create_time'

        # 6.3 获取商品数据, 顺便按照排序方式排序
        skus = SKU.objects.filter(category=category, is_launched=True).order_by(sortkind)

        # 7. 分液效果:
        # 7.1  根据Paginator创建一个对象(总的数据, 指定每页的个数)
        paginator = Paginator(skus, 5)

        # 7.2  使用对象的page()函数, 获取对应页吗的商品数据
        try:
            page_skus = paginator.page(page_num)
        except EmptyPage:
            return http.HttpResponseForbidden('获取的是空页面')

        # 7.3  获取总页数
        total_page = paginator.num_pages

        # 4.拼接参数
        context = {
                'categories': categories,
                'breadcrumb': breadcrumb,
                'total_page': total_page,
                'page_skus': page_skus,
                'page_num': page_num,
                'sort': sort,
                'category': category
        }

        # 5.返回
        return render(request, 'list.html', context)


class HotGoodsView(View):

    def get(self, request, category_id):
        '''
        返回列表页中热销数据(2个)
        :param request:
        :param category_id:
        :return:
        '''
        # 1.从 mysql的SKU表中获取对应的商品(排序, 切片,保留2个)
        skus = SKU.objects.filter(category_id=category_id,
                                  is_launched=True).order_by('-sales')[:2]

        list = []

        # 2.遍历两个商品, 获取每一个
        for sku in skus:
            # 3.把商品属性品味dict 把dict 放到 list
            list.append({
                    'id': sku.id,
                    'default_image_url': sku.default_image_url,
                    'name': sku.name,
                    'price': sku.price
            })

        # 4.返回
        return http.JsonResponse({'code': RETCODE.OK,
                                  'errmsg': 'ok',
                                  'hot_skus': list})


class DetailView(View):

    def get(self, request, sku_id):
        '''
        根据sku_id 获取对应的商品, 整理格式, 返回
        :param request:
        :param sku_id:
        :return:
        '''
        # 1.根据sku_id 获取对应的商品
        data = get_goods_and_spec(sku_id, request)

        # 3.获取商品分类
        categories = get_categories()

        breadcrumb = get_breadcrumb(data.get('goods').category3)

        # 4.整理格式
        context = {
                'categories': categories,
                'sku': data.get('sku'),
                'goods': data.get('goods'),
                'specs': data.get('goods_specs'),
                'breadcrumb': breadcrumb
        }

        # 5.返回
        return render(request, 'detail.html', context)


class GoodsVisitView(View):

    def post(self, request, category_id):
        '''
        记录用户访问次数
        :param request:
        :param category_id:
        :return:
        '''
        # 1.根据category_id 获取类别对象
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return http.HttpResponseForbidden('参数不能为空')

        # 获取今天的日期:
        # (日期+时间)
        time = timezone.localtime()

        today_str = '%d-%02d-%02d' % (time.year, time.month, time.day)

        today_time = datetime.strptime(today_str, '%Y-%m-%d')

        # 2.现根据今天的日期, 从数据库中获取对应的记录
        try:
            count_data = category.goodsvisitcount_set.get(date=today_time)

        except GoodsVisitCount.DoesNotExist:
            # 5.如果不存在, 创建新的
            count_data = GoodsVisitCount()
        try:
            # 3.如果获取到了记录, 更新(类别, count+1)
            count_data.category = category
            count_data.count += 1
            # 4.保存
            count_data.save()
        except Exception as e:
            return http.HttpResponseForbidden('更新数据库出错')

        # 6.返回
        return http.JsonResponse({'code': RETCODE.OK,
                                  'errmsg': 'ok'})
