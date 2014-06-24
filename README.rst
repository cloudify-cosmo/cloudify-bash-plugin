Cloudify Bash Plugin
====================

This plugin allows the execution of bash scripts as part of a node
interface opeations.

Usage
-----

**built-in bash types**

Cloudify offers some built in types, whose lifecycle interface (see
`Lifecycle
Interface <https://github.com/CloudifySource/cosmo-manager/blob/develop/orchestrator/src/main/resources/cloudify/types/types.yaml#L18>`__)
is mapped to execute bash scripts by default. When using these types, a
property by the name of 'scripts' should be part of the node properties,
mapping each interface operation to a specific script.

for example:

::

    -   name: http_web_server
        type: cloudify.types.bash.web_server
        properties:
          scripts:            
            configure: scripts/configure.sh
            start: scripts/start.sh
            stop: scripts/stop.sh

This means that the 'configure', 'start' and 'stop' operations will be
executed by the 'configure.sh', 'start.sh' and 'stop.sh' scripts
respectively. You can of course create you own interface and map any
operation to any script.

for a complete example of the usage see `Cloudify Hello
World <https://github.com/CloudifySource/cloudify-hello-world/blob/feature/CFY-430-hello-world-bash/hello-world/blueprint.yaml>`__

**direct operation mapping**

You can also specify a script for execution on a specific operation by
mapping it directly inside the intefrace declaration.

for example:

::

    types:
      my_new_type:
        derived_from: cloudify.types.base
        interfaces:
            my_new_interface:
                - my_new_operation:
                      mapping: 'bash_runner.tasks.run'
                      properties:
                          script_path: 'scripts/my-new-script.sh'
                          

This means the operation 'my\_new\_operation' of inteface
'my\_new\_inteface' for the type 'my\_new\_type' is mapped to the Bash
plugin, with the 'my-new-script.sh' set for execution.

API
---

Cloudify offers some extra API available to use inside your scripts.

**blueprint resource access**

You can access blueprint resource inside your script using the function
'download\_resource <relative\_path\_to\_resource>', to enable this
function add the following line at the beginning of your script:

::

    . ${CLOUDIFY_FILE_SERVER}

for example:

::

    . ${CLOUDIFY_FILE_SERVER}
    cfy_download_resource index.html

index.html in this example should be placed in the root of the blueprint
folder.

*NOTE: This function is implemented using bash 'wget' function. That
means you can pass any wget flags as well.*

**logging**

You can log messages from the script by using the 'info <message>' and
'error <message>' functions. to enable these function add the following
line at the beginning of your script:

::

    . ${CLOUDIFY_LOGGING}

for example:

::

    cfy_info THIS IS AN INFO PRINT
    cfy_error THIS IS AN ERROR PRINT

This messages will be stored in Cloudify's logging mechanism and be
viewed as regular logs. As such, they will be displayed in the CLI, as
well as the Web interface.

By default, Cloudify will not log the script's system out stream. to
enable this type of logging, pass the 'log\_all' property as part of the
node properties, or in the direct mapping approach. (see above)
