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
sudo apt-get install -y git iwd python-pip
sudo pip install --upgrade pip setuptools wheel pigpio

# Set up keyboard layout
sudo localectl set-keymap "us" --no-convert

# Set up timezone and locale
sudo timedatectl set-timezone "Asia/Kolkata"
sudo locale-gen "en_US.UTF-8"
sudo update-locale LANG="en_US.UTF-8"

# Static IP Configuration
echo "interface eth0" | sudo tee -a /etc/dhcpcd.conf
echo "static ip_address=192.168.1.10/24" | sudo tee -a /etc/dhcpcd.conf
echo "static routers=192.168.1.1" | sudo tee -a /etc/dhcpcd.conf
echo "static domain_name_servers=8.8.8.8" | sudo tee -a /etc/dhcpcd.conf

# Install and enable necessary services (e.g., ssh)
sudo apt-get update
sudo apt-get install -y ssh
sudo systemctl enable ssh
sudo systemctl start ssh
