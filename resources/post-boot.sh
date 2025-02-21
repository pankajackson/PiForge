#!/bin/bash

set -e

# Set up user and password
USER_NAME="lxa"
USER_PASS="123"
sudo useradd -m -s /bin/bash "$USER_NAME" || echo "User $USER_NAME already exists."
echo "$USER_NAME:$USER_PASS" | sudo chpasswd
sudo usermod -aG sudo "$USER_NAME"
sudo -u "$USER_NAME" xdg-user-dirs-update

# Set up hostname
sudo hostnamectl set-hostname "pi.lxa.local"

# Install necessary packages
sudo apt-get update
sudo apt-get install -y git iwd barrier python-pip

# Install and enable necessary services (e.g., ssh)
sudo apt-get update
sudo apt-get install -y ssh
sudo systemctl enable ssh
sudo systemctl start ssh
