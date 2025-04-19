import getpass
from utilities.users import get_user, generate_encrypted_password
from utilities.wpa import generate_wpa_psk


def get_config():
    hostname = (
        input("Enter hostname [pi02.linuxastra.com]: ").strip() or "pi02.linuxastra.com"
    )
    username, home_dir, ssh_dir, ssh_pub_key = get_user()

    password = getpass.getpass(f"Enter password for user {username}: ")
    password_hash = generate_encrypted_password(password)

    wifi_ssid = (
        input("Enter SSID for WIFI [JACKSON_PRIVATE_NETWORK] : ").strip()
        or "JACKSON_PRIVATE_NETWORK"
    )
    wifi_psk_input = getpass.getpass(f"Enter WPA password for {wifi_ssid}: ")
    if not (8 <= len(wifi_psk_input) <= 63):
        raise ValueError("WPA password must be between 8 and 63 characters.")

    wpa_psk = generate_wpa_psk(wifi_ssid, wifi_psk_input)
    wlan0_ips = (
        input("Enter IP addresses for wlan0 [192.168.1.3/24,10.0.0.3/24]: ").strip()
        or "192.168.1.3/24,10.0.0.3/24"
    )
    wlan0_dns = (
        input("Enter DNS servers for wlan0 [192.168.1.3,8.8.8.8]: ")
        or "192.168.1.3,8.8.8.8"
    )
    eth0_ips = (
        input("Enter IP addresses for eth0 [192.168.1.2/24,10.0.0.2/24]: ").strip()
        or "192.168.1.2/24,10.0.0.2/24"
    )
    eth0_dns = (
        input("Enter DNS servers for eth0 [192.168.1.2,8.8.8.8]: ")
        or "192.168.1.2,8.8.8.8"
    )
    gateway = input("Enter gateway [192.168.1.1]: ") or "192.168.1.1"

    return {
        "hostname": hostname,
        "new_user": username,
        "password_hash": password_hash,
        "ssh_public_key": ssh_pub_key,
        "wifi_ssid": wifi_ssid,
        "wifi_psk": wpa_psk,
        "wifi_psk_plain": wifi_psk_input,
        "wlan0_ips": wlan0_ips,
        "wlan0_dns": wlan0_dns,
        "eth0_ips": eth0_ips,
        "eth0_dns": eth0_dns,
        "gateway": gateway,
        "wifi_country": input("Enter country code for WIFI [IN]: ").strip() or "IN",
        "timezone": input("Enter timezone [Asia/Kolkata]: ").strip() or "Asia/Kolkata",
    }
