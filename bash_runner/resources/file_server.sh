#!/bin/bash
function download_resource() { wget -x -nH ${CLOUDIFY_FILE_SERVER_BLUEPRINT_ROOT}/$@; }
