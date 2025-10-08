#!/usr/bin/env python3

from services.clients import get_clients
from services.awg import add_peer

def sync():
        clients = get_clients()
        for ip, client in clients.items():
                if client.get("status"):
                        try:
                                add_peer(ip)
                                print(f"[SYNC] Клиент {ip} добавлен в peers.")
                        except Exception as e:
                                print(f"[SYNC] Ошибка для {ip}: {e}")
                else:
                        print(f"[SYNC] Клиент {ip} пропущен: неактивен")
if __name__ == "__main__":
        sync()
