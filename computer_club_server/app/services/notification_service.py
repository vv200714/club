import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Сервис для отправки уведомлений"""
    
    async def send_email(self, to_email: str, subject: str, body: str):
        """Отправка email (заглушка)"""
        logger.info(f"Sending email to {to_email}: {subject}")
        
        # Реальная отправка email (раскомментировать когда будут настройки)
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USER
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
        """
        
        # Пока просто логируем
        logger.info(f"Email would be sent to {to_email}: {subject}\n{body}")
        
        return True
    
    async def send_booking_confirmation(self, user_email: str, booking_id: int, computer_name: str, start_time, end_time, total_price):
        """Отправка подтверждения бронирования"""
        
        subject = "Подтверждение бронирования"
        body = f"""
        Ваше бронирование подтверждено!
        
        Детали:
        - ID бронирования: {booking_id}
        - Компьютер: {computer_name}
        - Начало: {start_time}
        - Окончание: {end_time}
        - Сумма: {total_price} руб.
        
        Спасибо за использование нашего сервиса!
        """
        
        await self.send_email(user_email, subject, body)
    
    async def send_payment_receipt(self, user_email: str, amount: float, payment_type: str):
        """Отправка чека об оплате"""
        
        subject = "Чек об оплате"
        body = f"""
        Оплата прошла успешно!
        
        Сумма: {amount} руб.
        Тип: {payment_type}
        
        Спасибо за оплату!
        """
        
        await self.send_email(user_email, subject, body)