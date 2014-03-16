__author__ = 'rantav'

from setuptools import setup

COSMO_CELERY_VERSION = "0.3"
COSMO_CELERY_BRANCH = "develop"
COSMO_CELERY = "https://github.com/CloudifySource" \
               "/cosmo-celery-common/tarball/{0}"\
               .format(COSMO_CELERY_BRANCH)

setup(
    name='cloudify-bash-plugin',
    version='0.1.0',
    author='rantav',
    author_email='rantav@gmail.com',
    packages=['bash_runner'],
    license='LICENSE',
    description='Plugin for running simple bash scripts',
    install_requires=[
        "cosmo-celery-common"
    ],
    dependency_links=["{0}#egg=cosmo-celery-common-{1}"
                      .format(COSMO_CELERY, COSMO_CELERY_VERSION)])
