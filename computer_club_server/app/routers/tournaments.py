from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import schemas
import models
import auth
from database import get_db

router = APIRouter(prefix="/api/tournaments", tags=["Tournaments"])

@router.get("/", response_model=List[schemas.TournamentResponse])
def get_all_tournaments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Получить список всех турниров"""
    
    tournaments = db.query(models.Tournament).filter(
        models.Tournament.status != models.TournamentStatus.DRAFT
    ).order_by(models.Tournament.start_date.desc()).all()
    
    return tournaments

@router.get("/upcoming", response_model=List[schemas.TournamentResponse])
def get_upcoming_tournaments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Получить предстоящие турниры"""
    
    tournaments = db.query(models.Tournament).filter(
        models.Tournament.start_date > datetime.now(),
        models.Tournament.status == models.TournamentStatus.REGISTRATION
    ).order_by(models.Tournament.start_date).all()
    
    return tournaments

@router.post("/{tournament_id}/register")
def register_for_tournament(
    tournament_id: int,
    team_name: str = None,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Зарегистрироваться на турнир"""
    
    tournament = db.query(models.Tournament).filter(
        models.Tournament.id == tournament_id
    ).first()
    
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )
    
    # Проверяем статус турнира
    if tournament.status != models.TournamentStatus.REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration is closed"
        )
    
    if tournament.start_date < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tournament already started"
        )
    
    # Проверяем количество участников
    if tournament.current_participants >= tournament.max_participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tournament is full"
        )
    
    # Проверяем, не зарегистрирован ли уже
    existing = db.query(models.TournamentRegistration).filter(
        models.TournamentRegistration.user_id == current_user.id,
        models.TournamentRegistration.tournament_id == tournament_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already registered"
        )
    
    # Создаем регистрацию
    registration = models.TournamentRegistration(
        user_id=current_user.id,
        tournament_id=tournament_id,
        team_name=team_name,
        status="confirmed",
        payment_status=models.PaymentStatus.PENDING if tournament.entry_fee > 0 else models.PaymentStatus.PAID
    )
    
    db.add(registration)
    
    # Увеличиваем счетчик участников
    tournament.current_participants += 1
    
    db.commit()
    
    return {
        "success": True,
        "message": "Successfully registered for tournament",
        "requires_payment": tournament.entry_fee > 0,
        "entry_fee": tournament.entry_fee
    }

@router.get("/my", response_model=List[schemas.TournamentRegistrationResponse])
def get_my_tournaments(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить мои турниры"""
    
    registrations = db.query(models.TournamentRegistration).filter(
        models.TournamentRegistration.user_id == current_user.id
    ).all()
    
    return registrations