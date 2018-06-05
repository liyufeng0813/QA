from django.conf.urls import url
from people.views import follower, handle, setting
from question import views as question_views


urlpatterns = [
    url(r'^my/fav/$', question_views.fav_topic_list, name='fav_topic_list'),

    url(r'^follow/(?P<uid>\d+)/$', follower.follow, name='follow'),
    url(r'^unfollow/(?P<uid>\d+)/$', follower.unfollow, name='unfollow'),
    url(r'^my/following/$', follower.following, name='following'),

    url(r'^register/$', handle.register, name='register'),
    url(r'^login/$', handle.login, name='login'),
    url(r'^logout/$', handle.logout, name='logout'),

    url(r'^users/$', handle.au_top, name='au_top'),
    url(r'^user/(?P<uid>\d+)/$', handle.user, name='user'),
    url(r'^user/(?P<uid>\d+)/topics/$', handle.user_topics, name='user_topics'),
    url(r'^user/(?P<uid>\d+)/comments/$', handle.user_comments, name='user_comments'),

    url(r'^send_verified_email/$', handle.send_verified_email, name='send_verified_email'),
    url(r'^email_verified/(?P<uid>\d+)/(?P<token>\w+)/$', handle.email_verified, name='email_verified'),
    url(r'^find_password/$', handle.find_password, name='find_pass'),
    url(r'^reset_password/$', handle.reset_password, name='reset_password'),
    url(r'^reset_password/(?P<uid>\d+)/(?P<token>\w+)/$', handle.first_reset_password, name='first_reset_password'),

    url(r'^settings/$', setting.profile, name='settings'),
    url(r'^password/$', setting.password, name='password'),

    url(r'^settings/upload_headimage/$', setting.upload_headimage, name='upload_headimage'),
    url(r'^settings/delete_headimage/$', setting.delete_headimage, name='delete_headimage'),
]
