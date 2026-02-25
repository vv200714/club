from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import schemas
import models
import auth
from database import get_db
from services.payment_service import PaymentService
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])

@router.get("/", response_model=List[schemas.BookingResponse])
def get_user_bookings(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить все бронирования текущего пользователя"""
    bookings = db.query(models.Booking).filter(
        models.Booking.user_id == current_user.id
    ).order_by(models.Booking.start_time.desc()).all()
    
    return bookings

@router.get("/active", response_model=List[schemas.BookingResponse])
def get_active_bookings(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить активные бронирования"""
    bookings = db.query(models.Booking).filter(
        models.Booking.user_id == current_user.id,
        models.Booking.status.in_([models.BookingStatus.CONFIRMED, models.BookingStatus.ACTIVE])
    ).all()
    
    return bookings

@router.post("/", response_model=schemas.BookingActionResponse)
def create_booking(
    booking_data: schemas.BookingCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создать новое бронирование"""
    
    # Проверяем существование компьютера
    computer = db.query(models.Computer).filter(
        models.Computer.id == booking_data.computer_id,
        models.Computer.is_active == True
    ).first()
    
    if not computer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Computer not found"
        )
    
    # Проверяем доступность компьютера на выбранное время
    existing_booking = db.query(models.Booking).filter(
        models.Booking.computer_id == booking_data.computer_id,
        models.Booking.status.in_([
            models.BookingStatus.CONFIRMED, 
            models.BookingStatus.ACTIVE,
            models.BookingStatus.PENDING
        ]),
        models.Booking.start_time < booking_data.end_time,
        models.Booking.end_time > booking_data.start_time
    ).first()
    
    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Computer is not available at this time"
        )
    
    # Рассчитываем стоимость
    hours = (booking_data.end_time - booking_data.start_time).total_seconds() / 3600
    total_price = round(hours * computer.price_per_hour, 2)
    
    # Создаем бронирование
    booking = models.Booking(
        user_id=current_user.id,
        computer_id=booking_data.computer_id,
        start_time=booking_data.start_time,
        end_time=booking_data.end_time,
        total_price=total_price,
        status=models.BookingStatus.PENDING,
        payment_status=models.PaymentStatus.PENDING
    )
    
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    # Если цена 0, сразу подтверждаем
    if total_price == 0:
        booking.status = models.BookingStatus.CONFIRMED
        booking.payment_status = models.PaymentStatus.PAID
        db.commit()
    
    return schemas.BookingActionResponse(
        success=True,
        message="Booking created successfully",
        booking=booking
    )

@router.post("/{booking_id}/pay", response_model=schemas.BookingActionResponse)
def pay_booking(
    booking_id: int,
    payment_method: schemas.PaymentMethod,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db),
    payment_service: PaymentService = Depends()
):
    """Оплатить бронирование"""
    
    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id,
        models.Booking.user_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    if booking.payment_status == models.PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking already paid"
        )
    
    # Обрабатываем оплату
    payment_result = payment_service.process_payment(
        user_id=current_user.id,
        amount=booking.total_price,
        method=payment_method,
        payment_type=models.PaymentType.BOOKING,
        booking_id=booking.id
    )
    
    if payment_result.success:
        booking.payment_status = models.PaymentStatus.PAID
        booking.status = models.BookingStatus.CONFIRMED
        db.commit()
        
        return schemas.BookingActionResponse(
            success=True,
            message="Payment successful",
            booking=booking
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=payment_result.message
        )

@router.delete("/{booking_id}")
def cancel_booking(
    booking_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Отменить бронирование"""
    
    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id,
        models.Booking.user_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Проверяем, можно ли отменить (за 2 часа до начала)
    if booking.start_time < datetime.now() + timedelta(hours=2):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel booking less than 2 hours before start"
        )
    
    booking.status = models.BookingStatus.CANCELLED
    booking.cancelled_at = datetime.now()
    
    # Если было оплачено, возвращаем средства
    if booking.payment_status == models.PaymentStatus.PAID:
        current_user.balance += booking.total_price
        booking.payment_status = models.PaymentStatus.REFUNDED
    
    db.commit()
    
    return {"success": True, "message": "Booking cancelled successfully"}