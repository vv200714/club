from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from auth import get_password_hash
from datetime import datetime, timedelta
import random

def seed_database():
    """Заполнение базы тестовыми данными"""
    db = SessionLocal()
    
    try:
        # Создаем админа
        admin = models.User(
            email="admin@club.ru",
            username="admin",
            full_name="Admin Adminov",
            hashed_password=get_password_hash("admin123"),
            role=models.UserRole.ADMIN,
            balance=10000,
            is_active=True
        )
        db.add(admin)
        
        # Создаем тестовых пользователей
        users = []
        for i in range(1, 6):
            user = models.User(
                email=f"user{i}@example.com",
                username=f"user{i}",
                full_name=f"User {i}",
                hashed_password=get_password_hash("password123"),
                role=models.UserRole.CLIENT,
                balance=random.randint(0, 5000),
                is_active=True
            )
            db.add(user)
            users.append(user)
        
        # Создаем компьютеры
        computers = []
        for row in range(1, 4):
            for place in range(1, 5):
                computer = models.Computer(
                    name=f"ПК {row}-{place}",
                    row=row,
                    place=place,
                    price_per_hour=random.choice([150, 200, 250]),
                    processor="Intel Core i7-12700K",
                    ram="32GB DDR5",
                    graphics_card="RTX 3070",
                    monitor="27'' 165Hz",
                    status=models.ComputerStatus.AVAILABLE,
                    position_x=place * 100,
                    position_y=row * 100
                )
                db.add(computer)
                computers.append(computer)
        
        # Создаем бронирования
        for i, user in enumerate(users[:3]):
            booking = models.Booking(
                user_id=user.id,
                computer_id=computers[i].id,
                start_time=datetime.now() + timedelta(days=1, hours=i),
                end_time=datetime.now() + timedelta(days=1, hours=i+2),
                total_price=computers[i].price_per_hour * 2,
                status=models.BookingStatus.CONFIRMED,
                payment_status=models.PaymentStatus.PAID
            )
            db.add(booking)
        
        # Создаем турниры
        tournaments = [
            models.Tournament(
                name="CS:GO Tournament #1",
                game="CS:GO",
                start_date=datetime.now() + timedelta(days=7),
                end_date=datetime.now() + timedelta(days=7, hours=5),
                registration_end_date=datetime.now() + timedelta(days=6),
                max_participants=16,
                current_participants=8,
                entry_fee=300,
                prize_pool=5000,
                status=models.TournamentStatus.REGISTRATION,
                format="5x5"
            ),
            models.Tournament(name="Dota 2 Cup", 
                game="Dota 2",
                start_date=datetime.now() + timedelta(days=14),
                end_date=datetime.now() + timedelta(days=14, hours=6),
                registration_end_date=datetime.now() + timedelta(days=13),
                max_participants=8,
                current_participants=3,
                entry_fee=500,
                prize_pool=8000,
                status=models.TournamentStatus.REGISTRATION,
                format="5x5"
            )
        ]
        
        for tournament in tournaments:
            db.add(tournament)
        
        db.commit()
        print("✅ Тестовые данные успешно добавлены!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Заполнение базы тестовыми данными...")
    seed_database()