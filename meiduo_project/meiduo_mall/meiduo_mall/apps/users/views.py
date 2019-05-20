import re


from django.contrib.auth.views import login
from django.db import DatabaseError
from django.http import HttpResponse
from django import http
from django.shortcuts import render, redirect
from django.urls import reverse
from django_redis import get_redis_connection

from meiduo_mall.utils.response_code import RETCODE
from .models import User

# Create your views here.
from django.views import View


class MobileCountView(View):

    def get(self,request,mobile):

        count = User.objects.filter(mobile=mobile).count()

        return HttpResponse({'code':RETCODE.OK,
                             'errmsg':'ok',
                             'count':count})





class UsernameCountView(View):

    def get(self,request,username):


        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code':RETCODE.OK,
                             'errmsg':'ok',
                             'count':count})


class RegisterView(View):

    def get(self,request):
        """
        定义一个接口，返回注册页面
        :param request:
        :return:
        """

        return render(request,'register.html')


    def post(self, request):
        """
        实现用户注册
        :param request: 请求对象
        :return: 注册结果
        """
        #1.接收参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')

        # TODD:sms_code
        sms_code_client = request.POST.get('sms_code')
        allow = request.POST.get('allow')

        #2.校验参数
        # 判断参数是否齐全
        if not all([username, password, password2, mobile, allow]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        # 判断两次密码是否一致
        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')
        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')
        # 获取 redis 链接对象
        redis_conn = get_redis_connection('verify_code')

        # 从 redis 中获取保存的 sms_code
        sms_code_server = redis_conn.get('sms_code_%s' % mobile)

        # 判断 sms_code_server 是否存在
        if sms_code_server is None:
            # 不存在直接返回, 说明服务器的过期了, 超时
            return render(request, 'register.html', {'sms_code_errmsg': '无效的短信验证码'})

        # 如果 sms_code_server 存在, 则对比两者:
        if sms_code_client != sms_code_server.decode():
            # 对比失败, 说明短信验证码有问题, 直接返回:
            return render(request, 'register.html', {'sms_code_errmsg': '输入短信验证码有误'})
        # 判断是否勾选用户协议
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')


        #3.保存到数据库
            # 保存注册数据
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg': '注册失败'})




        #5.状态保持
        login(request,user)

        # # 响应注册结果
        # return http.HttpResponse('保存成功,跳转还没有做到首页')
        # 响应注册结果
        return redirect(reverse('contents:index'))


