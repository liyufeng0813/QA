from django.db import models


class Category(models.Model):
    """站点类别"""
    name = models.CharField(max_length=100, verbose_name='类别')

    def __str__(self):
        return self.name


class CoolSite(models.Model):
    """站点详情"""
    category = models.ForeignKey(Category, verbose_name='所属类别')
    url = models.URLField(verbose_name='站点地址')
    name = models.CharField(max_length=100, verbose_name='站点名称')
    description = models.TextField(blank=True, null=True, verbose_name='站点介绍')
    created_on = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return self.name
