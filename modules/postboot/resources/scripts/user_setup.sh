#!/bin/bash

set -e

# Set up user and password
USER_NAME="jackson"
USER_PASS="123"
sudo useradd -m -s /bin/bash "$USER_NAME" || echo "User $USER_NAME already exists."
echo "$USER_NAME:$USER_PASS" | sudo chpasswd
sudo usermod -aG sudo "$USER_NAME"
sudo -u "$USER_NAME" xdg-user-dirs-update
