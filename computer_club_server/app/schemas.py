from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from models import UserRole, ComputerStatus, BookingStatus, PaymentStatus, PaymentType, PaymentMethod, TournamentStatus

# ========== USER SCHEMAS ==========
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    id: int
    role: UserRole
    balance: float
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

# ========== COMPUTER SCHEMAS ==========
class ComputerBase(BaseModel):
    name: str
    row: int
    place: int
    price_per_hour: float
    processor: Optional[str] = None
    ram: Optional[str] = None
    graphics_card: Optional[str] = None
    monitor: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None

class ComputerCreate(ComputerBase):
    pass

class ComputerUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[ComputerStatus] = None
    price_per_hour: Optional[float] = None
    notes: Optional[str] = None

class ComputerResponse(ComputerBase):
    id: int
    status: ComputerStatus
    is_active: bool
    last_maintenance: Optional[datetime] = None
    notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# ========== BOOKING SCHEMAS ==========
class BookingBase(BaseModel):
    computer_id: int
    start_time: datetime
    end_time: datetime

class BookingCreate(BookingBase):
    pass

class BookingResponse(BaseModel):
    id: int
    user_id: int
    computer_id: int
    start_time: datetime
    end_time: datetime
    status: BookingStatus
    total_price: float
    payment_status: PaymentStatus
    created_at: datetime
    computer: Optional[ComputerResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

class BookingActionResponse(BaseModel):
    success: bool
    message: str
    booking: Optional[BookingResponse] = None

# ========== PAYMENT SCHEMAS ==========
class PaymentCreate(BaseModel):
    booking_id: Optional[int] = None
    tournament_id: Optional[int] = None
    amount: float
    method: PaymentMethod
    type: PaymentType

class PaymentResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    payment_date: datetime
    type: PaymentType
    method: PaymentMethod
    status: PaymentStatus
    transaction_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# ========== TOURNAMENT SCHEMAS ==========
class TournamentBase(BaseModel):
    name: str
    game: str
    start_date: datetime
    max_participants: int
    entry_fee: float = 0
    description: Optional[str] = None
    prize_pool: Optional[float] = 0

class TournamentCreate(TournamentBase):
    pass

class TournamentResponse(TournamentBase):
    id: int
    current_participants: int
    status: TournamentStatus
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TournamentRegistrationResponse(BaseModel):
    id: int
    tournament_id: int
    registration_date: datetime
    status: str
    payment_status: PaymentStatus
    tournament: Optional[TournamentResponse] = None

# ========== SESSION SCHEMAS ==========
class SessionStartRequest(BaseModel):
    user_id: int
    computer_id: int
    booking_id: Optional[int] = None
    notes: Optional[str] = None

class SessionResponse(BaseModel):
    id: int
    user_id: int
    computer_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    total_price: Optional[float] = None
    user_name: Optional[str] = None
    computer_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# ========== HALL SCHEMAS ==========
class HallComputer(BaseModel):
    id: int
    name: str
    row: int
    place: int
    status: ComputerStatus
    status_display: str
    status_color: str
    current_user: Optional[str] = None
    price_per_hour: float

class HallRow(BaseModel):
    row_number: int
    computers: List[HallComputer]

class HallSchemeResponse(BaseModel):
    rows: List[HallRow]
    total_computers: int
    available: int
    occupied: int
    reserved: int
    maintenance: int

# ========== FINANCIAL SCHEMAS ==========
class PaymentStatsResponse(BaseModel):
    date: datetime
    total_revenue: float
    transactions_count: int
    average_check: float
    by_method: dict
    by_hour: dict

class FinancialReportResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_revenue: float
    total_bookings: int
    total_tournaments: int
    revenue_by_type: dict
    revenue_by_method: dict
    daily_revenue: dict