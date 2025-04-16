#!/bin/bash

set -e

SCRIPT=$(basename "$0")
CWD=$(dirname "$0")
BASEDIR=$(realpath "$CWD")
LOG_FILE="/var/log/postboot.log"

echo "Running post apply hook $SCRIPT from $BASEDIR"
exec > >(tee -a "$LOG_FILE") 2>&1

bash "$BASEDIR/system_setup.sh"
bash "$BASEDIR/network_setup.sh"
# bash "$BASEDIR/user_setup.sh"

# Wait for internet before continuing
HOST="8.8.8.8"
WAIT_TIME=5
echo "Waiting for internet connection..."
while ! ping -c 1 -W 1 "$HOST" &>/dev/null; do
    echo "No internet connection. Retrying in $WAIT_TIME seconds..."
    sleep "$WAIT_TIME"
done

bash "$BASEDIR/sshd_setup.sh"
bash "$BASEDIR/packages_setup.sh"

# Disable once the service ran successfully
systemctl disable postboot.service
