import datetime
import re

from django.shortcuts import render, redirect
from django.http import Http404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib import messages
from question.models import *
from question.forms import *
from people.models import Member

NUM_TOPICS_PAGE = settings.NUM_TOPIC_PAGE
NUM_COMMENT_PAGE = settings.NUM_COMMENT_PAGE


@require_http_methods(['GET', 'POST'])
def index(request):
    # 获取主题列表
    topic_list = Topic.objects.all().order_by('-created_on')[:NUM_TOPICS_PAGE]
    nodes = cache.get('index_nodes')

    # 节点及类别
    if not nodes:
        nodes = []
        category_list = Category.objects.all()
        for category in category_list:
            node = {}
            category_nodes = Node.objects.filter(category=category)
            node['category_name'] = category.name
            node['category_nodes'] = category_nodes
            nodes.append(node)
        cache.set('index_nodes', nodes, 60)     # 缓存设置60秒

    # 今日热议
    hot_topics = cache.get('index_hot_topics')
    if not hot_topics:
        now = timezone.now()
        start_time = now - datetime.timedelta(hours=23, minutes=59, seconds=59)
        hot_comments = Comment.objects.filter(created_on__gt=start_time).values('topic')\
                           .annotate(count=Count('topic')).order_by('-count')[:NUM_COMMENT_PAGE]
        hot_topics = []
        for comment in hot_comments:
            topic = Topic.objects.get(id=comment['topic'])
            hot_topics.append(topic)
        cache.set('index_hot_topic', hot_topics, 60)

    return render(request, 'question/index.html', {'topic_list': topic_list,
                                                   'nodes': nodes,
                                                   'hot_topics': hot_topics})


@require_http_methods(['GET', 'POST'])
def recent(request):
    topic_list = Topic.objects.all().order_by('-created_on')
    paginator = Paginator(topic_list, NUM_TOPICS_PAGE)
    page = request.GET.get('page', 1)

    try:
        topic_list = paginator.page(page)
    except PageNotAnInteger:
        topic_list = paginator.page(1)
    except EmptyPage:
        topic_list = paginator.page(paginator.num_pages)

    return render(request, 'question/recent.html', {'topic_list': topic_list})


@require_http_methods(['GET', 'POST'])
def node(request, node_slug):
    try:
        node = Node.objects.get(slug=node_slug)
    except Node.DoesNotExist:
        raise Http404
    topic_list = Topic.objects.filter(node=node).order_by('-created_on')
    paginator = Paginator(topic_list, NUM_TOPICS_PAGE)
    page = request.GET.get('page', 1)

    try:
        topic_list = paginator.page(page)
    except PageNotAnInteger:
        topic_list = paginator.page(1)
    except EmptyPage:
        topic_list = paginator.page(paginator.num_pages)

    return render(request, 'question/node.html', {'topic_list': topic_list, 'node': node})


@require_http_methods(['GET', 'POST'])
def topic(request, topic_id):
    try:
        topic = Topic.objects.get(id=topic_id)
    except Topic.DoesNotExist:
        raise Http404

    topic.num_views += 1
    topic.save()

    faved_num = FavoritedTopic.objects.filter(topic=topic).count()
    if request.user.is_authenticated():
        try:
            faved_topic = FavoritedTopic.objects.filter(user=request.user, topic=topic).first()
        except (Member.DoesNotExist, FavoritedTopic.DoesNotExist):
            faved_topic = None

    comment_list = Comment.objects.filter(topic=topic).order_by('created_on')
    paginator = Paginator(comment_list, NUM_COMMENT_PAGE)
    page = request.GET.get('page', 1)

    try:
        comment_list = paginator.page(page)
    except PageNotAnInteger:
        comment_list = paginator.page(1)
    except EmptyPage:
        comment_list = paginator.page(paginator.num_pages)

    reply_form = ReplyForm()

    return render(request, 'question/topic.html', locals())


@login_required
@require_http_methods(['GET', 'POST'])
def reply(request, topic_id):
    """回复"""
    try:
        topic = Topic.objects.get(id=topic_id)
        comment_list = Comment.objects.filter(topic=topic).order_by('created_on')
        paginator = Paginator(comment_list, NUM_COMMENT_PAGE)
        page = request.GET.get('page', 1)

        try:
            comment_list = paginator.page(page)
        except PageNotAnInteger:
            comment_list = paginator.page(1)
        except EmptyPage:
            comment_list = paginator.page(paginator.num_pages)
    except Topic.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            last_comment = Comment.objects.filter(author=request.user).order_by('-created_on').first()
            if last_comment and last_comment.content == form.cleaned_data.get('content', '') and (timezone.now() - last_comment.created_on).seconds < 5:
                messages.error(request, '不可以提交两次重复的回复！')
            else:
                comment = form.save(commit=False)
                request.user.comment_num += 1
                request.user.calculate_au()
                request.user.save()
                comment.author = request.user

                try:
                    topic = Topic.objects.get(id=topic_id)
                except Topic.DoesNotExist:
                    raise Http404

                comment.topic = topic
                comment.save()

                team_name_pattern = re.compile('(?<=@)([0-9a-zA-Z_.]+)', re.UNICODE)    # 正则获取@后面的字符串
                at_name_list = set(re.findall(team_name_pattern, comment.content))      # 获取@的用户
                if at_name_list:
                    for at_name in at_name_list:
                        if at_name != comment.author.username and at_name != comment.topic.author.username:
                            try:
                                at_user = Member.objects.get(username=at_name)
                                if at_user:
                                    notice = Notice(from_user=comment.author, to_user=at_user, topic=comment.topic, content=comment.content)
                                    notice.save()
                            except Notice.DoesNotExist:
                                pass

                topic.num_comments += 1
                topic.updated_on = timezone.now()
                topic.last_reply = request.user
                topic.save()
                return redirect(reverse('question:topic', kwargs={'topic_id': topic_id}))
    else:
        form = ReplyForm()
    return render(request, 'question/topic.html', {'node': node, 'topic': topic, 'form': form, 'comment_list': comment_list, 'paginator': paginator})


@login_required
@require_http_methods(['GET', 'POST'])
def new(request, node_slug):
    """发布新主题"""
    try:
        node = Node.objects.get(slug=node_slug)
    except Node.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            last_topic = Topic.objects.filter(author=request.user).order_by('-created_on').first()
            if last_topic and last_topic.title == form.cleaned_data.get('title', '') and (timezone.now() - last_topic.created_on).seconds < 5:
                messages.error(request, '不可重复提交相同的主题！')
                return redirect(reverse('question:topic', kwargs={'topic_id': last_topic.id}))
            else:
                topic = form.save(commit=False)
                topic.node = node
                request.user.topic_num += 1
                request.user.calculate_au()
                request.user.save()
                topic.author = request.user
                topic.last_reply = request.user
                topic.updated_on = timezone.now()
                topic.save()
                node.num_topics += 1
                node.save()
                return redirect(reverse('question:topic', kwargs={'topic_id': topic.id}))
    else:
        form = TopicForm()
    return render(request, 'question/new.html', {'node': node, 'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def edit(request, topic_id):
    try:
        topic = Topic.objects.get(id=topic_id)
        if topic.author != request.user:
            raise Http404
    except Topic.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic.title = form.cleaned_data.get('title', '')
            topic.content = form.cleaned_data.get('content', '')
            topic.updated_on = timezone.now()
            topic.save()
        return redirect(reverse('question:topic', kwargs={'topic_id': topic_id}))
    else:
        form = TopicForm(instance=topic)
    return render(request, 'question/edit.html', {'form': form, 'topic': topic})


@login_required
def notice(request):
    context = {}
    if request.method == 'GET':
        notices = Notice.objects.filter(to_user=request.user, is_deleted=False).order_by('-time')
        context['notices'] = notices
        return render(request, 'question/notice.html', context)


@login_required
def notice_delete(request, notice_id):
    if request.method == 'GET':
        try:
            notice = Notice.objects.get(id=notice_id)
        except Notice.DoesNotExist:
            raise Http404
        notice.is_deleted = True
        notice.save()
    return redirect(reverse('question:notice'))


@login_required
def fav_topic_list(request):
    """查看所有主题"""
    faved_topic = FavoritedTopic.objects.filter(user=request.user).all()
    return render(request, 'question/fav_topic.html', locals())


@login_required
def fav_topic(request, topic_id):
    """关注新的主题"""
    if not request.method == 'POST':
        return redirect(reverse('question:index'))

    try:
        topic = Topic.objects.get(pk=topic_id)
        if FavoritedTopic.objects.filter(user=request.user, topic=topic).first():
            messages.error(request, '该主题已经关注！')
        FavoritedTopic.objects.create(user=request.user, topic=topic)
    except Topic.DoesNotExist:
        messages.error(request, '主题不存在！')
        return redirect(reverse('question:index'))
    return redirect(reverse('question:topic', kwargs={'topic_id': topic_id}))


@login_required
def unfav_topic(request, topic_id):
    """取消关注主题"""
    if not request.method == 'POST':
        return redirect(reverse('question:index'))

    try:
        topic = Topic.objects.get(pk=topic_id)
        faved_topic = FavoritedTopic.objects.filter(user=request.user, topic=topic)
        faved_topic.delete()
    except Topic.DoesNotExist:
        messages.error(request, '主题不存在！')
        return redirect(reverse('question:index'))
    return redirect(reverse('question:topic', kwargs={'topic_id': topic_id}))
