import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'g2g_textiles.settings')
application = get_wsgi_application()
