#/usr/bin/env python  
from tornado.options import options, define, parse_command_line  
from django.core.wsgi import get_wsgi_application  
import tornado.httpserver  
import tornado.ioloop  
import tornado.web  
import tornado.wsgi  
import os, sys  
  
  
SITE_ROOT = os.path.dirname(os.getcwd())   
PROJECT_NAME = os.path.basename(os.getcwd())  
  
sys.path.append( SITE_ROOT )  
os.environ['DJANGO_SETTINGS_MODULE'] = PROJECT_NAME + '.settings'  
  
define('port', type=int, default=8080)  
def main():  
    tornado.options.parse_command_line()  
  
    wsgi_app = tornado.wsgi.WSGIContainer(  
        get_wsgi_application())  
  
    tornado_app = tornado.web.Application(  
        [              
            ('.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),  
        ])  
  
    server = tornado.httpserver.HTTPServer(tornado_app)  
    server.listen(options.port)  
    tornado.ioloop.IOLoop.instance().start()  
  
if __name__ == '__main__':  
        main()  