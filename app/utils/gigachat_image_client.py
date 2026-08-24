import time

# ... (далее идут константы) ...

# Глобальный кэш для токена (живет 30 минут)
_token_cache = {"token": None, "expires_at": 0}

def get_gigachat_token() -> str:
    """Получает токен доступа для GigaChat API с кэшированием"""
    current_time = time.time()
    
    # Если токен есть и он еще действителен (с запасом 5 минут), возвращаем его
    if _token_cache["token"] and current_time < (_token_cache["expires_at"] - 300):
        return _token_cache["token"]
    
    logger.info("🔄 Получение нового токена GigaChat...")
    auth_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": BASIC_AUTH
    }
    
    try:
        response = requests.post(AUTH_URL, headers=auth_headers, data="scope=GIGACHAT_API_PERS", timeout=10, verify=CERT_PATH)
        response.raise_for_status()
        token = response.json().get("access_token")
        
        _token_cache["token"] = token
        _token_cache["expires_at"] = current_time + 1800 # 30 минут
        
        logger.info("✅ Токен GigaChat успешно получен и закэширован")
        return token
    except requests.exceptions.RequestException:
        logger.warning("⚠️ Ошибка сертификата, пробуем без проверки...")
        response = requests.post(AUTH_URL, headers=auth_headers, data="scope=GIGACHAT_API_PERS", timeout=10, verify=False)
        response.raise_for_status()
        token = response.json().get("access_token")
        
        _token_cache["token"] = token
        _token_cache["expires_at"] = current_time + 1800
        
        logger.info("✅ Токен GigaChat успешно получен (без проверки) и закэширован")
        return token

# ... (остальная часть файла generate_image и upload_to_max_api остается без изменений из предыдущего сообщения) ...
