# entry point for the Django loop
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

#import os
#os.environ.update(DJANGO_SETTINGS_MODULE='EasyFind.settings')
#from django.core.wsgi import get_wsgi_application
#application = get_wsgi_application()
