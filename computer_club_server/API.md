# Computer Club API Documentation

## Базовый URL


## Аутентификация

### Регистрация
**POST** `/api/auth/register`
```json
{
  "email": "user@example.com",
  "username": "user123",
  "full_name": "",
  "phone": "+79999999999",
  "password": "password"
}