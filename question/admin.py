from django.contrib import admin
from question.models import *


class TopicAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'node', 'author', 'num_views', 'num_comments', 'created_on', 'updated_on']
    search_fields = ['id', 'title', 'node']
    list_filter = ['node__name']


class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'topic', 'author', 'content', 'created_on']
    list_filter = ['topic__node__name']


class NodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'created_on', 'updated_on', 'num_topics']


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


class NoticeAdmin(admin.ModelAdmin):
    list_display = ['id', 'from_user', 'to_user', 'topic', 'is_readed', 'is_deleted', 'time']


class FavoritedTopicAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'topic']


admin.site.register(Topic, TopicAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Node, NodeAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Notice, NoticeAdmin)
admin.site.register(FavoritedTopic, FavoritedTopicAdmin)
