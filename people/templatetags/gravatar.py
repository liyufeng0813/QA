from urllib import parse
import hashlib

from django import template
from django.contrib.auth import get_user_model
from django.conf import settings

GRAVATAR_URL_PREFIX = getattr(settings, 'GRAVATAR_URL_PREFIX', 'http://www.gravatar.com/')
GRAVATAR_DEFAULT_IMAGE = getattr(settings, 'GRAVATAR_DEFAULT_IMAGE', '')
GRAVATAR_DEFAULT_RATING = getattr(settings, 'GRAVATAR_DEFAULT_RATING', 'g')
GRAVATAR_DEFAULT_SIZE = getattr(settings, 'GRAVATAR_DEFAULT_SIZE', 48)
QINIU_URL = getattr(settings, 'QINIU_URL')

User = get_user_model()
register = template.Library()


def get_user(user):
    if not isinstance(user, User):
        try:
            User.objects.get(username=user)
        except User.DoesNotExist:
            raise Exception('用户未注册！')
    return user.email


def get_gravatar_id(email):
    email = email.encode()
    return hashlib.md5(email).hexdigest()


@register.simple_tag
def gravatar(user, size=None):
    try:
        if isinstance(user, User):
            return gravatar_url_for_user(user, size)
        return gravatar_url_for_email(user, size)
    except ValueError:
        raise template.TemplateSyntaxError('语法错误！')


@register.simple_tag
def gravatar_url_for_user(user, size=None):
    if user.avatar and user.avatar != '':
        img = QINIU_URL + user.avatar
        return img
    else:
        email = get_user(user)
        return gravatar_url_for_email(email, size)


@register.simple_tag
def gravatar_url_for_email(email, size=None):
    gravatar_url = '{}avatar/{}'.format(GRAVATAR_URL_PREFIX, get_gravatar_id(email))
    parameters = [p for p in (('d', GRAVATAR_DEFAULT_IMAGE), ('s', size or GRAVATAR_DEFAULT_SIZE), ('r', GRAVATAR_DEFAULT_RATING)) if p[1]]

    if parameters:
        gravatar_url += '?' + parse.urlencode(parameters, doseq=True)
    return gravatar_url
