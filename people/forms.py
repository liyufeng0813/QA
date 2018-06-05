from django import forms
from django.core.validators import URLValidator
from people.models import Member


class RegisterForm(forms.Form):
    username = forms.CharField(label='用户名', min_length=2, max_length=16, required=True)
    password1 = forms.CharField(label='密码', min_length=6, max_length=30, widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(label='重复密码', min_length=6, max_length=30, widget=forms.PasswordInput, required=True)
    email = forms.EmailField(label='邮箱', max_length=255, required=True)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1', '')
        password2 = self.cleaned_data.get('password2', '')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('两次密码不相同！')
        return password2

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()

        if username.startswith('_'):
            raise forms.ValidationError('用户名不可以以下划线开头！')
        if '@' in username:
            raise forms.ValidationError('用户名内不可含有 @ 符号！')

        try:
            Member._default_manager.get(username=username)
        except Member.DoesNotExist:
            return username
        raise forms.ValidationError('用户名 "{}" 已经存在！'.format(username))

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()

        try:
            Member._default_manager.get(email=email)
        except Member.DoesNotExist:
            return email
        raise forms.ValidationError('邮箱 "" 已经存在！'.format(email))


class LoginForm(forms.Form):
    username = forms.CharField(label='用户名', required=True)
    password = forms.CharField(label='密码', widget=forms.PasswordInput, required=True)

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        username_exist, email_exist = True, True

        try:
            Member._default_manager.get(username=username)
        except Member.DoesNotExist:
            username_exist = False
        try:
            Member._default_manager.get(email=username)
        except Member.DoesNotExist:
            email_exist = False

        if username_exist or email_exist:
            return username
        raise forms.ValidationError('用户名或者邮箱不存在！')


class ProfileForm(forms.ModelForm):
    blog = forms.CharField(label='博客', max_length=255, required=False, validators=[URLValidator],
                           widget=forms.URLInput(attrs={'class': 'form-control'}))
    location = forms.CharField(label='城市', max_length=50, required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    weibo = forms.CharField(label='新浪微博', max_length=255, required=False,
                            widget=forms.TextInput(attrs={'class': 'form-control'}))
    profile = forms.CharField(label='个人介绍', max_length=255, required=False,
                              widget=forms.Textarea(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='邮箱', max_length=255, required=True,
                             widget=forms.TextInput(attrs={'class': 'disabled form-control'}))

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        user = kwargs.get('instance', None)
        self.old_email = user.email

    def clean_email(self):
        cleaned_data = super(ProfileForm, self).clean()
        email = cleaned_data.get('email').strip()
        try:
            user = Member._default_manager.get(email=email)
        except (Member.DoesNotExist, ValueError):
            return email
        else:
            if user.email == self.old_email:
                return email
            else:
                raise forms.ValidationError('邮箱 "{}" 已经存在'.format(email))

    def clean_weibo(self):
        weibo = self.cleaned_data.get('weibo', '').strip()

        if weibo.startswith('@'):
            weibo = weibo[1:]
        return weibo

    class Meta:
        model = Member
        fields = ('email', 'blog', 'location', 'weibo', 'profile')


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(label='原密码', required=True,
                                   widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label='新密码', required=True, min_length=6, max_length=30,
                                   widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='重复新密码', required=True, min_length=6, max_length=30,
                                   widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1', '')
        password2 = self.cleaned_data.get('password2', '')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('两次输入的密码不相同！')
        return password2
