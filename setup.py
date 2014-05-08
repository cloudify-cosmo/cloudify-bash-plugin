#########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

__author__ = 'rantav'

from setuptools import setup

PLUGINS_COMMON_VERSION = "3.0b1"
PLUGINS_COMMON_BRANCH = "3.0b1"
PLUGINS_COMMON = "https://github.com/cloudify-cosmo" \
    "/cloudify-plugins-common/tarball/{0}"\
    .format(PLUGINS_COMMON_BRANCH)

setup(
    name='cloudify-bash-plugin',
    version='1.0b1',
    author='rantav',
    author_email='rantav@gmail.com',
    packages=['bash_runner', 'bash_runner/resources'],
    package_data={'bash_runner': ['resources/file_server.sh',
                                  'resources/logging.sh']},
    license='LICENSE',
    description='Plugin for running simple bash scripts',
    install_requires=[
        "cloudify-plugins-common"
    ],
    dependency_links=["{0}#egg=cloudify-plugins-common-{1}"
                      .format(PLUGINS_COMMON, PLUGINS_COMMON_VERSION)])
