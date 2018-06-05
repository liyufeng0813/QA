from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.db import IntegrityError
from people.models import Member, Follower


@csrf_protect
@login_required
def follow(request, uid):
    if not request.method == 'POST':
        return redirect(reverse('question:index'))

    user_a = request.user
    try:
        user_b = Member.objects.get(pk=uid)
    except Member.DoesNotExist:
        messages.error(request, '该用户不存在！')
        return redirect(reverse('question:index'))
    if user_a.id == uid:
        messages.error(request, '不能关注自己！')
        return redirect(reverse('question:index'))

    try:
        Follower.objects.create(user_a=user_a, user_b=user_b)
        messages.success(request, '关注成功！')
        return redirect(reverse('user:user', kwargs={'uid': uid}))
    except IntegrityError:
        messages.error(request, '你已经关注了该用户！')
        return redirect(reverse('question:index'))


@csrf_protect
@login_required
def unfollow(request, uid):
    if not request.method == 'POST':
        return redirect(reverse('question:index'))

    user_a = request.user
    try:
        user_b = Member.objects.get(pk=uid)
        follower = Follower.objects.filter(user_a=user_a, user_b=user_b)
    except (Member.DoesNotExist, Follower.DoesNotExist):
        messages.error(request, '粉丝关系或该用户不存在')
        return redirect(reverse('question:index'))
    else:
        follower.delete()
        messages.success(request, '取消关注成功！')
        return redirect(reverse('user:user', kwargs={'uid': user_b.id}))


@login_required
def following(request):
    following_list = Follower.objects.filter(user_a=request.user).all()
    return render(request, 'people/following.html', locals())
