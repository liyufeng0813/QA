import base64
import json

from django.shortcuts import render, redirect, Http404
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from QA import settings
from people.forms import ProfileForm, PasswordChangeForm
from people.models import Member

from qiniu import Auth
import qiniu.config
from qiniu import BucketManager

SITE_URL = getattr(settings, 'SITE_URL')
AK = settings.AK
SK = settings.SK


@csrf_protect
@login_required
def profile(request):
    """修改个人信息"""
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save(commit=True)
            messages.success(request, '设置成功！')
            return render(request, 'people/settings.html', {'form': form})
    else:
        form = ProfileForm(instance=user)
    q = Auth(AK, SK)
    buket_name = 'avatar'
    key_name = 'avatar/' + user.username
    callbackBody = 'filename=$(fname)&filesize=$(fsize)'
    callbackUrl = SITE_URL + reverse('user:upload_headimage')
    mimeLimit = 'image/jpeg; image/png'
    policy = {
        'callbackUrl': callbackUrl,
        'callbackBody': callbackBody,
        'mimeLimit': mimeLimit,
    }
    uptoken = q.upload_token(buket_name, key_name, 3600, policy)
    return render(request, 'people/settings.html', {'form': form, 'user': user, 'uptoken': uptoken})


@csrf_protect
@login_required
def upload_headimage(request):
    """上传头像"""
    print(request, ' 11111111')
    if request.method == 'POST':
        print(request, '1212111112')
        try:
            retstr = request.GET.get('upload_ret')
            print(retstr, '=-=-==-=')
            retstr = retstr.encode('utf-8')
            dec = base64.urlsafe_b64decode(retstr)
            ret = json.loads(dec)
            if ret and ret['key']:
                request.user.avatar = ret['key']
                request.user.save()
            else:
                raise Http404
            messages.success(request, '头像上传成功！')
        except:
            messages.error(request, '头像上传失败！')
    return redirect(reverse('user:settings'))


@csrf_protect
@login_required
def delete_headimage(request):
    """删除头像"""
    user = request.user
    if not user.avatar:
        messages.error(request, '你还没有上传头像！')
    else:
        q = Auth(AK, SK)
        buket = BucketManager(q)
        buket_name = 'avatar'
        ret, info = buket.delete(buket_name, user.avatar)
        if ret:
            user.avatar = ''
            user.save()
            messages.success(request, '头像删除成功！')
        else:
            messages.error(request, '头像删除失败！')
    return redirect(reverse('user:settings'))


@csrf_protect
@login_required
def password(request):
    """重置密码"""
    user = request.user
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if user.check_password(data.get('old_password', '')):
                user.set_password(data['password2'])
                user.save()
                messages.success(request, '密码设置成功，请重新登录！')
                auth_logout(request)
                return redirect(reverse('user:login'))
            else:
                messages.error(request, '当前密码输入错误！')
                return render(request, 'people/password.html', {'form': form})
    else:
        form = PasswordChangeForm()
    return render(request, 'people/password.html', {'form': form})
