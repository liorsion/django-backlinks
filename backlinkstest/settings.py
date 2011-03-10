import os

SITE_ID = 1
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = os.path.join(os.path.dirname(__file__), 'backlinks.db')
INSTALLED_APPS = ['django.contrib.sites', 'backlinks', 'backlinks.pingback', 'backlinks.trackback']
ROOT_URLCONF = ['tetproject.urls']
