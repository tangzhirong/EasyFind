from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
	('^(\w+)$', 'personal_info.views.personInfo'),
)
