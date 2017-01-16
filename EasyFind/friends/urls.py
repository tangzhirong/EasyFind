from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
	('^(\w+)$', 'friends.views.friends'),
	('^remove/$', 'friends.views.remove'),
)
