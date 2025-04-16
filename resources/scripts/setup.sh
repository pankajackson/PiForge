#!/bin/bash

set -e

SCRIPT=$(basename "$0")
CWD=$(dirname "$0")
BASEDIR=$(realpath $CWD)

echo "Running post apply hook $SCRIPT from $BASEDIR"

bash $BASEDIR/system_setup.sh
bash $BASEDIR/network_setup.sh
bash $BASEDIR/user_setup.sh
bash $BASEDIR/sshd_setup.sh
bash $BASEDIR/packages_setup.sh
