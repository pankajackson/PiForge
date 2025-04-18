import getpass
from utilities.users import get_user, generate_encrypted_password
from utilities.wpa import generate_wpa_psk


def get_config():
    username, home_dir, ssh_dir, ssh_pub_key = get_user()

    password = getpass.getpass(f"Enter password for user {username}: ")
    password_hash = generate_encrypted_password(password)

    wifi_ssid = input("Enter SSID for WIFI: ")
    wifi_psk_input = getpass.getpass(f"Enter WPA password for {wifi_ssid}: ")

    if not (8 <= len(wifi_psk_input) <= 63):
        raise ValueError("WPA password must be between 8 and 63 characters.")

    wpa_psk = generate_wpa_psk(wifi_ssid, wifi_psk_input)

    return {
        "hostname": "pi02",
        "new_user": username,
        "password_hash": password_hash,
        "ssh_public_key": ssh_pub_key,
        "wifi_ssid": wifi_ssid,
        "wifi_psk": wpa_psk,
        "wifi_country": "IN",
        "timezone": "Asia/Kolkata",
    }
