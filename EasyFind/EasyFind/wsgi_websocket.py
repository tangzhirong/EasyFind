# entry point for the websocket loop
import gevent.monkey
gevent.monkey.patch_thread()

from ws4redis.uwsgi_runserver import uWSGIWebsocketServer
application = uWSGIWebsocketServer()

#import os
#import gevent.socket
#import redis.connection
#redis.connection.socket = gevent.socket
#os.environ.update(DJANGO_SETTINGS_MODULE='EasyFind.settings')
#from ws4redis.uwsgi_runserver import uWSGIWebsocketServer
#application = uWSGIWebsocketServer()
