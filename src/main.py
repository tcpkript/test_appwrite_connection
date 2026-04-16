from fastapi import FastAPI, BackgroundTasks
from .appwrite_fastapi import AppwriteBridge
import os
import httpx
from datetime import datetime

# 1. Crear la aplicación FastAPI
app = FastAPI(title="APPyWrite Telegram Bot")

# 2. Configuración de Telegram (Añadir a Appwrite Console)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

async def send_telegram_message(message: str):
    """
    Función de utilidad para enviar mensajes a Telegram.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configurados.")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"Error enviando a Telegram: {e}")
            return False

# 3. Rutas de la API

@app.get("/")
async def root():
    return {"status": "alive", "time": datetime.now().isoformat()}

@app.get("/cron/telegram-alert")
async def telegram_cron():
    """
    Este endpoint será llamado por el Scheduler de Appwrite.
    Ej: cada 1 hora.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"🚀 <b>APPyWrite Update</b>\n\nEl backend sigue vivo.\nFecha: <code>{now}</code>"
    
    success = await send_telegram_message(message)
    
    return {
        "success": success,
        "timestamp": now,
        "message": "Cron alert executed"
    }

@app.post("/telegram/notify")
async def notify_custom(message: str):
    """
    Puedes llamar a este endpoint desde fuera (ej: Postman)
    para mandar mensajes personalizados.
    """
    success = await send_telegram_message(message)
    return {"status": "sent" if success else "failed"}

# 4. Configurar el Puente para Appwrite
bridge = AppwriteBridge(app)

# 5. El punto de entrada (ASYNC)
async def main(context):
    # TIP: Appwrite Schedules envían la ruta '/' por defecto si no se especifica.
    # Podemos forzar a que el Cron llame a la ruta del bot:
    
    if context.req.headers.get("x-appwrite-trigger") == "schedule":
        # Si el trigger es un Cron de Appwrite, podemos redirigirlo 
        # internamente a nuestro endpoint del bot si queremos.
        context.req.path = "/cron/telegram-alert"
        
    return await bridge.handle(context)
