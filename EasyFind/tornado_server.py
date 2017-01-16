import os
import tornado.httpserver
import tornado.ioloop
import tornado.wsgi
from django.core.wsgi import get_wsgi_application


def main():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'EasyFind.settings' # path to your settings module
    application = get_wsgi_application()
    container = tornado.wsgi.WSGIContainer(application)
    http_server = tornado.httpserver.HTTPServer(container)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
