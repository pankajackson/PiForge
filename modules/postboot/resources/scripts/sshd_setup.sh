#!/bin/bash

set -e

# Install and enable necessary services (e.g., ssh)
sudo apt-get install -y ssh
sudo systemctl enable ssh
sudo systemctl start ssh
