"""
WSGI config for sample project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

try:
    from dotenv import load_dotenv
    BASE_DIR = Path(__file__).resolve().parent.parent  # /home/django/sample/sample/.. = /home/django/sample
    load_dotenv(BASE_DIR / '.env')  # OS側に既にある環境変数は上書きしない
except Exception:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sample.settings')

application = get_wsgi_application()
