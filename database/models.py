import enum
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, Float
from datetime import datetime, timezone, timedelta

from services.awg import is_valid_key


def now_utc():
    return datetime.now(timezone.utc)

class UserStatus(str, enum.Enum):
    """
    active - нет проблем, скорость тарифа\n
    restricted - оплата просрочена, скорость ограничена до 1мбит\n
    blocked - месяц просрочки, скорость урезается до 0.5мбит, все дочерние отключаются(status = offline)\n
    inactive - нет доступа к туннелю
    """
    ACTIVE = "active"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"
    INACTIVE = "inactive"
    
class DeviceStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    
class UserRoles(str, enum.Enum):
    ADMIN = "admin"
    REGULAR = "regular"
    
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, default="Пользователь")
    role = Column(Enum(UserRoles), nullable=False,default=UserRoles.REGULAR)
    hidden_description = Column(String)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    status = Column(
        Enum(UserStatus),
        nullable=False,
        default=UserStatus.ACTIVE
    )
    next_payment = Column(DateTime)
    balance = Column(Integer, nullable=False, default=0)
    
    tariff_id = Column(Integer, ForeignKey("tariffs.id"), default=-1)
    tariff = relationship("Tariff", back_populates="users", foreign_keys=[tariff_id])
    devices = relationship("Device",
                           back_populates="owner",
                           cascade="all, delete-orphan")
    
    extra_users = Column(Integer, nullable=False, default=0)
    extra_devices = Column(Integer, nullable=False, default=0)
    extra_speed = Column(Integer, nullable=False, default=0)
    
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    parent = relationship("User", remote_side=[id], back_populates="children", foreign_keys=[parent_id])
    children = relationship("User", back_populates="parent", cascade="all, delete-orphan")
    
    payments = relationship("Payment", back_populates="user")

    _tc_class_maked = Column(Boolean, nullable=False, default=False)
    _tc_speed = Column(Integer, nullable=False, default=0) ## NO CHANGE WITHOUT TC BILLING
    _pending_delete = Column(Boolean, nullable=False, default=False)
    
    @property
    def max_children(self):
        """
        Возвращает макс.кол-во дочерних пользователей.
        :return: int [-1, +inf]
        """
        return getattr(self.tariff, "users_count",1) + self.extra_users - 1
    
    @property
    def max_devices(self):
        """
        Возвращает макс.кол-во устройств пользователя.
        :return: int [-1, +inf]
        """
        return getattr(self.tariff, "devices_count",1) + self.extra_devices

    @property
    def effective_speed(self) -> int:
        """
        Возвращает скорость, который действительно у пользователя.
        """
        tariff_speed = self.tariff.speed if self.tariff else 0
        return tariff_speed + self.extra_speed
    
class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False, default="Устройство")
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    status = Column(
        Enum(DeviceStatus),
        nullable=False,
        default=DeviceStatus.ACTIVE
    )
    # Ссылка на владельца
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User",
                         back_populates="devices",
                         passive_deletes=True,
                         foreign_keys=[user_id])
    
    public_key = Column(String, nullable=False)
    
    _awg_known_key = Column(String, nullable=False, default="") ## NO CHANGE WITHOUT AWG BILLING
    _awg_peered = Column(Boolean, nullable=False, default=False) ## NO CHANGE WITHOUT AWG BILLING
    _tc_confirmed = Column(Boolean, nullable=False, default=False) ## NO CHANGE WITHOUT AWG BILLING
    _pending_delete = Column(Boolean, nullable=False, default=False)
    
class Tariff(Base):
    __tablename__ = "tariffs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="Тариф")
    description = Column(String)
    speed = Column(Integer, nullable=False, default=20)
    devices_count = Column(Integer, nullable=False, default=1)
    users_count = Column(Integer, nullable=False, default=1)
    show = Column(Boolean, nullable=False, default=False)
    payment = Column(Integer, nullable=False, default=0)
    users = relationship("User", back_populates="tariff")
    
class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, default=0)
    desc = Column(String)
    date = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    
    user = relationship("User", back_populates="payments")
    
