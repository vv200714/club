from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

# ========== ПЕРЕЧИСЛЕНИЯ ==========
class UserRole(str, enum.Enum):
    CLIENT = "client"
    ADMIN = "admin"
    MODERATOR = "moderator"

class ComputerStatus(str, enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"
    BROKEN = "broken"

class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"

class PaymentType(str, enum.Enum):
    BOOKING = "booking"
    TOURNAMENT = "tournament"
    BALANCE_TOP_UP = "balance_top_up"
    DEPOSIT = "deposit"

class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    ONLINE = "online"
    BALANCE = "balance"
    SBP = "sbp"

class TournamentStatus(str, enum.Enum):
    DRAFT = "draft"
    REGISTRATION = "registration"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"

# ========== МОДЕЛИ ==========
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(200), nullable=False)
    phone = Column(String(20))
    role = Column(Enum(UserRole), default=UserRole.CLIENT)
    balance = Column(Float, default=0.0)
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime)
    
    # Relationships
    bookings = relationship("Booking", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    tournament_registrations = relationship("TournamentRegistration", back_populates="user")
    sessions = relationship("Session", back_populates="user")

class Computer(Base):
    __tablename__ = "computers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    row = Column(Integer, nullable=False)  # Ряд
    place = Column(Integer, nullable=False)  # Место
    status = Column(Enum(ComputerStatus), default=ComputerStatus.AVAILABLE)
    price_per_hour = Column(Float, nullable=False)
    
    # Характеристики
    processor = Column(String(100))
    ram = Column(String(50))
    graphics_card = Column(String(100))
    monitor = Column(String(100))
    periphery = Column(String(200))
    
    # Координаты на схеме
    position_x = Column(Integer)
    position_y = Column(Integer)
    
    last_maintenance = Column(DateTime)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    bookings = relationship("Booking", back_populates="computer")
    sessions = relationship("Session", back_populates="computer")

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    computer_id = Column(Integer, ForeignKey("computers.id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    total_price = Column(Float)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    created_at = Column(DateTime, server_default=func.now())
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(String(500))
    
    # Relationships
    user = relationship("User", back_populates="bookings")
    computer = relationship("Computer", back_populates="bookings")
    payment = relationship("Payment", back_populates="booking", uselist=False)
    session = relationship("Session", back_populates="booking", uselist=False)

class Tournament(Base):
    __tablename__ = "tournaments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    game = Column(String(100), nullable=False)
    game_type = Column(String(50))  # CS:GO, Dota 2, etc
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    registration_end_date = Column(DateTime)
    max_participants = Column(Integer)
    min_participants = Column(Integer)
    current_participants = Column(Integer, default=0)
    entry_fee = Column(Float, default=0)
    prize_pool = Column(Float, default=0)
    status = Column(Enum(TournamentStatus), default=TournamentStatus.DRAFT)
    format = Column(String(50))  # 1x1, 5x5
    rules = Column(Text)
    image_url = Column(String(500))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    registrations = relationship("TournamentRegistration", back_populates="tournament")

class TournamentRegistration(Base):
    __tablename__ = "tournament_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tournament_id = Column(Integer, ForeignKey("tournaments.id"))
    registration_date = Column(DateTime, server_default=func.now())
    status = Column(String(50), default="confirmed")  # confirmed, cancelled, disqualified
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    team_name = Column(String(100))
    final_place = Column(Integer)
    
    # Relationships
    user = relationship("User", back_populates="tournament_registrations")
    tournament = relationship("Tournament", back_populates="registrations")
    payment = relationship("Payment", back_populates="tournament_registration")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, server_default=func.now())
    type = Column(Enum(PaymentType), nullable=False)
    method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Связанные сущности
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=True)
    tournament_registration_id = Column(Integer, ForeignKey("tournament_registrations.id"), nullable=True)
    
    # Для онлайн платежей
    transaction_id = Column(String(200))
    payment_details = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    booking = relationship("Booking", back_populates="payment")
    tournament_registration = relationship("TournamentRegistration", back_populates="payment")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    computer_id = Column(Integer, ForeignKey("computers.id"))
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    total_price = Column(Float)
    started_by_admin = Column(String(100))
    notes = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    computer = relationship("Computer", back_populates="sessions")
    booking = relationship("Booking", back_populates="session")