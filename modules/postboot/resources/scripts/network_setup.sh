#!/bin/bash

# Define static IP settings
ETH_IFACE=$(nmcli device status | awk '$2 == "ethernet" {print $1; exit}')
WLAN_IFACE=$(nmcli device status | awk '$2 == "wifi" {print $1; exit}')
ETH0_IPS="192.168.1.20/24"
WLAN0_IPS="192.168.1.30/24"
GATEWAY="192.168.1.10"
ETH0_DNS="192.168.1.20,8.8.8.8"
WLAN0_DNS="192.168.1.30,8.8.8.8"
WIFI_SSID="${WIFI_SSID:-MY_SSID}"
WIFI_PASSWORD="${WIFI_PASSWORD:-MY_PASSWORD}"
WIFI_COUNTRY="${WIFI_COUNTRY:-IN}"

# Check if NetworkManager is installed
if ! command -v nmcli &>/dev/null; then
    echo "Error: NetworkManager is not installed. Please install it first."
    exit 1
fi

# Unblock Wi-Fi if soft-blocked
if command -v rfkill &>/dev/null; then
    if rfkill list wifi | grep -q "Soft blocked: yes"; then
        echo "Wi-Fi is soft blocked. Unblocking..."
        rfkill unblock wifi
        for filename in /var/lib/systemd/rfkill/*:wlan; do
            echo 0 >$filename
        done
        sleep 2
    fi
else
    echo "Warning: rfkill not found. Cannot check for Wi-Fi soft block."
fi

# Set Wi-Fi country (regulatory domain)
if command -v iw &>/dev/null; then
    echo "Setting Wi-Fi country to $WIFI_COUNTRY..."
    iw reg set "$WIFI_COUNTRY"
else
    echo "Warning: 'iw' not found, cannot set Wi-Fi country code."
fi

# Function to remove unwanted connections
cleanup_networks() {
    echo "Removing unnecessary NetworkManager connections (excluding bridges and static configurations)..."

    # List all connections and remove those that are NOT:
    # - The static ones we are configuring (static-eth0, static-wlan)
    # - Bridge and virtual networks used by Docker, virtualization, or other apps
    nmcli -t -f NAME,DEVICE con show | grep -Ev 'docker|br-|virbr|vnet|tun|tap|lo|static-eth0|static-wlan' | cut -d: -f1 | while read -r con; do
        echo "Deleting connection: $con"
        nmcli con delete "$con"
    done
}

# Function to configure a network connection
configure_network() {
    local iface="$1"
    local con_name="$2"
    local ip="$3"
    local dns="$4"
    local ssid="$5"
    local password="$6"

    # Check if the connection exists
    if nmcli con show "$con_name" &>/dev/null; then
        echo "Updating existing connection: $con_name"
        nmcli con modify "$con_name" ipv4.addresses "$ip"
        nmcli con modify "$con_name" ipv4.gateway "$GATEWAY"
        nmcli con modify "$con_name" ipv4.dns "$dns"
        nmcli con modify "$con_name" ipv4.method manual
    else
        echo "Creating new connection: $con_name"
        if [[ "$iface" == "$WLAN_IFACE" ]]; then
            nmcli con add type wifi ifname "$iface" con-name "$con_name" ssid "$ssid" ipv4.method manual \
                ipv4.addresses "$ip" \
                ipv4.gateway "$GATEWAY" \
                ipv4.dns "$dns" \
                autoconnect yes
        else
            nmcli con add type ethernet ifname "$iface" con-name "$con_name" ipv4.method manual \
                ipv4.addresses "$ip" \
                ipv4.gateway "$GATEWAY" \
                ipv4.dns "$dns" \
                autoconnect yes
        fi
    fi

    # Configure Wi-Fi security if applicable
    if [[ "$iface" == "wlan0" && -n "$password" ]]; then
        nmcli con modify "$con_name" wifi-sec.key-mgmt wpa-psk
        nmcli con modify "$con_name" wifi-sec.psk "$password"
    fi
}

# Cleanup unwanted networks
cleanup_networks

# Configure Ethernet (eth0)
configure_network "$ETH_IFACE" "static-eth0" "$ETH0_IPS" "$ETH0_DNS"

# Configure Wi-Fi (wlan0)
configure_network "$WLAN_IFACE" "static-wlan" "$WLAN0_IPS" "$WLAN0_DNS" "$WIFI_SSID" "$WIFI_PASSWORD"

# Restart connections
echo "Restarting network connections..."
nmcli con up static-eth0
nmcli con up static-wlan

# Verify setup
echo "Final Network Configuration:"
nmcli con show
ip a

echo "Static IP setup completed successfully!"
