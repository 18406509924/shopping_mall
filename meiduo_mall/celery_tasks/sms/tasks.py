from celery_tasks.main import celery_apps
from celery_tasks.yuntongxun.ccp_sms import CCP


@celery_apps.task(bind=True, name='send_sms_code', retry_backoff=3)
def send_sms_code(self, mobile, sms_code):
    # try:
    result = CCP().send_template_sms(mobile, [sms_code, 5], 1)
    # except Exception as e:
    #     raise self.retry(exec=e, max_retries=3)
    #
    # if result != 0:
    #     raise self.retry(exec=Exception('发送彻底失败'), max_retries=3)

    print(result)

    return result