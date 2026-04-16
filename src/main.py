from fastapi import FastAPI
from .appwrite_fastapi import AppwriteBridge
import os

# 1. Crear la aplicación FastAPI
app = FastAPI(title="Appwrite FastAPI Bridge")

# 2. Definir tus rutas como lo harías normalmente
@app.get("/")
async def root():
    return {
        "motto": "Build like a team of hundreds_",
        "learn": "https://appwrite.io/docs",
        "bridge": "FastAPI is now running on Appwrite!"
    }

@app.get("/ping")
async def ping():
    return "Pong"

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    return {"user_id": user_id, "status": "mocked", "message": "Ready to scale!"}

# 3. Configurar el Puente para Appwrite
# Instanciarlo fuera de main para mantener la app en memoria (Warm Start)
bridge = AppwriteBridge(app)

# 4. El punto de entrada que Appwrite espera
def main(context):
    # El bridge se encarga de traducir context -> FastAPI -> context
    return bridge.handle(context)
