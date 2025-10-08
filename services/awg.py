import base64, subprocess
from config.settings import INTERFACE_NAME

class AWGError(Exception):
    """Ошибка работы с AmneziaWG"""
    pass


def is_valid_key(key: str) -> bool:
    if not isinstance(key, str):
        return False
    if len(key) != 44:
        return False
    try:
        decoded = base64.b64decode(key, validate=True)
    except Exception:
        return False
    return len(decoded) == 32


def generate_keys() -> dict:
    private_key = subprocess.check_output(["awg", "genkey"], text=True).strip()
    public_key = subprocess.check_output(
        ["awg", "pubkey"], input=private_key, text=True).strip()

    return {
        "private_key": private_key,
        "public_key": public_key
    }


def add_peer(ip: str, public_key: str) -> bool:
    if not is_valid_key(public_key):
        raise ValueError("[AWG.PY | ADD_PEER] Неверный публичный ключ.")

    cmd = [
        "awg", "set", INTERFACE_NAME, "peer", public_key, "allowed-ips", f"{ip}/32"
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise AWGError(f"Ошибка при добавлении клиента в AWG: {e}")
    return True


def remove_peer(public_key: str) -> bool:
    if not is_valid_key(public_key):
        raise ValueError("[AWG.PY | REMOVE_PEER] Неверный публичный ключ.")

    cmd = [
        "awg", "set", INTERFACE_NAME, "peer", public_key, "remove"
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise AWGError(f"Ошибка при удалении клиента в AWG: {e}")
    return True
