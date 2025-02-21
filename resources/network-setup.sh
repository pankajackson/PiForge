#!/bin/bash

# Define static IP settings
ETH0_IPS="192.168.1.10/24,10.0.0.10/24"
WLAN0_IPS="192.168.1.11/24,10.0.0.11/24"
GATEWAY="192.168.1.1"
ETH0_DNS="192.168.1.10,8.8.8.8"
WLAN0_DNS="192.168.1.11,8.8.8.8"
WIFI_SSID="${WIFI_SSID:-JACKSON_PRIVATE_NETWORK}"
WIFI_PASSWORD="${WIFI_PASSWORD:-test123}"

# Check if NetworkManager is installed
if ! command -v nmcli &>/dev/null; then
    echo "Error: NetworkManager is not installed. Please install it first."
    exit 1
fi

# Remove only NetworkManager-managed default connections (ignore Docker/other system bridges)
echo "Removing existing NetworkManager connections (excluding bridges)..."
nmcli -t -f NAME,DEVICE con show | grep -Ev 'docker|br-|virbr|vnet|tun|tap|lo' | cut -d: -f1 | while read -r con; do
    nmcli con delete "$con"
done

# Configure Ethernet (eth0)
echo "Setting up static IP for eth0..."
nmcli con add type ethernet ifname eth0 con-name static-eth0 ipv4.method manual \
    ipv4.addresses "$ETH0_IPS" \
    ipv4.gateway "$GATEWAY" \
    ipv4.dns "$ETH0_DNS" \
    autoconnect yes

# Configure Wi-Fi (wlan0)
echo "Setting up static IP for wlan0..."
nmcli con add type wifi ifname wlan0 con-name static-wlan ssid "$WIFI_SSID" ipv4.method manual \
    ipv4.addresses "$WLAN0_IPS" \
    ipv4.gateway "$GATEWAY" \
    ipv4.dns "$WLAN0_DNS" \
    autoconnect yes

# Set Wi-Fi password if needed
if [ -n "$WIFI_PASSWORD" ]; then
    nmcli con modify static-wlan wifi-sec.key-mgmt wpa-psk
    nmcli con modify static-wlan wifi-sec.psk "$WIFI_PASSWORD"
fi

# Restart connections
echo "Restarting network connections..."
nmcli con down static-eth0 && nmcli con up static-eth0
nmcli con down static-wlan && nmcli con up static-wlan

# Verify setup
echo "Final Network Configuration:"
nmcli con show
ip a

echo "Static IP setup completed successfully!"
