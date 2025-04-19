#!/bin/bash

set -e

SCRIPT=$(basename "$0")
CWD=$(dirname "$0")
BASEDIR=$(realpath "$CWD")
LOG_FILE="$BASEDIR/logs/postboot.log"
LOG_DIR=$(dirname "$LOG_FILE")

# Existing logging setup
echo "Running post apply hook $SCRIPT from $BASEDIR"
exec > >(tee -a "$LOG_FILE") 2>&1
ln -sf "$LOG_FILE" "$LOG_DIR/postboot.txt"

# Start Python HTTP server in background
PORT=8182
python3 -m http.server "$PORT" --directory "$LOG_DIR" &
SERVER_PID=$!
sleep 1

bash "$BASEDIR/vars.sh"
bash "$BASEDIR/system_setup.sh"
bash "$BASEDIR/network_setup.sh"
# bash "$BASEDIR/user_setup.sh" # Managed by first run script

# Wait for internet before continuing
HOST="8.8.8.8"
WAIT_TIME=5
echo "Waiting for internet connection..."
while ! ping -c 1 -W 1 "$HOST" &>/dev/null; do
    echo "No internet connection. Retrying in $WAIT_TIME seconds..."
    sleep "$WAIT_TIME"
done

# bash "$BASEDIR/sshd_setup.sh" # Managed by first run script
bash "$BASEDIR/packages_setup.sh"

# Disable once the service ran successfully
systemctl disable postboot.service

# Stop the service
if ps -p "$SERVER_PID" >/dev/null; then
    kill "$SERVER_PID"
fi
