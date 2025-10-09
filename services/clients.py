"""
Работа с БАЗОЙ ДАННЫХ
"""
import database.crud
from database import get_session, crud
from database.models import *
from utils.utils import orn_to_dict
from config.settings import SUBNET_PREFIX

class NotFoundError(Exception):
    pass

class ClientService:
    
    @staticmethod
    def _get_user(session, user_id) -> User:
        user = crud.get_by_id(session, User, user_id)
        return user
    
    @staticmethod
    def _get_device(session, device_id: int = None, ip: str = None):
        """
        Универсальный поиск устройство по ID ИЛИ IP.
        Нужно передать хотя бы один параметр
        :param session: SQLAlchemy session
        :param device_id: ID устройства
        :param ip: IP устройства
        :return: obj Device
        """
        query = session.query(Device)
        if device_id:
            device = query.filter(Device.id == device_id).first()
        elif ip:
            device = query.filter(Device.ip == ip).first()
        else:
            raise ValueError("Некорректные device_id или ip")

        return device
            
    @staticmethod
    def get_user_by_ip(ip: str, session=None, as_dict=False) -> dict | User | None:
        """
        Возвращает пользователя по IP
        ВНИМАНИЕ: Если не передать сессию, то всегда возвращается dict, т.к иначе объект будет detached!
        :param ip: str: Само IP
        :param session: SQLAlchemy session
        :param as_dict: bool: выдать dict'ом или ORM-объектом
        :return: dict | Device
        """
        if session:
            device = ClientService._get_device(session, ip=ip)
            if not device: return None
            return orn_to_dict(device.owner, include_relationships=True) if as_dict else device.owner
        else:
            with get_session() as session:
                return ClientService.get_user_by_ip(ip, session=session, as_dict=True)
        
    @staticmethod
    def get_device_by_ip(ip: str, session=None, as_dict=False) -> dict | Device | None:
        """
        Возвращает устройство по IP\n
        ВНИМАНИЕ: Если не передать сессию, то всегда возвращается dict, т.к иначе объект будет detached!
        :param ip: str: Само IP
        :param session: SQLAlchemy session
        :param as_dict: bool: выдать dict'ом или ORM-объектом
        :return: dict | Device
        """
        if session:
            device = ClientService._get_device(session,ip=ip)
            if not device: return None
            return orn_to_dict(device, include_relationships=True) if as_dict else device
        else:
            with get_session() as session:
                return ClientService.get_device_by_ip(ip, session, as_dict=True)
    
    @staticmethod
    def get_device_by_id(device_id: int, session=None, as_dict=False) -> dict | Device | None:
        if session:
            device = ClientService._get_device(session, device_id)
            if not device: return None
            return orn_to_dict(device, include_relationships=True) if as_dict else device
        else:
            with get_session() as session:
                return ClientService.get_device_by_id(device_id, session=session, as_dict=True)
    
    @staticmethod
    def get_user_by_id(user_id: int, session=None, as_dict=False) -> dict | User | None:
        if session:
            user = ClientService._get_user(session,user_id)
            if not user: return None
            return orn_to_dict(user, include_relationships=True) if as_dict else user
        else:
            with get_session() as session:
                return ClientService.get_user_by_id(user_id, session=session, as_dict=True)
        
    @staticmethod
    def add_new_client(username: str, parent_id: int = None) -> int:
        """
        Добавляет пользователя и возвращает его ID
        :param username: имя пользователя
        :param parent_id: ID родителя(если есть)
        :return: int ID нового пользователя
        """
        with get_session() as session:
            user = User(username=username, parent_id=parent_id)
            return crud.add(session, user)
        
    @staticmethod
    def delete_client(user_id: int, actor_id: int):
        with get_session() as session:
            user = ClientService._get_user(session, user_id)
            if not user:
                raise NotFoundError(f"Пользователь {user_id} не найден")
            crud.mark_for_delete(session, user)
    
    @staticmethod
    def add_new_device(ip: str, user_id: int, public_key: str, actor_id: int, name=None) -> int:
        with get_session() as session:
            actor = ClientService._get_user(session, actor_id)
            device = Device(
                ip=ip,
                name=name,
                user_id=user_id,
                public_key=public_key
            )
            return crud.add(session, device)
        
    @staticmethod
    def delete_device(device_id, actor_id: int):
        with get_session() as session:
            device = ClientService._get_device(session,device_id=device_id)
            if not device:
                raise NotFoundError(f"Устройство {device_id} не найдено")
            crud.mark_for_delete(session, device)
        pass
    
    @staticmethod
    def add_new_tariff():
        pass
    
    @staticmethod
    def delete_tariff():
        pass
    
    @staticmethod
    def get_tariff():
        pass
    
    @staticmethod
    def set_tariff_to_user():
        # Тут, наверное, надо сделать логику по пересчету устройств и детей
        pass
    
    @staticmethod
    def get_conn_permission(client: dict) -> bool:
        if not client:
            return False
        blocked_values = (
            UserStatus.BLOCKED,
            UserStatus.INACTIVE
        )
        if client.get("status") in blocked_values:
            return False
        return True
    
    @staticmethod
    def get_busy_ips(session=None):
        if not session:
            with get_session() as session:
                return ClientService.get_busy_ips(session)
        devices = crud.get_all(session, Device)
        return [device.ip for device in devices['Device']]
        
    @staticmethod
    def get_free_ips() -> list:
        busy_ips = ClientService.get_busy_ips()
        free_ips = []
        for i in range(2,255):
            ip = SUBNET_PREFIX+str(i)
            if ip not in busy_ips:
                free_ips.append(ip)
        return free_ips
    
    @staticmethod
    def get_first_free_ip() -> str | None:
        busy_ips = ClientService.get_busy_ips()
        for i in range(2,255):
            ip = SUBNET_PREFIX+str(i)
            if ip not in busy_ips:
                return ip
        return None
    
    @staticmethod
    def add_payment(user: User, amount:int, session=None, desc: str = ""):
        if session is None:
            with get_session() as session:
                return ClientService.add_payment(user, amount, session, desc)
        else:
            payment = Payment(
                user_id = user.id,
                amount = amount,
                desc = desc,
                date = now_utc()
            )
            crud.add(session,payment)
# import json
# from config.settings import CLIENTS_JSON_PATH, SUBNET_PREFIX
# from datetime import datetime, timedelta
#
# class ClientDBError(Exception):
#     pass
#
# def _load_data():
#     try:
#         with open(CLIENTS_JSON_PATH, "r", encoding="utf-8") as f:
#             return json.load(f)
#     except FileNotFoundError:
#         return {"clients": {}, "plans": {}}
#     except json.JSONDecodeError:
#         raise ClientDBError("Файл поврежден или имеет неверный формат.")
#
# def _save_data(data):
#     with _lock:
#         with open(CLIENTS_JSON_PATH, "w", encoding="utf-8") as f:
#             json.dump(data, f, ensure_ascii=False, indent=4)
#
# def get_time_with_delta(days_delta):
#     now = datetime.now()
#     later = (now + timedelta(days=days_delta)).replace(microsecond=0).isoformat()
#     return later
#
# def get_clients():
#     data = _load_data()
#     return data.get("clients", {})
#
# def get_client(ip):
#     return get_clients().get(ip)
#
# def get_plans():
#     data = _load_data()
#     return data.get("plans", {})
#
# def update_client(ip, updates):
#     if not isinstance(updates, dict):
#         raise TypeError("Поле updates должно быть словарем.")
#
#     with _lock:
#         data = _load_data()
#         clients = data.get("clients", {})
#         if not clients:
#             raise ValueError(f"Ошибка загрузки клиентов.")
#         if ip not in clients:
#             raise ValueError(f"Клиент с IP {ip} не найден.")
#         clients[ip].update(updates)
#         _save_data(data)
#
# def add_client(client_data, ip_suffix = None) -> str:
#     if not isinstance(client_data, dict):
#         raise TypeError("client_data должен быть словарем.")
#     with _lock:
#         data = _load_data()
#         clients = data.get("clients",{})
#         if ip_suffix is not None:
#             if not isinstance(ip_suffix, int):
#                 raise ValueError(f"IP_SUFFIX должен быть числом.")
#             if not (2 <= ip_suffix <= 254):
#                 raise ValueError(f"IP {SUBNET_PREFIX+str(ip_suffix)} не может быть использован.")
#             ip = SUBNET_PREFIX + str(ip_suffix)
#             if ip in clients:
#                 raise ValueError(f"Клиент с IP {ip} уже существует.")
#         else:
#             for i in range(2,255):
#                 candidate_ip = SUBNET_PREFIX+str(i)
#                 if candidate_ip not in clients:
#                     ip = candidate_ip
#                     break
#             else:
#                 raise RuntimeError("Нет свободных IP для выдачи.")
#
#         client_data.setdefault("name", "UserWithNoName")
#         client_data.setdefault("created", get_time_with_delta(0))
#         client_data.setdefault("next_payment", get_time_with_delta(30))
#         client_data.setdefault("status", False)
#
#         clients[ip] = client_data
#         data["clients"] = clients
#         _save_data(data)
#         return ip
#
#
# def remove_client(ip: str) -> bool:
#     # Проверка, чтоб не работать по пустяку.
#     with _lock:
#         client = get_client(ip)
#         if not client:
#             raise ValueError(f"Клиент {ip} не найден.")
#
#         data = _load_data()
#         clients = data.get("clients", {})
#         clients.pop(ip)
#         data["clients"] = clients
#         _save_data(data)
#         return True
#
# def set_activated_client(ip: str) -> bool:
#     update_client(ip, {"status": True})
#     return True
#
#
# def set_deactivated_client(ip):
#     update_client(ip, {"status": False})
#     return True
