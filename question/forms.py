from django import forms
from question.models import Topic, Comment


class TopicForm(forms.ModelForm):
    title = forms.CharField(label='标题', required=True)
    content = forms.CharField(label='内容', required=True)

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 3 or len(title) > 100:
            raise forms.ValidationError('标题长度请控制在：3-100！')
        else:
            return title

    class Meta:
        model = Topic
        fields = ('title', 'content')


class ReplyForm(forms.ModelForm):
    content = forms.CharField(label='回复', required=True)

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()

        if len(content) == 0:
            raise forms.ValidationError('评论不可为空！')
        if len(content) > 1000:
            raise forms.ValidationError('评论内容不可长于1000！')
        else:
            return content

    class Meta:
        model = Comment
        fields = ('content',)
