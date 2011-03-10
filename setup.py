import os
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'django-backlinks',
    version = '0.1a1',
    license = 'BSD',
    description = 'A generic linkbacks app for Django',
    long_description = read('README'),
    author = 'Jeff Kistler',
    author_email = 'jeff@jeffkistler.com',
    url = 'https://bitbucket.org/jeffkistler/django-backlinks',
    packages = ['backlinks',
                'backlinks.templatetags',
                'backlinks.tests',
                'backlinks.utils',
                'backlinks.pingback',
                'backlinks.pingback.templatetags',
                'backlinks.trackback',
                'backlinks.trackback.templatetags'],
    package_dir = {'': 'src'},
    package_data = {'backlinks': ['fixtures/*',],
                    'backlinks.trackback': ['templates/backlinks/trackback/*']},
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
