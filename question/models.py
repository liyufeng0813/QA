from django.db import models
from django.db.models.signals import post_save
from people.models import Member


class Category(models.Model):
    """类别"""
    name = models.CharField(max_length=100, verbose_name='类别')

    def __str__(self):
        return self.name


class Node(models.Model):
    """节点"""
    name = models.CharField(max_length=100, verbose_name='节点')
    slug = models.SlugField(max_length=100, verbose_name='url标识符')
    created_on = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_on = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name='更新时间')
    num_topics = models.SmallIntegerField(default=0, verbose_name='主题数')
    category = models.ForeignKey(Category, verbose_name='所属类别')

    def __str__(self):
        return self.name


class Topic(models.Model):
    """主题"""
    title = models.CharField(max_length=100, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    node = models.ForeignKey(Node, verbose_name='所属节点')
    author = models.ForeignKey(Member, verbose_name='作者')
    num_views = models.IntegerField(default=0, verbose_name='浏览量')
    num_comments = models.IntegerField(default=0, verbose_name='评论数')
    last_reply = models.ForeignKey(Member, related_name='+', verbose_name='最后回复者', null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, verbose_name='发表时间')
    updated_on = models.DateTimeField(blank=True, null=True, verbose_name='更新时间')

    def __str__(self):
        return self.title


class Comment(models.Model):
    """评论"""
    content = models.TextField(verbose_name='内容')
    author = models.ForeignKey(Member, verbose_name='作者')
    topic = models.ForeignKey(Topic, verbose_name='所属主题')
    created_on = models.DateTimeField(auto_now_add=True, verbose_name='评论时间')

    def __str__(self):
        return self.content


class Notice(models.Model):
    """通知"""
    from_user = models.ForeignKey(Member, related_name='+', verbose_name='来自用户')
    to_user = models.ForeignKey(Member, related_name='+', verbose_name='接收用户')
    topic = models.ForeignKey(Topic, null=True, verbose_name='所属主题')
    content = models.TextField(verbose_name='内容')
    time = models.DateTimeField(auto_now_add=True, verbose_name='通知时间')
    is_readed = models.BooleanField(default=False, verbose_name='是否以读')
    is_deleted = models.BooleanField(default=False, verbose_name='是否删除')

    def __str__(self):
        return self.content


class FavoritedTopic(models.Model):
    """记录用户最爱的主题"""
    user = models.ForeignKey(Member, verbose_name='用户')
    topic = models.ForeignKey(Topic, verbose_name='主题')

    def __str__(self):
        return str(self.id)


def create_notice(sender, **kwargs):
    """
    如果评论者是这个主题的作者，就不通知这个作者。
    也就是，自己给自己的主题评论，就不通知自己。
    """
    comment = kwargs.get('instance', None)
    if comment and comment.author != comment.topic.author:
        Notice.objects.create(
            from_user=comment.author,
            to_user=comment.topic.author,
            topic=comment.topic,
            content=comment.content,
        )


post_save.connect(create_notice, sender=Comment)
