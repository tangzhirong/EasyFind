
from django.conf.urls import patterns, include, url
import views
from django.conf import settings
from django.conf.urls.static import static

from django_sse.redisqueue import RedisQueueView

urlpatterns = patterns('',
	('^publish/(\w+)$', 'tasks.views.publish'),
	('^redis_discover/$', 'tasks.views.redis_discover'),
	# url(r'^stream1/$', RedisQueueView.as_view(redis_channel="foo"), name="stream1"),
)+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)

# urlpatterns += patterns('',
#     url(r'^sse/$', 'views.SSE.as_view()', name='sse'),  # this URL is arbitrary.
#     url(r'^$', 'views.HomePage.as_view()', name='homepage'),
# )
