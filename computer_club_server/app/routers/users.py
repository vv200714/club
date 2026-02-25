from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas
import models
import auth
from database import get_db

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Получить информацию о текущем пользователе"""
    return current_user

@router.put("/me", response_model=schemas.UserResponse)
def update_current_user(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Обновить информацию о текущем пользователе"""
    
    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.get("/balance")
def get_balance(
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Получить текущий баланс"""
    return {"balance": current_user.balance}

@router.post("/balance/top-up")
def top_up_balance(
    amount: float,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Пополнить баланс"""
    
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )
    
    current_user.balance += amount
    
    # Создаем запись о платеже
    payment = models.Payment(
        user_id=current_user.id,
        amount=amount,
        type=models.PaymentType.BALANCE_TOP_UP,
        method=models.PaymentMethod.ONLINE,
        status=models.PaymentStatus.PAID
    )
    
    db.add(payment)
    db.commit()
    
    return {
        "success": True,
        "new_balance": current_user.balance,
        "amount_added": amount
    }