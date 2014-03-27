########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import os
from os.path import dirname
import unittest

from cloudify.mocks import MockCloudifyContext
from cloudify.constants import MANAGER_IP_KEY, \
    MANAGER_FILE_SERVER_BLUEPRINTS_ROOT_URL_KEY, MANAGER_FILE_SERVER_URL_KEY

from bash_runner.tasks import run, ProcessException
import bash_runner.tests as test_path


__author__ = 'elip'


def properties_to_dict(properties):
    result = {}
    for line in properties.splitlines():
        (key, val) = line.split("=")
        if val.isdigit():
            val = int(val)
        result[key] = val
    return result


class TestBashRunner(unittest.TestCase):

    file_server_process = None

    @classmethod
    def setUpClass(cls):

        resources_path = os.path.join(dirname(test_path.__file__),
                                      "resources")

        from bash_runner.tests.file_server import FileServer
        from bash_runner.tests.file_server import PORT

        cls.file_server_process = FileServer(resources_path)
        cls.file_server_process.start()

        os.environ[MANAGER_FILE_SERVER_BLUEPRINTS_ROOT_URL_KEY] \
            = "http://localhost:{0}".format(PORT)
        os.environ[MANAGER_FILE_SERVER_URL_KEY] = \
            "http://localhost:{0}".format(PORT)

        os.environ[MANAGER_IP_KEY] = "localhost"

    @classmethod
    def tearDownClass(cls):
        cls.file_server_process.stop()

    def create_context(self, properties):
        return BashRunnerMockCloudifyContext(
            node_id='test',
            blueprint_id='',
            deployment_id='test',
            execution_id='test',
            operation='cloudify.interfaces.lifecycle.start',
            properties=properties)

    def test_script_path(self):
        run(self.create_context({}), script_path="ls.sh")

    def test_scripts(self):

        scripts = {
            'start': 'ls.sh'
        }

        run(self.create_context({'scripts': scripts}))

    def test_no_script_path_no_scripts(self):

        try:
            run(self.create_context({}))
            self.fail("Expected a runtime error")
        except RuntimeError:
            pass

    def test_environment_injection(self):

        properties = {
            'port': 8080,  # test integer
            'url': 'http://localhost',  # test string
            'node_id': u'node_id'  # test unicode
        }

        out = run(self.create_context(properties), script_path="env.sh")

        expected_dict = {
            'CLOUDIFY_NODE_ID': 'test',
            'CLOUDIFY_BLUEPRINT_ID': '',
            'CLOUDIFY_DEPLOYMENT_ID': 'test',
            'CLOUDIFY_MANAGER_IP': 'localhost',
            'CLOUDIFY_EXECUTION_ID': 'test',
            'CLOUDIFY_FILE_SERVER_BLUEPRINT_ROOT': 'http://localhost:53229/',
            'port': 8080,
            'url': 'http://localhost',
            'node_id': 'node_id'
        }

        actual_dict = properties_to_dict(out)
        for key in expected_dict:
            self.assertEqual(expected_dict[key], actual_dict[key])

    def test_complex_property(self):

        properties = {
            'port': {
                'a': 1
            }
        }

        out = run(self.create_context(properties),
                  script_path="env-with-complex-prop.sh")

        expected_dict = {
            'port_a': 1
        }

        actual_dict = properties_to_dict(out)
        for key in expected_dict:
            self.assertEqual(expected_dict[key], actual_dict[key])

    def test_no_script_mapping_for_operation(self):

        scripts = {
            'stop': 'ls.sh'
        }

        out = run(self.create_context({'scripts': scripts}))
        self.assertIsNone(out)

    def test_bad_script(self):
        try:
            run(self.create_context({}), script_path="bad.sh")
        except ProcessException as e:
            self.assertTrue('bad_command: command not found' in e.stderr)
            self.assertTrue(e.exit_code is not 0)

    def test_logging(self):

        out = run(self.create_context({}), script_path="test_logging.sh")
        line = out.splitlines()
        self.assertEqual(line[0],
                         "[INFO] [test_logging.sh] THIS IS AN INFO PRINT")
        self.assertEqual(line[1],
                         "[ERROR] [test_logging.sh] THIS IS AN ERROR PRINT")

    def test_download_resource(self):

        expected_path = "/tmp/index.html"  # see test_file_server.sh
        if os.path.exists(expected_path):  # cleanup
            os.remove(expected_path)

        run(self.create_context({}), script_path="test_file_server.sh",
            log_all=True)

        # check the download_resource actually worked
        self.assertTrue(os.path.exists(expected_path))


class BashRunnerMockCloudifyContext(MockCloudifyContext):

    def download_resource(self, resource_path, target_path=None):
        return os.path.join(dirname(test_path.__file__),
                            "resources", resource_path)
