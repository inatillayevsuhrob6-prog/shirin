import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
application=get_wsgi_application()

script_name = os.getenv('FORCE_SCRIPT_NAME', '').rstrip('/')
if script_name:
    django_application = application

    def application(environ, start_response):
        path_info = environ.get('PATH_INFO', '')
        if path_info == script_name:
            environ['PATH_INFO'] = '/'
        elif path_info.startswith(f'{script_name}/'):
            environ['PATH_INFO'] = path_info[len(script_name):]
        return django_application(environ, start_response)
