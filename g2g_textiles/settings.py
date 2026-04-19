from pathlib import Path
import os
import dj_database_url
import cloudinary
import cloudinary.uploader
import cloudinary.api

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'gtwog.ch',
    'www.gtwog.ch',
    'g2g-textiles.onrender.com',
    'localhost',
    '127.0.0.1',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary_storage',
    'cloudinary',
    'homepage',
]

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
    'MEDIA_TAG': 'media',
    'INVALID_VIDEO_ERROR_MESSAGE': 'Please upload a valid video file.',
    'EXCLUDE_DELETE_ORPHANED_MEDIA_UNDER_FOLDER': '',
    'STATIC_TAG': 'static',
    'STATICFILES_MANIFEST_ROOT': '',
    'STATIC_IMAGES_EXTENSIONS': ['jpg', 'jpe', 'jpeg', 'jpc', 'jp2', 'j2k', 'wdp', 'jxr', 'hdp', 'png', 'gif', 'webp', 'bmp', 'tif', 'tiff', 'ico'],
    'STATIC_VIDEOS_EXTENSIONS': ['mp4', 'webm', 'flv', 'mov', 'ogv', 'avi', 'wmv', 'mpeg', 'flv', '3gp', '3g2'],
    'MAGIC_FILE_PATH': 'magic',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'g2g_textiles.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'g2g_textiles.wsgi.application'

# --- Database ---
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600
    )
}

# --- i18n ---
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', 'English'),
    ('de', 'Deutsch'),
]
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]
USE_I18N = True
USE_L10N = True
USE_TZ = True
TIME_ZONE = 'UTC'

# --- Static files ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- Media files (Cloudinary) ---
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- Upload size limits ---
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Email ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.resend.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = 'resend'
EMAIL_HOST_PASSWORD = os.environ.get('RESEND_API_KEY', '')
DEFAULT_FROM_EMAIL = 'G2G Textiles <production@gtwog.ch>'
QUOTE_NOTIFICATION_EMAIL = 'production@gtwog.ch'

# --- Auth ---
LOGIN_URL = '/en/portal/login/'
LOGIN_REDIRECT_URL = '/en/portal/'
LOGOUT_REDIRECT_URL = '/en/portal/login/'