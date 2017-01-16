"""EasyFind URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
import views
from django_sse.redisqueue import RedisQueueView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$',views.index),
    url(r'^login$',views.login),
    url(r'^logon$',views.logon),
    url(r'^logout/(\w+)$',views.logout),
    url(r'^(\w+)$',views.user_page),
    url(r'^tasks/',include('tasks.urls')),
    url(r'^task_deliver/$',views.task_deliver),
    url(r'^task_out/$',views.task_out),
    url(r'^task_over/$',views.task_over),
    url(r'^showInfo/$',views.showInfo),
    url(r'^getLocation/$',views.getLocation),
    url(r'^devices/',include('devices.urls')),
    url(r'^personal_info/',include('personal_info.urls')),
    url(r'^friends/',include('friends.urls')),
    url(r'^test/',views.test),
    url(r'^ios/',include('ios.urls')),
    url(r'^userPage/(\w+)$',views.userPage),
    url(r'^addFriend/',views.addFriend),
    url(r'^isRead/',views.isRead),
    url(r'^log/',views.showlog),
    url(r'^userlog/',views.showUserlog),
    url(r'^showSystemIndex/',views.showSystemIndex),
    url(r'^getUserInfo/',views.getUserInfo),
    #url(r'^sse/$', views.SSE.as_view(), name='sse'),  # this URL is arbitrary.
    # url(r'^stream1/$', RedisQueueView.as_view(redis_channel="foo"), name="stream1"),
    # url(r'^stream2/$', views.MySseStreamView.as_view(), name="stream2"),
    #url(r'^stream2/$', views.sse_request),
    #url(r'^event1/$', views.MySseStreamView),
    #url(r'^$', views.HomePage.as_view(), name='homepage'),
]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)



#urlpatterns = patterns('',

#) + staticfiles_urlpatterns()
# urlpatterns += patterns('',
#     url(r'^sse/$', RedisQueueView.as_view(redis_channel="foo"), name="sse"),
# )
