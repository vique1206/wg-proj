import os

SETTINGS_PATH = os.path.join("config", "settings.py")
DB_PATH = os.path.join("database", "vpn.db")

def create_settings():
    if not os.path.exists("config"):
        os.makedirs("config")
        print("Создана папка config")
    if not os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            f.write("""# Создан с помощью init.py
import os

IS_PROD = False
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
INTERFACE_NAME = "awg0" ## DST !!!
MIRROR_INTERFACE_NAME = "ifb0" ## SRC !!!
SPEED_CEIL = 600 ## Mbit
SUBNET_PREFIX = "10.88.88."
DATABASE_PATH = os.path.join(BASE_DIR, "database", "vpn.db")
SERVER_PUBLIC_KEY = ""
ENDPOINT = "123.231.123.231:51820"
            """)
        print(f"[+] Создан файл {SETTINGS_PATH}")
    else:
        print(f"[=] {SETTINGS_PATH} уже существует")
        
def init_db():
    from database import Base, engine
    import database.models
    if os.path.exists(DB_PATH):
        print(f"[=] База уже существует")
        return
    
    Base.metadata.create_all(engine)
    print(f"[+] База данных создана")
    
def add_plugs_into_db():
    from database import SessionLocal
    from database.models import Tariff
    session = SessionLocal()
    try:
        tariff = Tariff(id=-1, name="НЕСУЩЕСТВУЮЩИЙ", description="НЕ ИСПОЛЬЗОВАТЬ")
        session.add(tariff)
        session.commit()
        print(f"[+] Добавлен тариф -1")
    except Exception as e:
        session.rollback()
        print(f"[?] Не получилось добавить тариф -1, возможно, уже существует")
    finally:
        session.close()
        
if __name__ == "__main__":
    create_settings()
    init_db()
    add_plugs_into_db()
    print("=== ГОТОВО ===")
    
    input("\nСкебоб")