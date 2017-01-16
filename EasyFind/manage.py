# !/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "EasyFind.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

# from gevent import monkey; monkey.patch_all()
# from gevent.wsgi import WSGIServer
#
# from django.core.management import setup_environ
# import settings
# setup_environ(settings)
#
# from django.core.handlers.wsgi import WSGIHandler as DjangoWSGIApp
# application = DjangoWSGIApp()
# server = WSGIServer(("127.0.0.1", 1234), application)
# print "Starting server on http://127.0.0.1:1234"
# server.serve_forever()
