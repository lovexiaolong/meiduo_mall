import random

from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View


from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection

from meiduo_mall.libs.yuntongxun.ccp_sms import CCP
from meiduo_mall.utils.response_code import RETCODE
import logging

from verifications import const

logger = logging.getLogger('django')


class SMSCodeView(View):
    def get(self,request,mobile):
        """

        :param request:
        :param mobile:
        :return:
        """
        #链接redis
        redis_conn = get_redis_connection('verify_code')

        send_flag = redis_conn.get('send_flag_%s' % mobile)

        if send_flag:
            #如果进入这里，意味着60s以内第二次来访问
            return http.JsonResponse({'code':RETCODE.THROTTLINGERR,'errmsg':'发送短信验证码过于频繁'})
        #1.接收参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        #2.校验
        if not all([image_code_client,uuid]):
            return http.JsonResponse({'code':RETCODE.NECESSARYPARAMERR,'errmsg':'缺少必传参数'})

        #2.链接redis
        redis_conn = get_redis_connection('verify_code')

        #2.2 取出图形验证码 判断是否存在（过期）
        image_code_server = redis_conn.get('img_%s' % uuid)

        if image_code_server is None:

            return http.JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'图形验证码失效'})

        #2.3 删除图形验证码
        try:
            redis_conn.delete('img_%s' % uuid)
        except Exception as e:
            logger.error(e)

        #2.4 比较（前端和dedis中）图形验证码
        if image_code_client.lower() != image_code_server.decode().lower():
            return http.JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'输入图形验证码有误'})

        #3.生成随机验证码
        sms_code = '%06d' % random.randint(0,999999)
        logger.info(sms_code)

        #创建管道
        pl = redis_conn.pipeline()

        #4.保存到redis中
        pl.setex('sms_code_%s' % mobile,const.SMS_CODE_REDIS_EXPIRES,sms_code)

        pl.setex('send_flag_%s' % mobile,60,1)

        #执行
        pl.execute()

        #5.发送短信验证码（调用的云通讯的接口）
        # CCP().send_template_sms(mobile,[sms_code,5],1)
        # from celery_tasks.sms.tasks import send_sms_code
        # send_sms_code.delay(mobile,sms_code)


        #6.返回（code + errmsg）
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok'})



class ImageCodeView(View):

    def get(self,request,uuid):
        """

        :param request:
        :param uuid:
        :return:
        """
        #1.生成图形验证码：text + image
        text,image = captcha.generate_captcha()
        #2.获取redis的链接对象
        redis_conn = get_redis_connection('verify_code')
        #3.保存验证码
        # 图形验证码有效期，单位：秒
        # IMAGE_CODE_REDIS_EXPIRES = 300
        redis_conn.setex('img_%s' % uuid,const.IMAGE_CODE_REDIS_EXPIRES,text)
        #4.返回（图片）
        return http.HttpResponse(image,content_type='image/jpg')
