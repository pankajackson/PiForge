#!/bin/bash

set -e

HOST_NAME="${HOST_NAME:-pi.lxa.com}"

# Set up hostname
sudo hostnamectl set-hostname "$HOST_NAME"
