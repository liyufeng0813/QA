import hashlib
import random
import string

from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone


class MyUserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('用户必须填写邮箱！')
        if not username:
            raise ValueError('用户必须填写用户名！')

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            date_joined=timezone.now(),
            last_login=timezone.now(),
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(username, email, password=password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class Member(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name='邮箱', max_length=255, unique=True)
    username = models.CharField(verbose_name='用户名', max_length=16, unique=True)
    weibo = models.CharField(verbose_name='新浪微博', max_length=255, blank=True, null=True)
    blog = models.CharField(verbose_name='个人网站', max_length=255, blank=True, null=True)
    location = models.CharField(verbose_name='城市', max_length=50, blank=True, null=True)
    profile = models.CharField(verbose_name='个人简介', max_length=255, blank=True, null=True)
    avatar = models.CharField(verbose_name='头像', max_length=255, blank=True, null=True)
    au = models.IntegerField(verbose_name='用户活跃度', default=0)
    last_ip = models.GenericIPAddressField(verbose_name='上次访问IP', default='0.0.0.0')
    email_verified = models.BooleanField(verbose_name='邮箱是否验证', default=False)
    date_joined = models.DateTimeField(verbose_name='用户注册时间', default=timezone.now)
    topic_num = models.IntegerField(verbose_name='帖子数', default=0)
    comment_num = models.IntegerField(verbose_name='评论数', default=0)
    is_active = models.BooleanField(default=True, verbose_name='是否活跃')
    is_admin = models.BooleanField(default=False, verbose_name='是否是管理员')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = MyUserManager()

    def __str__(self):
        return self.username

    def get_username(self):
        return self.username

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

    def calculate_au(self):
        self.au = self.topic_num * 5 + self.comment_num
        return self.au

    def is_email_verified(self):
        return self.email_verified

    def get_email(self):
        return self.email


class Follower(models.Model):
    user_a = models.ForeignKey(Member, related_name='user_a', verbose_name='偶像')
    user_b = models.ForeignKey(Member, related_name='user_b', verbose_name='粉丝')

    class Meta:
        unique_together = ('user_a', 'user_b')

    def __str__(self):
        return '{} following {}'.format(self.user_b, self.user_a)


class EmailVerified(models.Model):
    """邮箱验证"""
    user = models.OneToOneField(Member)
    token = models.CharField(verbose_name='邮箱验证口令', max_length=255, default=None)
    timestamp = models.DateTimeField(default=timezone.now, verbose_name='生成时间')

    def __str__(self):
        return '{}:{}'.format(self.user, self.token)

    def random_str(self):
        salt = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        return salt

    def generate_token(self):
        year = self.timestamp.year
        month = self.timestamp.month
        day = self.timestamp.day
        date = '{}-{}-{}'.format(year, month, day)
        token = hashlib.md5((self.random_str() + date).encode('utf-8')).hexdigest()
        return token


class FindPassword(models.Model):
    """找回密码"""
    user = models.OneToOneField(Member, verbose_name='用户')
    token = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '{}:{}'.format(self.user, self.token)

    def random_str(self):
        salt = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        return salt

    def generate_token(self):
        year = self.timestamp.year
        month = self.timestamp.month
        day = self.timestamp.day
        date = '{}-{}-{}'.format(year, month, day)
        token = hashlib.md5((self.random_str() + date).encode('utf-8')).hexdigest()
        return token
