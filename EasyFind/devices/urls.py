from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
	('^(\w+)$', 'devices.views.devices'),
	('^addDevice/(\w+)$', 'devices.views.addDevice'),
	('^removeDevice/(.+)/$', 'devices.views.removeDevice'),
)
