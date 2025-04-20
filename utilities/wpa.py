import hashlib
import binascii


def generate_wpa_psk(ssid: str, passphrase: str) -> str:
    psk = hashlib.pbkdf2_hmac(
        "sha1",  # WPA2 uses HMAC-SHA1
        passphrase.encode("utf-8"),
        ssid.encode("utf-8"),
        4096,
        32,  # 256-bit key
    )
    return binascii.hexlify(psk).decode("utf-8")
