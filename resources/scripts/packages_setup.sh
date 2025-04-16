#!/bin/bash

set -e

# Install necessary packages
sudo apt-get update
sudo apt-get install -y git iwd barrier python3-pip python3-dev python3-venv
