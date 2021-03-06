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
import collections
import subprocess
import fcntl
import select
import os
import errno
from os.path import dirname

from cloudify import utils
from cloudify.utils import get_manager_ip
from cloudify.decorators import operation

from bash_runner import resources


@operation
def run(ctx, script_path=None, log_all=False, **kwargs):

    """
    Execute bash scripts.

        Parameters:

            scripts - A dictionary mapping lifecycle events to script paths.

            script_path - The path to the script relative
                          to the blueprints root directory.
                          Will only be used if the 'scripts' argument is None.
        Exceptions:

            If both 'scripts' and 'script_path' is None.
            A runtime exception will be raised since there is no
            script to run.
    """

    sh = get_script_to_run(ctx, script_path)
    if sh is None:
        return None
    bash(sh, ctx, log_all)
    return "[{0}] succeeded. return code 0".format(os.path.basename(sh))


def get_script_to_run(ctx, script_path=None):
    if script_path:
        return ctx.download_resource(script_path)
    if 'scripts' in ctx.properties:
        operation_simple_name = ctx.operation.split('.')[-1:].pop()
        scripts = ctx.properties['scripts']
        if operation_simple_name not in scripts:
            ctx.logger.info("No script mapping found for operation {0}. "
                            "Nothing to do.".format(operation_simple_name))
            return None
        return ctx.download_resource(scripts[operation_simple_name])

    raise RuntimeError('No script to run')


def run_and_return_output(ctx, script_path=None, log_all=False, **kwargs):
    sh = get_script_to_run(ctx, script_path)
    if sh is None:
        return None
    return bash(sh, ctx, log_all)


def strip_level(line, level):
    return line.replace('[{0}] '.format(level), '', 1)


def is_info_log(line):
    return line.startswith('[INFO]')


def is_error_log(line):
    return line.startswith('[ERROR]')


def bash(path, ctx, log_all):
    return execute("/bin/bash {0}".format(path), ctx, log_all)


def execute(command, ctx, log_all):
    ctx.logger.info('Running command: %s' % command)
    env = setup_environment(ctx)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               env=env)
    make_async(process.stdout)
    make_async(process.stderr)

    stdout = str()
    stderr = str()
    return_code = None

    while True:
        # Wait for data to become available
        select.select([process.stdout, process.stderr], [], [])

        return_code = process.poll()

        # Try reading some data from each
        stdout_piece = read_async(process.stdout)
        stderr_piece = read_async(process.stderr)

        if stdout_piece:
            if is_info_log(stdout_piece) or log_all:
                ctx.logger.info(strip_level(stdout_piece,
                                            'INFO'))
            if is_error_log(stdout_piece):
                ctx.logger.error(strip_level(stdout_piece,
                                             'ERROR'))
        if stderr_piece:
            ctx.logger.error(stderr_piece)

        stdout += stdout_piece
        stderr += stderr_piece

        if return_code is not None and not stdout_piece and not stderr_piece:
            break

    ctx.logger.info('Done running command (return_code=%d): %s'
                    % (return_code, command))
    if return_code == 0:
        return stdout
    else:
        raise ProcessException(command, return_code, stdout, stderr)


# Helper function to add the O_NONBLOCK flag to a file descriptor
def make_async(fd):
    fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) |
                os.O_NONBLOCK)


# Helper function to read some data from a file descriptor,
# ignoring EAGAIN errors
def read_async(fd):
    try:
        return fd.readline()
    except IOError, e:
        if e.errno != errno.EAGAIN:
            raise e
        else:
            return ''


def flatten(d, parent_key=''):
    items = []
    for k, v in d.items():
        new_key = parent_key + '_' + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)


def setup_environment(ctx):
    """
    Add some useful environment variables to the environment
    """

    env = os.environ.copy()
    # See in context.py
    # https://github.com/CloudifySource
    # /cosmo-celery-common/blob/develop/cloudify/context.py
    env['CLOUDIFY_NODE_ID'] = ctx.node_id.encode('utf-8')
    env['CLOUDIFY_BLUEPRINT_ID'] = ctx.blueprint_id.encode('utf-8')
    env['CLOUDIFY_DEPLOYMENT_ID'] = ctx.deployment_id.encode('utf-8')
    env['CLOUDIFY_MANAGER_IP'] = get_manager_ip().encode('utf-8')
    env['CLOUDIFY_EXECUTION_ID'] = ctx.execution_id.encode('utf-8')

    logging_script_path = os.path.join(dirname(resources.__file__),
                                       "logging.sh")

    file_server_script_path = os.path.join(dirname(resources.__file__),
                                           "file_server.sh")

    env['CLOUDIFY_LOGGING'] = logging_script_path
    env['CLOUDIFY_FILE_SERVER'] = file_server_script_path

    url = '{0}/{1}'.format(
        utils.get_manager_file_server_blueprints_root_url(),
        ctx.blueprint_id)

    env['CLOUDIFY_FILE_SERVER_BLUEPRINT_ROOT'] = url.encode('utf-8')

    # assuming properties are flat.
    # inject each property as an environment variable.
    for key, value in flatten(ctx.properties).iteritems():
        env[key] = value.encode('utf-8') \
            if isinstance(value, unicode) \
            or isinstance(value, str) else repr(value)

    return env


class ProcessException(Exception):
    def __init__(self, command, exit_code, stdout, stderr):
        Exception.__init__(self, stderr)
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
