from asgiref.wsgi import WsgiToAsgi
from flask import Flask, render_template, request, jsonify

from services.clients import *
from services.awg import generate_keys, is_valid_key
appf = Flask(__name__)

from config.settings import IS_PROD
TEST_IP = "10.88.88.2"

@appf.route("/", methods=["GET"])
def profile():
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permisson = False
    try:
        client = ClientService.get_user_by_ip(ip)
        permisson = ClientService.get_conn_permission(client)
    finally:
        if permisson:
            return render_template("profile.html")
        else:
            return render_template("error.html", code=403, desc="Доступ запрещен")
        
@appf.route("/api/profile", methods=["GET"])
def get_profile():
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    user = ClientService.get_user_by_ip(ip)
    if not user:
        return "Доступ запрещен, если вы уверены, что это ошибка, обратитесь к администратору", 403
    user.pop("hidden_description")
    user['ip'] = ip
    print(user["created_at"])
    return jsonify(user)

@appf.route("/api/addDevice", methods=["POST"])
def add_device():
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    data = request.get_json(force=True, silent=True)
    with get_session() as session:
        user = ClientService.get_user_by_ip(ip, session=session)
        user : User
        if not user:
            return jsonify({"error": "Нет прав выполнить эту операцию"}), 403
        
        if user.max_devices <= len(user.devices):
            return jsonify({"error": "Лимит устройств превышен!"}), 400
        else:
            ip = ClientService.get_first_free_ip()
            if not ip:
                return jsonify({"error":"Не осталось свободных IP, либо непредвиденная ошибка!"}), 500
            keys = generate_keys()
            name = data['name'] if data['name'] else None
            try:
                device_id = ClientService.add_new_device(ip,user.id,keys['public_key'],user.id,name)
            except Exception as e:
                return jsonify({"error":f"Не получилось создать устройство: {e}"}), 500
        return jsonify({"private_key":f"{keys['private_key']}", "public_key": f"{keys['public_key']}"}), 200


@appf.route("/api/getDevice", methods=["POST"])
def get_device():
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
        
    data = request.get_json(force=True, silent=True)
    with get_session() as session:
        user = ClientService.get_user_by_ip(ip, session=session)
        user : User
        if not user:
            return jsonify({"error": "Нет прав выполнить эту операцию"}), 403
        
        ip = data['ip'] if data['ip'] else None
        device = ClientService.get_device_by_ip(ip, session=session)
        if not device:
            return jsonify({"error": "Зач ты пытаешься че-то достать)"}), 400
        if device.owner != user:
            return jsonify({"error": "Нет прав выполнить эту операцию"}), 403
        
        return orn_to_dict(device)

@appf.route("/api/deleteDevice", methods=["POST"])
def delete_device():
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
        
    data = request.get_json(force=True, silent=True)
    with get_session() as session:
        user = ClientService.get_user_by_ip(ip, session=session)
        user : User
        if not user:
            return jsonify({"error": "Нет прав выполнить эту операцию"}), 403
        
        target_device_ip = data['ip']
        device = ClientService.get_device_by_ip(target_device_ip, session)
        if device.owner != user:
            return jsonify({"error": "Нет прав выполнить эту операцию"}), 403
        
        try:
            ClientService.delete_device(device.id, user.id)
        except Exception as e:
            return jsonify({"error": f"Произошла ошибка: {e}"}), 500
        
    return jsonify({"message": "Успешно"})

@appf.route('/api/editDevice', methods=["POST"])
def edit_device():
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
        
        data = request.get_json(force=True, silent=True)
        with get_session() as session:
            user = ClientService.get_user_by_ip(ip, session=session)
            user: User
            if not user:
                return jsonify({"error": "Нет прав выполнить эту операцию"}), 403
            
            ip = data['ip'] if data['ip'] else None
            device = ClientService.get_device_by_ip(ip, session=session)
            name = data['name'] if data['name'] else None
            device.name = name
            status = DeviceStatus.ACTIVE if data['status'] else DeviceStatus.INACTIVE
            device.status = status
            
            return jsonify({"message":"Успешно"}),200
        
## АДМИНСКАЯ ЧАСТЬ, ПРОВЕРЯТЬ ПРАВА ##

@appf.route("/panel", methods=["GET"])
def panel():
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permission = False
    try:
        client = ClientService.get_user_by_ip(ip)
        permission = client['role'] == UserRoles.ADMIN
    finally:
        if permission:
            return render_template("panel.html")
        else:
            return render_template("error.html", code=403, desc="Доступ запрещен"), 403
        
@appf.route("/api/admin/get_clients", methods=["GET"])
def admin_get_clients():
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permission = False
    try:
        client = ClientService.get_user_by_ip(ip)
        permission = client['role'] == UserRoles.ADMIN
    finally:
        if permission:
            with get_session() as session:
                clients = crud.get_all(session, User)
                json_clients = {}
                for c in clients['User']:
                    c : User
                    json_clients[str(c.id)] = orn_to_dict(c,True)
                return jsonify(json_clients)
        else:
            return render_template("error.html", code=403, desc="Доступ запрещен"), 403

@appf.route("/api/admin/get_client/<int:user_id>", methods=["GET"])
def admin_get_client(user_id):
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permission = False
    try:
        client = ClientService.get_user_by_ip(ip)
        permission = client['role'] == UserRoles.ADMIN
    finally:
        if permission:
            with get_session() as session:
                user = ClientService.get_user_by_id(user_id)
                if user is None:
                    return jsonify({"error": "Клиент не найден"}), 404
                return jsonify(user)
        else:
            return render_template("error.html", code=403, desc="Доступ запрещен"), 403

@appf.route("/api/admin/get_client_statuses", methods=["GET"])
def admin_get_client_statuses():
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permission = False
    try:
        client = ClientService.get_user_by_ip(ip)
        permission = client['role'] == UserRoles.ADMIN
    finally:
        if permission:
            data = {}
            for value in UserStatus:
                data[f'{value.name}'] = value.value
            return jsonify(data)
        else:
            return render_template("error.html", code=403, desc="Доступ запрещен"), 403

@appf.route("/api/admin/get_client_roles", methods=["GET"])
def admin_get_client_roles():
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permission = False
    try:
        client = ClientService.get_user_by_ip(ip)
        permission = client['role'] == UserRoles.ADMIN
    finally:
        if permission:
            data = {}
            for value in UserRoles:
                data[f'{value.name}'] = value.value
            return jsonify(data)
        else:
            return render_template("error.html", code=403, desc="Доступ запрещен"), 403

@appf.route("/api/admin/get_device_statuses", methods=["GET"])
def admin_get_device_statuses():
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permission = False
    try:
        client = ClientService.get_user_by_ip(ip)
        permission = client['role'] == UserRoles.ADMIN
    finally:
        if permission:
            data = {}
            for value in DeviceStatus:
                data[f'{value.name}'] = value.value
            return jsonify(data)
        else:
            return render_template("error.html", code=403, desc="Доступ запрещен"), 403

@appf.route("/api/admin/add_client", methods=["POST"])
def admin_add_client():
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permission = False
    try:
        client = ClientService.get_user_by_ip(ip)
        permission = client['role'] == UserRoles.ADMIN
    finally:
        if permission:
            with get_session() as session:
                data = request.get_json(force=True, silent=True)
                data : dict
                
                username = data.get("username", "Новый клиент")
                if username == "":
                    username = "Новый клиент"
                    
                balance = data.get("balance", 0)
                role = data.get("role", UserRoles.REGULAR)
                status = data.get("status",UserStatus.INACTIVE)
                hidden_description = data.get("description", "")
                tariff_id = data.get("tariff")
                if tariff_id:
                    try:
                        tariff_id = int(tariff_id)
                    except:
                        return jsonify({"error": "Некорректный тариф"}), 400
                
                next_payment = data.get("next_payment")
                try:
                    role_enum = UserRoles[role]
                    status_enum = UserStatus[status]
                    next_payment = datetime.strptime(next_payment, "%Y-%m-%d")
                except Exception as e:
                    return jsonify({"error": f"Некорректные роль или статус: {e}"}), 400
                
                user = User(
                    username=username,
                    balance=balance,
                    role=role_enum,
                    status=status_enum,
                    hidden_description=hidden_description,
                    tariff_id=tariff_id,
                    next_payment = next_payment
                )
                new_user_id =  crud.add(session, user)
                return jsonify({"id": new_user_id, "message": "Клиент создан"}), 201

@appf.route("/api/admin/edit_client/<int:user_id>", methods=["POST"])
def admin_edit_client(user_id):
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permission = False
    try:
        client = ClientService.get_user_by_ip(ip)
        permission = client['role'] == UserRoles.ADMIN
    finally:
        if not permission:
            return render_template("error.html", code=403, desc="Доступ запрещен"), 403

    data = request.get_json(force=True, silent=True) or {}
    with get_session() as session:
        user: User = ClientService.get_user_by_id(user_id, session=session)
        if not user:
            return jsonify({"error": "Клиент не найден"}), 404

        try:
            if "username" in data:
                user.username = data["username"]
            if "role" in data:
                try:
                    user.role = UserRoles[data["role"]]
                except ValueError:
                    return jsonify({"error": "Некорректная роль"}), 400
            if "status" in data:
                try:
                    user.status = UserStatus[data["status"]]
                except ValueError:
                    return jsonify({"error": "Некорректный статус"}), 400
            if "hidden_description" in data:
                user.hidden_description = data["hidden_description"]
            if "tariff_id" in data:
                user.tariff_id = data["tariff_id"]
            if "balance" in data:
                user.balance = data["balance"]
            if "next_payment" in data:
                user.next_payment = datetime.strptime(data["next_payment"], "%Y-%m-%d")
        except Exception as e:
            return jsonify({"error": f"че-то не получилось: {e}"}), 400

        return jsonify({"message": "Клиент обновлён"}), 200

@appf.route("/api/admin/delete_client/<int:user_id>", methods=["DELETE"])
def admin_delete_client(user_id):
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permission = False
    try:
        actor = ClientService.get_user_by_ip(ip)
        permission = actor['role'] == UserRoles.ADMIN
    finally:
        if not permission:
            return render_template("error.html", code=403, desc="Доступ запрещен"), 403

    with get_session() as session:
        user: User = ClientService.get_user_by_id(user_id, session=session)
        if not user:
            return jsonify({"error": "Клиент не найден"}), 404
        ClientService.delete_client(user_id, actor["id"])
        return jsonify({"message": "Клиент удалён"}), 200
    
@appf.route("/api/admin/get_devices", methods=["GET"])
def admin_get_devices():
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permission = False
    try:
        client = ClientService.get_user_by_ip(ip)
        permission = client['role'] == UserRoles.ADMIN
    finally:
        if not permission:
            return render_template("error.html", code=403, desc="Доступ запрещен"), 403

    with get_session() as session:
        devices = crud.get_all(session, Device)
        json_devices = {}
        for d in devices['Device']:
            d: Device
            json_devices[str(d.id)] = orn_to_dict(d, True)
        return jsonify(json_devices)


@appf.route("/api/admin/get_device/<int:device_id>", methods=["GET"])
def admin_get_device(device_id):
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permission = False
    try:
        client = ClientService.get_user_by_ip(ip)
        permission = client['role'] == UserRoles.ADMIN
    finally:
        if not permission:
            return render_template("error.html", code=403, desc="Доступ запрещен"), 403

    with get_session() as session:
        device = ClientService.get_device_by_id(device_id, session=session)
        if not device:
            return jsonify({"error": "Устройство не найдено"}), 404
        return jsonify(orn_to_dict(device, True))


@appf.route("/api/admin/add_device", methods=["POST"])
def admin_add_device():
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permission = False
    try:
        client = ClientService.get_user_by_ip(ip)
        permission = client['role'] == UserRoles.ADMIN
    finally:
        if not permission:
            return render_template("error.html", code=403, desc="Доступ запрещен"), 403

    data = request.get_json(force=True, silent=True)
    with get_session() as session:
        name = data.get("name", "Устройство")
        user_id = data.get("user_id")
        ip = ClientService.get_first_free_ip()
        if not user_id:
            return jsonify({"error": "Не указан владелец"}), 400
        public_key = data.get("public_key", None)
        if public_key is not None:
            if not is_valid_key(public_key):
                return jsonify({"error": "Невалидный ключ"}), 400
        else:
            keys = generate_keys()
            ClientService.add_new_device(ip,user_id,keys["public_key"],client["id"], name=name)
            return jsonify({"public_key": keys['public_key'], "private_key": keys["private_key"], "ip": ip})

        new_device_id = ClientService.add_new_device(ip,user_id,public_key,client["id"], name=name)
        return jsonify({"id": new_device_id, "message": "Устройство создано"}), 201


@appf.route("/api/admin/edit_device/<int:device_id>", methods=["POST"])
def admin_edit_device(device_id):
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permission = False
    try:
        client = ClientService.get_user_by_ip(ip)
        permission = client['role'] == UserRoles.ADMIN
    finally:
        if not permission:
            return render_template("error.html", code=403, desc="Доступ запрещен"), 403

    data = request.get_json(force=True, silent=True) or {}
    with get_session() as session:
        device: Device = ClientService.get_device_by_id(device_id, session=session)
        if not device:
            return jsonify({"error": "Устройство не найдено"}), 404

        if "name" in data:
            device.name = data["name"]
        if "status" in data:
            try:
                device.status = DeviceStatus(data["status"])
            except ValueError:
                return jsonify({"error": "Некорректный статус"}), 400
        if "public_key" in data:
            if is_valid_key(data["public_key"]):
                device.public_key = data["public_key"]

        return jsonify({"message": "Устройство обновлено"}), 200


@appf.route("/api/admin/delete_device/<int:device_id>", methods=["DELETE"])
def admin_delete_device(device_id):
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permission = False
    try:
        actor = ClientService.get_user_by_ip(ip)
        permission = actor['role'] == UserRoles.ADMIN
    finally:
        if not permission:
            return render_template("error.html", code=403, desc="Доступ запрещен"), 403

    with get_session() as session:
        device: Device = ClientService.get_device_by_id(device_id, session=session)
        if not device:
            return jsonify({"error": "Устройство не найдено"}), 404
        ClientService.delete_device(device_id, actor["id"])
        return jsonify({"message": "Устройство удалено"}), 200

@appf.route("/addmoney/<int:user_id>/<int:value>") ## Я устал, сделаю просто REST
def make_user_payment(user_id,value):
    if IS_PROD:
        ip = request.remote_addr
    else:
        ip = TEST_IP
    permission = False
    try:
        actor = ClientService.get_user_by_ip(ip)
        permission = actor['role'] == UserRoles.ADMIN
    finally:
        if not permission:
            return render_template("error.html", code=403, desc="Доступ запрещен"), 403
    
    with get_session() as session:
        try:
            user: User = ClientService.get_user_by_id(user_id, session)
            ClientService.add_payment(user, value, session, f"Учтено денег админом ID {actor['id']}")
            user.balance += value
            return jsonify(orn_to_dict(user)), 200
        except Exception as e:
            return jsonify({"error": e}), 500
# class User(Base):
#     __tablename__ = "users"
#
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, nullable=False, default="Пользователь")
#     role = Column(Enum(UserRoles), nullable=False, default=UserRoles.REGULAR)
#     hidden_description = Column(String)
#     created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)
#     status = Column(
#         Enum(UserStatus),
#         nullable=False,
#         default=UserStatus.ACTIVE
#     )
#     next_payment = Column(DateTime)
#     balance = Column(Integer, nullable=False, default=0)
#
#     tariff_id = Column(Integer, ForeignKey("tariffs.id"))
#     tariff = relationship("Tariff", back_populates="users", foreign_keys=[tariff_id])
#     devices = relationship("Device",
#                            back_populates="owner",
#                            cascade="all, delete-orphan")
#
#     extra_users = Column(Integer, nullable=False, default=0)
#     extra_devices = Column(Integer, nullable=False, default=0)
#     extra_speed = Column(Integer, nullable=False, default=0)


# @appf.route("/panel")
# def panel():
#     ip = TEST_IP
#     client = get_client(ip)
#     if not client or client.get("plan") != "admin":
#         return "Доступ запрещен", 403
#
#     clients = get_clients()
#     return render_template("panel.html", clients=clients)
#
# @appf.route('/add_client', methods=['POST'])
# def api_add_client():
#     ip = TEST_IP
#     client = get_client(ip)
#     if not client or client.get("plan") != "admin":
#         return "Доступ запрещен", 403
#
#     data = request.get_json(force=True, silent=True) or {}
#     print(f"Получен запрос add_client с данными: {data}")
#
#     if not data:
#         return jsonify({"error": "Неверный формат запроса или неправильное тело"}), 400
#
#     try:
#         ip, client_data, private_key = service.add_client(data)
#         print(f"Успешно добавлен клиент с IP: {ip}")
#     except ValueError as ve:
#         print(f"ValueError: {ve}")
#         return jsonify({"error": str(ve)}), 409
#     except Exception as e:
#         print(f"Exception: {e}")
#         return jsonify({"error": str(e)}), 400
#
#     response = {
#         "client" : {ip : client_data},
#         "peer_data" : {"public_key": SERVER_PUBLIC_KEY, "endpoint": ENDPOINT}
#     }
#
#     if private_key is not None:
#         response["private_key"] = private_key
#
#     return jsonify(response)
#
# @appf.route('/delete_client', methods=['POST'])
# def api_delete_client():
#     ip = TEST_IP
#     client = get_client(ip)
#     if not client or client.get("plan") != "admin":
#         return "Доступ запрещен", 403
#
#     data = request.get_json(force=True, silent=True) or {}
#
#     if not data:
#         return jsonify({"error": "Неверный формат запроса или неправильное тело"}), 400
#
#     ip = data.get("ip")
#     if not ip:
#         return jsonify({"error": "IP is NONE"}), 400
#
#     try:
#         service.remove_client(ip)
#     except ValueError as ve:
#         return jsonify({"error": str(ve)}), 404
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400
#
#     return jsonify({"result": f"Клиент {ip} успешно удален"})
#
# @appf.route('/get_clients', methods=['GET'])
# def api_get_clients():
#     ip = TEST_IP
#     client = get_client(ip)
#     if not client or client.get("plan") != "admin":
#         return "Доступ запрещен", 403
#
#     clients = get_clients()
#     return jsonify(clients)
#
# @appf.route('/update_client', methods=['POST'])
# def api_update_client():
#     remote_ip = TEST_IP
#     client = get_client(remote_ip)
#     if not client or client.get("plan") != "admin":
#         return "Доступ запрещен", 403
#
#     data = request.get_json(force=True, silent=True) or {}
#     try:
#         ip = data.get("ip")
#         updates = data.get("updates", {})
#
#         if not ip or not isinstance(updates, dict):
#             return jsonify({"error": "Неверные данные"}), 400
#
#         service.update_client(ip,updates)
#         return jsonify({"result": f"Клиент {ip} успешно изменен", "updates": updates})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

app = WsgiToAsgi(appf)

if __name__ == "__main__":
        appf.run(host="10.88.88.1", port=5000, debug=True, use_reloader=False)
