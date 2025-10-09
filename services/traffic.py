"""
Сервис для работы с traffic control в Linux UBUNTU.
"""
import subprocess

from sqlalchemy.sql.coercions import expect

from config.settings import INTERFACE_NAME, SPEED_CEIL, IS_PROD
## from config.settings import MIRROR_INTERFACE_NAME

parent = "1:"
guaranteed_mult = 0.5

def _run(cmd):
    if IS_PROD:
        subprocess.run(cmd, shell=True, check=True)
    else:
        print(cmd)
    
## CLASS_ID любого клиента равен 1:1 + ID клиента. Такая логика будет везде.

def _setup_user_class(interface,user_id,rate):
    """
    Can be used for CHANGE class cuz its overwritting
    :param interface: awg0 | ifb0
    :param user_id: any >0
    :param rate: any
    """
    if rate < 0.002:
        rate = 0.002
    user_id = str(user_id)
    cmd = f"tc class replace dev {interface} parent {parent} classid {parent+user_id} htb rate {rate * guaranteed_mult}Mbit ceil {rate}Mbit"
    _run(cmd)
    
def setup_user_class(user_id, rate):
    """
    Can be used for CHANGE class cuz its overwritting
    :param user_id: any >0
    :param rate: any
    """
    _setup_user_class(INTERFACE_NAME, user_id, rate)
    # _setup_user_class(MIRROR_INTERFACE_NAME, user_id, rate)
    
def _setup_device_filter(interface, device_id, ip, parent_id, i_type):
    """
    Can be used for CHANGE class cuz its overwritting
    :param interface: awg0 | ifb0
    :param device_id: any > 0
    :param ip: 10.88.88.x where 1 < x < 255
    :param parent_id: any > 0
    :param i_type: dst | src
    """
    if i_type not in ["dst", "src"]:
        return Exception("Неверный тип")
    parent_id = str(parent_id)
    cmd = f"tc filter replace dev {interface} protocol ip parent 1: prio {device_id} u32 match ip {i_type} {ip} flowid {parent+parent_id}"
    _run(cmd)
    
def setup_device_filter(device_id, ip, parent_id):
    _setup_device_filter(INTERFACE_NAME, device_id, ip, parent_id, "dst")
    # _setup_device_filter(MIRROR_INTERFACE_NAME, device_id, ip, parent_id, "src")
    
def delete_user_class(user_id: str):
    """НАДО УДАЛИТЬ СНАЧАЛА ВСЕ ЗАВИСИМОСТИ!"""
    cmd = f"tc class del dev awg0 classid {parent+user_id}"
    _run(cmd)
    
def delete_device_filter(device_id):
    cmd = f"tc filter del dev awg0 parent 1: pref {device_id}"