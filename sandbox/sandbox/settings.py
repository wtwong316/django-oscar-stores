import os

from django.utils.translation import gettext_lazy as _

import oscar

PROJECT_DIR = os.path.join(os.path.dirname(__file__), '..')
location = lambda x: os.path.join(PROJECT_DIR, x)

DEBUG = True
THUMBNAIL_DEBUG = DEBUG

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Default to using PostGIS.  Use a settings_local.py file to use a different
# database for testing (eg Spatialite)
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'oscar_stores',
        'USER': 'wai_takwong',
        'PASSWORD': 'wai_takwong',
        'HOST': 'localhost',
        'PORT': 5432,
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = location('public/media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

STATIC_URL = '/static/'
STATICFILES_DIRS = (location('static/'),)
STATIC_ROOT = location('public')

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'sba9ti)x&amp;^fkod-g91@^_yi6y_#&amp;3mo#m5@n)i&amp;k+0h=+zsfkb'

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'oscar.apps.basket.middleware.BasketMiddleware',
)

ROOT_URLCONF = 'sandbox.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'sandbox.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            location('templates'),
        ],
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',

                # Oscar specific
                'oscar.apps.search.context_processors.search_form',
                'oscar.apps.communication.notifications.context_processors.notifications',
                'oscar.apps.checkout.context_processors.checkout',
                'oscar.core.context_processors.metadata',
            ],
            'debug': DEBUG,
        }
    }
]

INSTALLED_APPS = [
    'django.contrib.gis',
    'sorl.thumbnail',
    'sdfs',
    'sdfs.dashboard',
    'sdfs.action',
    'esearch',
    'rest_framework',
    'django_countries',
    "django_elasticsearch_dsl",
    "django_elasticsearch_dsl_drf",
] + oscar.INSTALLED_APPS

AUTHENTICATION_BACKENDS = (
    'oscar.apps.renter.auth_backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# Oscar settings
from oscar.defaults import * # noqa E402

OSCAR_DASHBOARD_NAVIGATION.append(
    {
        'label': _('Sdfs'),
        'icon': 'fas fa-building-o',
        'children': [
            {
                'label': _('Sdfs'),
                'url_name': 'sdfs-dashboard:sdf-list',
            },
            {
                'label': _('Sdus'),
                'url_name': 'sdfs-dashboard:sdf-sdu-list',
            },
            {
                'label': _('Sdf groups'),
                'url_name': 'sdfs-dashboard:sdf-group-list',
            },
        ]
    })

OSCAR_ALLOW_ANON_CHECKOUT = True

OSCAR_SHOP_TAGLINE = "劏房住戶好幫手"

GEOIP_ENABLED = True
GEOIP_PATH = os.path.join(os.path.dirname(__file__), '../geoip')

# Haystack settings
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    },
}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'sorl.thumbnail': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

# This is set here to make spatialite work with Mac OS X it should
# not impact other linux-based systems. It has been tested on Ubuntu
# and works fine.
spatialite_lib = os.environ.get('SPATIALITE_LIBRARY_PATH', None)
if spatialite_lib is not None:
    SPATIALITE_LIBRARY_PATH = spatialite_lib

# Allow local overrides
try:
    from .settings_local import *   # noqa F403
except ImportError:
    pass

GOOGLE_MAPS_API_KEY = 'AIzaSyB1Y2sRZh6K4PgxqEnUD5Bt-TtOc5x5aA0'

from django.contrib.gis.measure import D
# Maximal distance of 150 kilometers
STORES_MAX_SEARCH_DISTANCE = D(km=5)

LOCALE_PATHS = (
    os.path.join(PROJECT_DIR, 'locale/'),
)

OSCAR_DEFAULT_CURRENCY = 'HKD'

# Elasticsearch
ELASTICSEARCH_DSL = {
    "default": {"hosts": "localhost:9200/"}
}

ELASTICSEARCH_INDEX_NAMES = {
    'sdfs.SdfSdu': 'sdus',
}

ALLOWED_HOSTS = ['*']
