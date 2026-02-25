import csv
import io
from datetime import datetime
from sqlalchemy.orm import Session
import models
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ReportService:
    """Сервис для генерации отчетов"""
    
    def generate_csv_report(self, db: Session, start_date: datetime, end_date: datetime) -> io.StringIO:
        """Генерирует CSV отчет по платежам"""
        
        payments = db.query(models.Payment).filter(
            models.Payment.payment_date >= start_date,
            models.Payment.payment_date <= end_date,
            models.Payment.status == models.PaymentStatus.PAID
        ).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow(['ID', 'Date', 'User ID', 'Amount', 'Type', 'Method', 'Transaction ID'])
        
        # Данные
        for p in payments:
            writer.writerow([
                p.id,
                p.payment_date.isoformat(),
                p.user_id,
                p.amount,
                p.type.value,
                p.method.value,
                p.transaction_id or ''
            ])
        
        output.seek(0)
        return output
    
    def generate_daily_report(self, db: Session, date: datetime) -> dict:
        """Генерирует дневной отчет"""
        
        start = datetime(date.year, date.month, date.day)
        end = start + timedelta(days=1)
        
        # Статистика по платежам
        payments = db.query(models.Payment).filter(
            models.Payment.payment_date >= start,
            models.Payment.payment_date < end,
            models.Payment.status == models.PaymentStatus.PAID
        ).all()
        
        # Статистика по сессиям
        sessions = db.query(models.Session).filter(
            models.Session.start_time >= start,
            models.Session.start_time < end,
            models.Session.status == models.SessionStatus.COMPLETED
        ).all()
        
        # Статистика по новым пользователям
        new_users = db.query(models.User).filter(
            models.User.created_at >= start,
            models.User.created_at < end
        ).count()
        
        total_hours = sum((s.end_time - s.start_time).total_seconds() / 3600 for s in sessions if s.end_time)
        
        return {
            "date": date.isoformat(),
            "revenue": sum(p.amount for p in payments),
            "transactions": len(payments),
            "sessions": len(sessions),
            "total_hours": round(total_hours, 2),
            "new_users": new_users,
            "average_session": round(total_hours / len(sessions), 2) if sessions else 0
        }