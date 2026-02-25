from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import schemas
import models
import auth
from database import get_db

router = APIRouter(prefix="/api/computers", tags=["Computers"])

@router.get("/", response_model=List[schemas.ComputerResponse])
def get_all_computers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Получить список всех компьютеров"""
    computers = db.query(models.Computer).filter(
        models.Computer.is_active == True
    ).order_by(models.Computer.row, models.Computer.place).all()
    
    return computers

@router.get("/available", response_model=List[schemas.ComputerResponse])
def get_available_computers(
    start_time: datetime = None,
    end_time: datetime = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Получить доступные компьютеры на указанное время"""
    
    if not start_time:
        start_time = datetime.now()
    if not end_time:
        end_time = start_time + timedelta(hours=1)
    
    # Получаем все компьютеры
    computers = db.query(models.Computer).filter(
        models.Computer.is_active == True,
        models.Computer.status == models.ComputerStatus.AVAILABLE
    ).all()
    
    # Проверяем бронирования на это время
    booked_computer_ids = db.query(models.Booking.computer_id).filter(
        models.Booking.status.in_([
            models.BookingStatus.CONFIRMED,
            models.BookingStatus.ACTIVE,
            models.BookingStatus.PENDING
        ]),
        models.Booking.start_time < end_time,
        models.Booking.end_time > start_time
    ).all()
    
    booked_ids = [id for (id,) in booked_computer_ids]
    
    # Фильтруем доступные
    available_computers = [c for c in computers if c.id not in booked_ids]
    
    return available_computers

@router.get("/hall-scheme", response_model=schemas.HallSchemeResponse)
def get_hall_scheme(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Получить схему зала с текущим статусом всех компьютеров"""
    
    computers = db.query(models.Computer).filter(
        models.Computer.is_active == True
    ).order_by(models.Computer.row, models.Computer.place).all()
    
    # Получаем активные сессии
    active_sessions = db.query(models.Session).filter(
        models.Session.status == models.SessionStatus.ACTIVE
    ).all()
    
    session_map = {s.computer_id: s for s in active_sessions}
    
    # Группируем по рядам
    rows_dict = {}
    for computer in computers:
        if computer.row not in rows_dict:
            rows_dict[computer.row] = []
        
        # Определяем текущего пользователя если компьютер занят
        current_user_name = None
        if computer.id in session_map:
            session = session_map[computer.id]
            user = db.query(models.User).filter(models.User.id == session.user_id).first()
            current_user_name = user.full_name if user else "Неизвестно"
        
        # Определяем цвет статуса
        status_colors = {
            models.ComputerStatus.AVAILABLE: "#4CAF50",    # Зеленый
            models.ComputerStatus.OCCUPIED: "#F44336",     # Красный
            models.ComputerStatus.RESERVED: "#FF9800",     # Оранжевый
            models.ComputerStatus.MAINTENANCE: "#9E9E9E",  # Серый
            models.ComputerStatus.BROKEN: "#000000"        # Черный
        }
        
        status_display = {
            models.ComputerStatus.AVAILABLE: "Свободен",
            models.ComputerStatus.OCCUPIED: "Занят",
            models.ComputerStatus.RESERVED: "Забронирован",
            models.ComputerStatus.MAINTENANCE: "Обслуживание",
            models.ComputerStatus.BROKEN: "Сломан"
        }
        
        hall_computer = schemas.HallComputer(
            id=computer.id,
            name=computer.name,
            row=computer.row,
            place=computer.place,
            status=computer.status,
            status_display=status_display[computer.status],
            status_color=status_colors[computer.status],
            current_user=current_user_name,
            price_per_hour=computer.price_per_hour
        )
        
        rows_dict[computer.row].append(hall_computer)
    
    # Формируем ответ
    rows = []
    for row_num in sorted(rows_dict.keys()):
        rows.append(schemas.HallRow(
            row_number=row_num,
            computers=sorted(rows_dict[row_num], key=lambda c: c.place)
        ))
    
    stats = {
        models.ComputerStatus.AVAILABLE: 0,
        models.ComputerStatus.OCCUPIED: 0,
        models.ComputerStatus.RESERVED: 0,
        models.ComputerStatus.MAINTENANCE: 0,
        models.ComputerStatus.BROKEN: 0
    }
    
    for c in computers:
        stats[c.status] += 1
    
    return schemas.HallSchemeResponse(
        rows=rows,
        total_computers=len(computers),
        available=stats[models.ComputerStatus.AVAILABLE],
        occupied=stats[models.ComputerStatus.OCCUPIED],
        reserved=stats[models.ComputerStatus.RESERVED],
        maintenance=stats[models.ComputerStatus.MAINTENANCE]
    )

@router.get("/{computer_id}", response_model=schemas.ComputerResponse)
def get_computer(
    computer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Получить информацию о конкретном компьютере"""
    
    computer = db.query(models.Computer).filter(
        models.Computer.id == computer_id,
        models.Computer.is_active == True
    ).first()
    
    if not computer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Computer not found"
        )
    
    return computer