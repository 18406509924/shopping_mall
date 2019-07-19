from itsdangerous import TimedJSONWebSignatureSerializer
from django.conf import settings
from itsdangerous import BadData
import logging
logger = logging.getLogger('django')


def generate_access_token(openid):
    '''
    把openid加密为access_token
    :param openid:
    :return:
    '''


    # TimedJSONWebSignatureSerializer('秘钥', 有效期)
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=3600)

    dict = {
        'openid':openid
    }

    token_bytes = serializer.dumps(dict)  # bytes

    return token_bytes.decode() # str



def check_access_token(access_token):
    '''
    把access_token解密为openid
    :param access_token:
    :return:
    '''
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=3600)

    try:
        data = serializer.loads(access_token)
    except BadData as e:
        logger.error(e)

        return None
    else:
        return data.get('openid')









# bytes ====> decode() 解码 ====> str
# str   ====> encode() 编码 ====> bytes

