from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
	('^app_login/$', 'ios.views.app_login'),
	('^app_register/$', 'ios.views.app_register'),
	('^get_device/$', 'ios.views.get_device'),
	('^add_device/$', 'ios.views.add_device'),
	('^delete_device/$', 'ios.views.delete_device'),
	('^search_user/$', 'ios.views.search_user'),
	('^get_friends/$', 'ios.views.get_friends'),
	('^add_friend/$', 'ios.views.add_friend'),
	('^delete_friend/$', 'ios.views.delete_friend'),
	('^get_tasks/$', 'ios.views.get_tasks'),
	('^accept_task/$', 'ios.views.accept_task'),
	('^publish_task/$', 'ios.views.publish_task'),
	('^task_out/$', 'ios.views.task_out'),
	('^task_over/$', 'ios.views.task_over'),
	('^task_discover/$', 'ios.views.task_discover'),
	('^get_devices/$', 'ios.views.get_devices'),
	('^upload_taskImg/$', 'ios.views.upload_taskImg'),
	
)
