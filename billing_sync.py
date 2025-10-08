import asyncio
from datetime import datetime, timezone
from database import get_session, crud, models
from services.awg import add_peer

CLEANUP_SYNC_INTERVAL = 120
TECH_SYNC_INTERVAL = 60
FIN_SYNC_INTERVAL = 30


def _delete_device(session, device):
    try:
        import services.awg as awg
        import services.traffic as tc
        awg.remove_peer(device.public_key)
        tc.delete_device_filter(device.id)
        crud._delete(session, device)
        print(f"[CLEANUP] Устройство {device.id} удалено")
    except Exception as e:
        print(f"[CLEANUP] Ошибка при удалении устройства {device.id}: {e}")

## В ПЕРВУЮ ОЧЕРЕДЬ
async def cleanup():
    while True:
        with get_session() as session:
            users = crud.get_filtered(session, models.User, pending_delete=True)
            devices = crud.get_filtered(session, models.Device, pending_delete=True)
            
            for device in devices:
                _delete_device(session, device)
                
            for user in users:
                try:
                    import services.traffic as tc
                    for userDevice in user.devices:
                        _delete_device(session, userDevice)
                    tc.delete_user_class(user.id)
                    crud._delete(session,user)
                    print(f"[CLEANUP] Пользователь {user.id} удален")
                except Exception as e:
                    print(f"[CLEANUP] Ошибка при удалении пользователя {user.id}: {e}")
        await asyncio.sleep(300)
        
def device_awg_sync(user: models.User):
    import services.awg as awg
    try:
        for device in user.devices:
            if device.status == models.DeviceStatus.ACTIVE:
                if device._awg_peered:
                    if device.public_key == device._awg_known_key:
                        pass
                    else:
                        awg.remove_peer(device._awg_known_key)
                        device._awg_peered = False
                        if awg.is_valid_key(device.public_key):
                            awg.add_peer(device.public_key)
                            device._awg_known_key = device.public_key
                            device._awg_peered = True
                        else:
                            pass
                else:
                    if awg.is_valid_key(device.public_key):
                        add_peer(device.public_key)
                        device._awg_known_key = device.public_key
                        device._awg_peered = True
            else:
                if device._awg_peered:
                    awg.remove_peer(device.public_key)
                    device._awg_peered = False
    except Exception as e:
        print(f"[DEVICE_AWG_SYNC] Что-то пошло не так: {e}")
        
def _set_user_class(user: models.User, rate: int):
    try:
        rate = str(rate)
    except:
        raise TypeError("ЧИСЛА МНЕ ДАЙ")
    import services.traffic as tc
    tc.setup_user_class(user.id, rate)
    user._tc_speed = rate
    user._tc_class_maked = True
    
def user_class_sync(user: models.User):
    match user.status:
        case models.UserStatus.ACTIVE:
            if user._tc_speed != user.effective_speed:
                _set_user_class(user, user.effective_speed)
        case models.UserStatus.RESTRICTED:
            if user._tc_speed != 1:
                _set_user_class(user, 1)
        case models.UserStatus.BLOCKED:
            if user._tc_speed != 0:
                _set_user_class(user, 0)
        case models.UserStatus.INACTIVE: ## Разница с blocked та, что blocked - санкция, а INACTIVE - просто выключен
            if user._tc_speed != 0:
                _set_user_class(user, 0)

def _set_device_filter(device: models.Device):
    import services.traffic as tc
    tc.setup_device_filter(str(device.id), device.ip, str(device.owner.id))
    device._tc_confirmed = True
    
def devices_filter_sync(user: models.User):
    for device in user.devices:
        if not device._tc_confirmed:
            _set_device_filter(device)
        
async def tech_sync():
    while True:
        with get_session() as session:
            users = crud.get_all(session, models.User)["User"]
            for user in users:
                user: models.User
                device_awg_sync(user)
                user_class_sync(user)
                devices_filter_sync(user)
                
        await asyncio.sleep(TECH_SYNC_INTERVAL)

def normalize_date(dt: datetime):
    dt = dt.replace(hour=0,minute=0,second=0,microsecond=0)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

async def fin_sync():
    while True:
        today = normalize_date(datetime.now(timezone.utc))
        with get_session() as session:
            users = crud.get_all(session, models.User)["User"]
            for user in users:
                if user.next_payment:
                    user_date = normalize_date(user.next_payment)
                    if user_date <= today:
                        user.balance -= user.tariff.payment if user.tariff else 0 ## Чтоб не возникало багов
                else:
                    user.balance -= user.tariff.payment if user.tariff else 0
                user.next_payment = today
                if user.balance < -user.tariff.payment if user.tariff else -50:
                    user.status = models.UserStatus.BLOCKED
                elif user.balance < 0:
                    user.status = models.UserStatus.RESTRICTED
                else:
                    user.status = models.UserStatus.ACTIVE
        await asyncio.sleep(FIN_SYNC_INTERVAL)
        
async def main():
    await asyncio.gather(
        cleanup(),
        tech_sync(),
        fin_sync()
    )
if __name__ == "__main__":
    asyncio.run(main())