
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import schemas
import models
import auth
from database import get_db

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# ========== УПРАВЛЕНИЕ СЕССИЯМИ ==========

@router.post("/sessions/start", response_model=schemas.SessionResponse)
def start_session(
    session_data: schemas.SessionStartRequest,
    admin_user: models.User = Depends(auth.get_admin_user),
    db: Session = Depends(get_db)
):
    """Запустить сессию для пользователя (только админ)"""
    
    # Проверяем компьютер
    computer = db.query(models.Computer).filter(
        models.Computer.id == session_data.computer_id,
        models.Computer.is_active == True
    ).first()
    
    if not computer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Computer not found"
        )
    
    if computer.status != models.ComputerStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Computer is {computer.status}"
        )
    
    # Проверяем пользователя
    user = db.query(models.User).filter(models.User.id == session_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Создаем сессию
    session = models.Session(
        user_id=session_data.user_id,
        computer_id=session_data.computer_id,
        booking_id=session_data.booking_id,
        start_time=datetime.now(),
        status=models.SessionStatus.ACTIVE,
        started_by_admin=admin_user.full_name,
        notes=session_data.notes
    )
    
    db.add(session)
    
    # Обновляем статус компьютера
    computer.status = models.ComputerStatus.OCCUPIED
    
    db.commit()
    db.refresh(session)
    
    return session

@router.post("/sessions/{session_id}/end")
def end_session(
    session_id: int,
    admin_user: models.User = Depends(auth.get_admin_user),
    db: Session = Depends(get_db)
):
    """Завершить сессию (только админ)"""
    
    session = db.query(models.Session).filter(
        models.Session.id == session_id,
        models.Session.status == models.SessionStatus.ACTIVE
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active session not found"
        )
    
    # Завершаем сессию
    session.end_time = datetime.now()
    session.status = models.SessionStatus.COMPLETED
    
    # Рассчитываем стоимость
    hours = (session.end_time - session.start_time).total_seconds() / 3600
    computer = db.query(models.Computer).filter(models.Computer.id == session.computer_id).first()
    session.total_price = round(hours * computer.price_per_hour, 2)
    
    # Освобождаем компьютер
    computer.status = models.ComputerStatus.AVAILABLE
    
    # Если есть бронирование, обновляем его
    if session.booking_id:
        booking = db.query(models.Booking).filter(models.Booking.id == session.booking_id).first()
        if booking:
            booking.status = models.BookingStatus.COMPLETED
    
    db.commit()
    
    return {
        "success": True,
        "message": "Session ended",
        "total_price": session.total_price,
        "duration_hours": round(hours, 2)
    }

@router.get("/sessions/active", response_model=List[schemas.SessionResponse])
def get_active_sessions(
    admin_user: models.User = Depends(auth.get_admin_user),
    db: Session = Depends(get_db)
):
    """Получить все активные сессии (только админ)"""
    
    sessions = db.query(models.Session).filter(
        models.Session.status == models.SessionStatus.ACTIVE
    ).all()
    
    # Добавляем имена пользователей и компьютеров
    result = []
    for session in sessions:
        user = db.query(models.User).filter(models.User.id == session.user_id).first()
        computer = db.query(models.Computer).filter(models.Computer.id == session.computer_id).first()
        
        session_dict = {
            "id": session.id,
            "user_id": session.user_id,
            "computer_id": session.computer_id,
            "start_time": session.start_time,
            "status": session.status,
            "user_name": user.full_name if user else None,
            "computer_name": computer.name if computer else None
        }
        result.append(session_dict)
    
    return result

# ========== УПРАВЛЕНИЕ КОМПЬЮТЕРАМИ ==========

@router.put("/computers/{computer_id}/status")
def change_computer_status(
    computer_id: int,
    status: models.ComputerStatus,
    reason: str = None,
    admin_user: models.User = Depends(auth.get_admin_user),
    db: Session = Depends(get_db)
):
    """Изменить статус компьютера (только админ)"""
    
    computer = db.query(models.Computer).filter(models.Computer.id == computer_id).first()
    if not computer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Computer not found"
        )
    
    old_status = computer.status
    computer.status = status
    computer.notes = f"[{datetime.now()}] Status changed from {old_status} to {status}. Reason: {reason}"
    computer.last_maintenance = datetime.now() if status == models.ComputerStatus.MAINTENANCE else computer.last_maintenance
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Computer status changed to {status}"
    }

@router.post("/computers", response_model=schemas.ComputerResponse)
def create_computer(
    computer_data: schemas.ComputerCreate,
    admin_user: models.User = Depends(auth.get_admin_user),
    db: Session = Depends(get_db)
):
    """Создать новый компьютер (только админ)"""
    
    computer = models.Computer(**computer_data.dict())
    db.add(computer)
    db.commit()
    db.refresh(computer)
    
    return computer

# ========== ФИНАНСОВАЯ АНАЛИТИКА ==========

@router.get("/finance/daily/{date}")
def get_daily_finance(
    date: datetime,
    admin_user: models.User = Depends(auth.get_admin_user),
    db: Session = Depends(get_db)
):
    """Получить финансовую статистику за день (только админ)"""
    
    start_of_day = datetime(date.year, date.month, date.day)
    end_of_day = start_of_day + timedelta(days=1)
    
    # Получаем все платежи за день
    payments = db.query(models.Payment).filter(
        models.Payment.payment_date >= start_of_day,
        models.Payment.payment_date < end_of_day,
        models.Payment.status == models.PaymentStatus.PAID
    ).all()
    
    # Статистика по методам оплаты
    by_method = {}
    for method in models.PaymentMethod:
        total = sum(p.amount for p in payments if p.method == method)
        if total > 0:
            by_method[method.value] = total
    
    # По часам
    by_hour = {}
    for hour in range(24):
        hour_start = start_of_day + timedelta(hours=hour)
        hour_end = hour_start + timedelta(hours=1)
        hour_payments = [p for p in payments if hour_start <= p.payment_date < hour_end]
        by_hour[hour] = sum(p.amount for p in hour_payments)
    
    return {
        "date": date,
        "total_revenue": sum(p.amount for p in payments),
        "transactions_count": len(payments),
        "average_check": sum(p.amount for p in payments) / len(payments) if payments else 0,
        "by_method": by_method,
        "by_hour": by_hour
    }

@router.get("/finance/report")
def get_financial_report(
    start_date: datetime,
    end_date: datetime,
    admin_user: models.User = Depends(auth.get_admin_user),
    db: Session = Depends(get_db)
):
    """Получить финансовый отчет за период (только админ)"""
    
    # Платежи за период
    payments = db.query(models.Payment).filter(
        models.Payment.payment_date >= start_date,
        models.Payment.payment_date <= end_date,
        models.Payment.status == models.PaymentStatus.PAID
    ).all()
    
    # По типам платежей
    by_type = {}
    for p_type in models.PaymentType:
        total = sum(p.amount for p in payments if p.type == p_type)
        if total > 0:
            by_type[p_type.value] = total
    
    # По методам оплаты
    by_method = {}
    for method in models.PaymentMethod:
        total = sum(p.amount for p in payments if p.method == method)
        if total > 0:
            by_method[method.value] = total
    
    # По дням
    daily = {}
    current = start_date.date()
    while current <= end_date.date():
        day_start = datetime.combine(current, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        day_payments = [p for p in payments if day_start <= p.payment_date < day_end]
        daily[current.isoformat()] = sum(p.amount for p in day_payments)
        current += timedelta(days=1)
    
    # Количество бронирований и турниров
    bookings_count = db.query(models.Booking).filter(
        models.Booking.created_at >= start_date,
        models.Booking.created_at <= end_date
    ).count()
    
    tournaments_count = db.query(models.Tournament).filter(
        models.Tournament.created_at >= start_date,
        models.Tournament.created_at <= end_date
    ).count()
    
    return {
        "period_start": start_date,
        "period_end": end_date,
        "total_revenue": sum(p.amount for p in payments),
        "total_bookings": bookings_count,
        "total_tournaments": tournaments_count,
        "revenue_by_type": by_type,
        "revenue_by_method": by_method,
        "daily_revenue": daily
    }