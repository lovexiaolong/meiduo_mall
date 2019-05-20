from celery_tasks.main import celery_app
from celery_tasks.yuntongxun.ccp_sms import CCP
import logging
logger=logging.getLogger('django')

@celery_app.task(bind=True, name='send_sms_code', retry_backoff=3)
def send_sms_code(self, mobile, sms_code):
    """
    发送短信
    :return:
    """
    try:
        # 调用 CCP() 发送短信, 并传递相关参数:
        result = CCP().send_template_sms(mobile, [sms_code, 5], 1)

    except Exception as e:

    #     # 如果发送过程出错, 打印错误日志
        logger.error(e)
    #
        # 有异常自动重试三次
        raise self.retry(exc=e, max_retries=3)

        # 如果发送成功, rend_ret 为 0:
    if result != 0:
        # 有异常自动重试三次
        raise self.retry(exc=Exception('发送短信失败'), max_retries=3)

    return result
