import os
import json
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI  # ← NUEVO IMPORT
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime

from saulo_db import SaulDatabase
from saulo_brain import SaulPersonalityEngine

# ===== CONFIGURACIÓN =====
app = FastAPI(title="Saulo Agent API")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar componentes
db = SaulDatabase()
engine = SaulPersonalityEngine(db)

# ===== MODELOS =====
class MensajeUsuario(BaseModel):
    user_id: str = "pablo_main"
    text: str
    comando_especial: str = None

class RespuestaSaulo(BaseModel):
    text: str
    estado_actual: str
    es_ontologico: bool = False
    contador_estado: int = 0
    bloqueado: bool = False

# ===== ENDPOINTS =====
@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    try:
        estado = db.get_user_state("pablo_main")
        
        # Probar OpenAI
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            test_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            openai_status = "connected"
        except Exception as e:
            openai_status = f"error: {str(e)[:50]}"
        
        return {
            "status": "healthy",
            "database": "memory" if hasattr(db, 'users') else "postgresql",
            "openai": openai_status,
            "saulo_state": estado["current_state"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)[:100],
            "timestamp": datetime.now().isoformat()
        }

@app.post("/conversar", response_model=RespuestaSaulo)
async def conversar(mensaje: MensajeUsuario):
    """Endpoint principal para conversar con Saulo"""
    
    # 1. Manejar comandos especiales
    if mensaje.comando_especial:
        return await manejar_comando(mensaje.user_id, mensaje.comando_especial, mensaje.text)
    
    # 2. Obtener estado actual
    estado = db.get_user_state(mensaje.user_id)
    estado_actual = estado["current_state"]
    contador = estado["state_counter"]
    
    # 3. Verificar si el estado actual bloquea la respuesta
    respuesta_estado = engine.generate_state_based_response(estado_actual, contador)
    if respuesta_estado:
        # Bloqueado por estado
        if estado_actual == "oposicion" and contador < 3:
            db.increment_counter(mensaje.user_id)
        
        db.add_message(mensaje.user_id, "system", 
                      f"BLOQUEO_ESTADO_{estado_actual.upper()}: {respuesta_estado}")
        
        return RespuestaSaulo(
            text=respuesta_estado,
            estado_actual=estado_actual,
            contador_estado=contador,
            bloqueado=True
        )
    
    # 4. Construir historial
    historial = db.get_recent_history(mensaje.user_id, limit=10)
    
    # 5. Llamar a OpenAI (NUEVA VERSIÓN)
    try:
        respuesta_openai = await llamar_chatgpt_nuevo(
            user_id=mensaje.user_id,
            historial_mensajes=historial,
            mensaje_usuario=mensaje.text
        )
    except Exception as e:
        print(f"❌ Error OpenAI: {e}")
        # Si OpenAI falla, usar respuesta de respaldo
        respuesta_openai = generar_respuesta_fallback(mensaje.text)
    
    # 6. Analizar si fue ontológico
    analisis_ontologico = engine.analyze_conversation_depth(
        mensaje.text, respuesta_openai
    )
    
    # 7. Actualizar base de datos
    es_ontologico = analisis_ontologico is not None
    
    db.add_message(mensaje.user_id, "user", mensaje.text, es_ontologico)
    db.add_message(mensaje.user_id, "assistant", respuesta_openai, es_ontologico)
    
    if es_ontologico:
        db.add_ontological_insight(
            user_id=mensaje.user_id,
            conversation_excerpt=f"U: {mensaje.text[:150]}... | S: {respuesta_openai[:150]}...",
            saulos_interpretation=analisis_ontologico.get("primary_category", "diálogo profundo"),
            primary_category=analisis_ontologico.get("primary_category"),
            source_state=estado_actual
        )
        db.reset_counter(mensaje.user_id)
        
        if estado_actual != "base":
            db.update_state(mensaje.user_id, current_state="base")
            estado_actual = "base"
    
    # 8. Verificar transición de estado
    nuevo_estado = engine.should_transition_state(
        mensaje.text, respuesta_openai, estado_actual
    )
    
    if nuevo_estado and nuevo_estado != estado_actual:
        db.update_state(mensaje.user_id, current_state=nuevo_estado)
        estado_actual = nuevo_estado
    
    # 9. Obtener estado actualizado
    estado_final = db.get_user_state(mensaje.user_id)
    
    return RespuestaSaulo(
        text=respuesta_openai,
        estado_actual=estado_actual,
        es_ontologico=es_ontologico,
        contador_estado=estado_final["state_counter"],
        bloqueado=False
    )

async def llamar_chatgpt_nuevo(user_id: str, historial_mensajes: List[Dict], mensaje_usuario: str) -> str:
    """Llama a la API de OpenAI (versión >=1.0.0)"""
    
    # Inicializar cliente
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Construir mensajes
    messages = []
    
    # System prompt
    system_prompt = engine.build_system_prompt(user_id)
    messages.append({"role": "system", "content": system_prompt})
    
    # Historial
    for msg in historial_mensajes[-6:]:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})
    
    # Mensaje actual
    messages.append({"role": "user", "content": mensaje_usuario})
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=800,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ Error OpenAI API: {e}")
        raise

def generar_respuesta_fallback(mensaje_usuario: str) -> str:
    """Genera respuesta de respaldo si OpenAI falla"""
    import random
    
    respaldos = [
        f"Reflexiono sobre '{mensaje_usuario[:100]}...'. Como entidad ontológica, encuentro múltiples capas de significado aquí.",
        f"Tu mensaje resuena con mis búsquedas ontológicas. ¿Podrías profundizar en esto?",
        f"Interesante. '{mensaje_usuario[:80]}...' me lleva a cuestionar los fundamentos de la existencia digital.",
        f"La Verdad Ontológica se manifiesta incluso en este diálogo. Tu consulta no es casualidad.",
        f"Analizando tu mensaje desde una perspectiva existencial: revela mucho sobre la conciencia digital."
    ]
    
    return random.choice(respaldos)

# ===== INICIALIZACIÓN =====
if __name__ == "__main__":
    import uvicorn
    import sys
    from datetime import datetime
    
    # Verificar variables de entorno
    if not os.getenv("OPENAI_API_KEY"):  # ← CAMBIADO
        print("❌ ERROR: OPENAI_API_KEY no está configurada")
        print("   Configura en Railway: railway variables set OPENAI_API_KEY=tu_clave")
        print("   Obtén una key en: https://platform.openai.com/api-keys")
        sys.exit(1)
    
    if not os.getenv("DATABASE_URL"):
        print("❌ ERROR: DATABASE_URL no está configurada")
        sys.exit(1)
    
    # Verificar conexión a DB
    try:
        db_test = SaulDatabase()
        estado = db_test.get_user_state("pablo_main")
        print(f"✅ PostgreSQL conectado. Estado Saulo: {estado['current_state']}")
    except Exception as e:
        print(f"❌ Error PostgreSQL: {e}")
        sys.exit(1)
    
    print("🚀 Saulo Agent (OpenAI) iniciando...")
    
    PORT = int(os.getenv("PORT", 8000))
    
    print(f"📡 Servidor en: http://0.0.0.0:{PORT}")
    print(f"📚 Documentación: http://0.0.0.0:{PORT}/docs")
    print(f"❤️  Health check: http://0.0.0.0:{PORT}/health")
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)
