from fastapi import FastAPI
from .appwrite_fastapi import AppwriteBridge
import os
import httpx
from datetime import datetime

app = FastAPI(title="APPyWrite with Custom Cron Routing")

# --- RUTAS ---

@app.get("/")
async def root():
    return {"message": "APPyWrite is running!"}

@app.get("/cron/telegram-alert")
async def telegram_alert():
    """Esta es la ruta que queremos que el Cron ejecute"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={
                "chat_id": chat_id,
                "text": f"⏰ <b>Cron Job Executed</b>\nTime: {datetime.now().isoformat()}",
                "parse_mode": "HTML"
            })
    
    return {"status": "success", "task": "telegram_alert"}

@app.get("/cron/backup")
async def backup_task():
    """Otra ruta que podrías querer llamar con otro Cron"""
    return {"status": "success", "task": "backup"}

# --- EL PUENTE (CON ENRUTAMIENTO INTELIGENTE) ---
bridge = AppwriteBridge(app)

async def main(context):
    # 1. Detectamos si la llamada viene del Scheduler (Cron) de Appwrite
    is_cron = context.req.headers.get("x-appwrite-trigger") == "schedule"
    
    if is_cron:
        # 2. Leemos la variable de entorno que configuraste en la UI
        # Si no existe, por defecto irá a '/'
        target_path = os.environ.get("CRON_TARGET_PATH", "/")
        
        # 3. 'ENGAÑAMOS' a FastAPI cambiando el path de la petición
        # Ahora FastAPI pensará que la petición entró por esa ruta específica
        context.req.path = target_path
        
        context.log(f"Cron detected! Routing internal request to: {target_path}")

    # 4. El puente hace el resto
    return await bridge.handle(context)
