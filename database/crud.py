from .models import User, Tariff, Device

def get_by_id(session, model, id: int):
    """
    Возвращает объект базы по Объекту+ID
    :param session: SQLAlchemy session
    :param model: тип данных: User, Tariff, Deivce
    :param id: искомый ID
    :return: искомый объект под ID = user_id
    """
    return session.query(model).filter(model.id == id).first()

def get_all(session, *args) -> dict:
    """
    :param session:
    :param args: тип данных: User, Tariff, Device
    Возвращает список кортежей: {'User' : {...}, 'Device' : {...}, ...}
    :return: list of lists
    """
    if args is None:
        return {}
    result = {}
    for model in args:
        result[model.__name__] = session.query(model).all()
    return result

def get_filtered(session, model, **filters) -> list:
    """
    Возвращает данные, соответствующие фильтру
    :param session: SQLAlchemy session
    :param model: obj: User, Tariff, Device, ...
    :param filters: например: "username"="Vlad"
    :return: orm
    """
    query = session.query(model)
    for attr, value in filters.items():
        if hasattr(model, attr):
            query = query.filter(getattr(model, attr) == value)
        else:
            raise ValueError(f"{model.__name__} не имеет атрибута '{attr}'")
    return query.all()

def add(session, obj) -> int:
    """
    Добавляет объект в базу
    :param session: SQLAlchemy session
    :param obj: User, Device, Traffic, ...
    """
    session.add(obj)
    session.flush() # ОБЯЗАТЕЛЬНО для получения ID
    return obj.id
    
def _delete(session, obj):
    """
    Удаляет объект из базы
    :param session: SQLAlchemy session
    :param obj: ORM объект User, Device, Traffic, ...
    """
    session.delete(obj)
    
def mark_for_delete(session, obj):
    if hasattr(obj, "_pending_delete"):
        obj._pending_delete = True
    else:
        raise ValueError(f"Модель {obj.__class__.__name__} не поддерживает отложенное удаление.")