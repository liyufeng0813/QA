import datetime

from django.shortcuts import render, redirect, Http404
from django.views.decorators.csrf import csrf_protect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.cache import cache
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.mail import send_mail
from django.contrib.auth import logout as auth_logout, authenticate, login as auth_login

from QA.settings import NUM_COMMENT_PAGE, NUM_TOPIC_PAGE, SITE_URL, FROM_EMAIL
from people.models import Member, Follower, EmailVerified as Email, FindPassword
from question.models import Topic, Comment
from people.forms import RegisterForm, LoginForm


@csrf_protect
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            new_user = Member.objects.create_user(username=data['username'],
                                                  email=data['email'],
                                                  password=data['password2'],)
            new_user.save()
            email_verified = Email(user=new_user)
            email_verified.token = email_verified.generate_token()
            email_verified.save()

            msg = "{} 你好：\r\n请点击链接验证你的邮箱：{}{}".format(
                new_user.username,
                SITE_URL,
                reverse('user:email_verified',kwargs={'uid': new_user.id, 'token': email_verified.token})
            )
            send_mail('欢迎加入', msg, FROM_EMAIL, [data['email']])
            messages.success(request, '注册成功，请去你的邮箱进行验证！')

            user = authenticate(email=data['email'], password=data['password2'])
            auth_login(request, user)
            go = reverse('question:index')
            is_auto_login = request.POST.get('auto', False)
            if not is_auto_login:
                request.session.set_expiry(0)
            else:
                time = datetime.timedelta(days=30)
                request.session.set_expiry(time)
            return redirect(go)
    else:
        form = RegisterForm()
    return render(request, 'people/register.html', {'form': form})


@csrf_protect
def login(request):
    if request.user.is_authenticated():
        redirect_url = request.GET.get('next', reverse('question:index'))
        return redirect(redirect_url)
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            username = data.get('username', '')
            if '@' in username:
                email = username
            else:
                user = Member.objects.get(username=username)
                email = user.email
            user = authenticate(email=email, password=data.get('password', ''))
            if user is not None:
                auth_login(request, user)
                go = reverse('question:index')
                is_auto_login = request.POST.get('auto', False)
                if not is_auto_login:
                    request.session.set_expiry(0)
                return redirect(go)
            else:
                messages.error(request, '密码不正确！')
                return render(request, 'people/login.html', locals())
    else:
        form = LoginForm()
    return render(request, 'people/login.html', {'form': form})


def logout(request):
    auth_logout(request)
    return redirect(reverse('question:index'))


def au_top(request):
    """用户榜"""
    au_list = cache.get('au_top_list')
    if not au_list:
        au_list = Member.objects.order_by('-au')[:20]
        cache.set('au_top_list', au_list, 60)

    user_count = cache.get('user_count')
    if not user_count:
        user_count = Member.objects.all().count()
        cache.set('user_count', user_count, 60)

    return render(request, 'people/au_top.html', locals())


def user(request, uid):
    try:
        user_from_id = Member.objects.get(pk=uid)
    except Member.DOesNotExist:
        raise Http404

    user_a = request.user
    if user_a.is_authenticated():
        try:
            follower = Follower.objects.filter(user_a=user_a, user_b=user_from_id).first()
        except Follower.DoesNotExist:
            follower = None     # 没有关注

        topic_list = Topic.objects.filter(author_id=uid).order_by('-created_on')[:NUM_TOPIC_PAGE]
        comment_list = Comment.objects.filter(author_id=uid).order_by('-created_on')[:NUM_COMMENT_PAGE]
        return render(request, 'people/user.html', locals())
    else:
        return redirect(reverse('question:index'))


def user_topics(request, uid):
    try:
        this_user = Member.objects.get(pk=uid)
    except Member.DoesNotExist:
        raise Http404

    topic_list = Topic.objects.filter(author_id=uid).order_by('-created_on')
    paginator = Paginator(topic_list, NUM_TOPIC_PAGE)
    page = request.GET.get('page', 1)
    try:
        topic_list = paginator.page(page)
    except PageNotAnInteger:
        topic_list = paginator.page(1)
    except EmptyPage:
        topic_list = paginator.page(paginator.num_pages)

    return render(request, 'people/user_topics.html', locals())


def user_comments(request, uid):
    try:
        this_user = Member.objects.get(pk=uid)
    except Member.DoesNotExist:
        raise Http404

    comment_list = Comment.objects.filter(author_id=uid).order_by('-created_on')
    paginator = Paginator(comment_list, NUM_COMMENT_PAGE)
    page = request.GET.get('page', 1)
    try:
        comment_list = paginator.page(page)
    except PageNotAnInteger:
        comment_list = paginator.page(1)
    except EmptyPage:
        comment_list = paginator.page(paginator.num_pages)

    return render(request, 'people/user_comments.html', locals())


@login_required
@csrf_protect
def send_verified_email(request):
    if not request.method == 'POST':
        return redirect(reverse('user:settings'))

    user = request.user
    if user.email_verified:
        messages.error(request, '你的邮箱已经验证过了！')
        return redirect(reverse('user:settings'))
    last_email = Email.objects.get(user=user)
    if (timezone.now() - last_email.timestamp).seconds < 120:
        messages.error(request, '两分钟内只能申请一次！')
    else:
        try:
            email = Email.objects.get(user=user)
            email.token = email.generate_token()
            email.timestamp = timezone.now()
            email.save()
        except Email.DoesNotExist:
            email = Email(user=user)
            email.token = email.generate_token()
            email.save()
        finally:
            msg = '{} 你好：\r\n欢迎你注册成为会员，请点击链接验证你的邮箱bb：{}{}'.format(
                user.username,
                SITE_URL,
                reverse('user:email_verified', kwargs={'uid': user.id, 'token': email.token})
            )
            send_mail('欢迎加入！', msg, FROM_EMAIL, [user.email])
            messages.success(request, '邮件已发送，请去邮箱验证！')
    return redirect(reverse('user:settings'))


def email_verified(request, uid, token):
    try:
        user = Member.objects.get(pk=uid)
        email = Email.objects.get(user=user)
    except (Member.DoesNotExist, Email.DoesNotExist):
        raise Http404
    else:
        if email.token == token:
            user.email_verified = True
            user.save()
            email.delete()
            messages.success(request, '邮箱验证成功！')
            if not request.user.is_authenticated():
                auth_login(request, user)
            return redirect(reverse('question:index'))
        else:
            raise Http404


def find_password(request):
    if not request.method == 'POST':
        return render(request, 'people/find_password.html')

    email = request.POST.get('email')
    user = None
    try:
        user = Member.objects.get(email=email)
    except Member.DoesNotExist:
        messages.error(request, '未找到用户！')

    if user:
        find_pass = FindPassword.objects.filter(user=user).first()
        if find_pass:
            if (timezone.now() - find_pass.timestamp).seconds < 60:
                messages.error(request, '一分钟内不可以重复找回密码！')
                return redirect(reverse('user:login'))
        else:
            find_pass = FindPassword(user=user)
            find_pass.timestamp = timezone.now()
            find_pass.token = find_pass.generate_token()
            find_pass.save()
        msg = '{} 你好：\r\n请点击链接重置密码 {}{}'.format(
            user.username,
            SITE_URL,
            reverse('user:first_reset_password', kwargs={'uid': user.id, 'token': find_pass.token})
        )
        send_mail('重置密码', msg, FROM_EMAIL, [email])
        messages.success(request, '密码找回邮件已发送！')
    return redirect(reverse('question:index'))


def first_reset_password(request, uid=None, token=None):
    try:
        user = Member.objects.get(pk=uid)
    except Member.DoesNotExist:
        raise Http404

    find_pass = FindPassword.objects.filter(user=user).first()
    if not find_pass:
        messages.error(request, '错误！')
        return redirect(reverse('user:find_pass'))
    now = timezone.now()
    timestamp = find_pass.timestamp
    if int(now.strftime('%Y%m%d')) - int(timestamp.strftime('%Y%m%d')) < 3:
        if find_pass.token == token:
            request.session['find_pass'] = uid
            return render(request, 'people/reset_password.html')
        else:
            raise Http404
    else:
        raise Http404


def reset_password(request):
    if request.method == 'GET':
        raise Http404

    password = request.POST.get('password')
    if len(password) < 6:
        messages.error(request, '密码长度不能小于6！')
        return render(request, 'people/reset_password.html')
    uid = request.session['find_pass']
    user = Member.objects.get(pk=uid)
    if user:
        user.set_password(password)
        user.save()
        FindPassword.objects.get(user=user).delete()
        del request.session['find_pass']
        messages.success(request, '密码重置成功，请登录！')
        return redirect(reverse('user:login'))
    raise Http404
