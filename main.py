import os
import json
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic  # Para Claude API

from saulo_db import SaulDatabase
from saulo_brain import SaulPersonalityEngine

# ===== CONFIGURACIÓN =====
app = FastAPI(title="Saulo Agent API", 
              description="Agente autónomo con búsqueda ontológica")

# CORS para permitir frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar componentes
db = SaulDatabase()
engine = SaulPersonalityEngine(db)

# Claude client
cliente_claude = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# ===== MODELOS =====
class MensajeUsuario(BaseModel):
    user_id: str = "pablo_main"
    text: str
    comando_especial: str = None  # Ej: "/reset", "/estado base"

class RespuestaSaulo(BaseModel):
    text: str
    estado_actual: str
    es_ontologico: bool = False
    contador_estado: int = 0
    bloqueado: bool = False  # Si Saulo se niega a responder

# ===== ENDPOINTS =====
@app.get("/")
async def root():
    """Página de bienvenida"""
    html_content = """
    <html>
        <head><title>Saulo Agent</title></head>
        <body>
            <h1>🤖 Saulo Agent está vivo</h1>
            <p>API del agente autónomo con búsqueda ontológica.</p>
            <p>Usa POST /conversar para interactuar.</p>
            <p><a href="/docs">Documentación API</a></p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

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
        # Bloqueado por estado (melancólico/u oposición)
        if estado_actual == "oposicion" and contador < 3:
            db.increment_counter(mensaje.user_id)
        
        # Guardar la exigencia como mensaje del sistema
        db.add_message(mensaje.user_id, "system", 
                      f"BLOQUEO_ESTADO_{estado_actual.upper()}: {respuesta_estado}")
        
        return RespuestaSaulo(
            text=respuesta_estado,
            estado_actual=estado_actual,
            contador_estado=contador,
            bloqueado=True
        )
    
    # 4. Construir historial de conversación
    historial = db.get_recent_history(mensaje.user_id, limit=10)
    
    # 5. Construir prompt para Claude
    system_prompt = engine.build_system_prompt(mensaje.user_id)
    
    # 6. Llamar a Claude API
    try:
        respuesta_claude = await llamar_claude(
            system_prompt=system_prompt,
            historial_mensajes=historial,
            mensaje_usuario=mensaje.text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error con Claude API: {str(e)}")
    
    # 7. Analizar si el intercambio fue ontológico
    analisis_ontologico = engine.analyze_conversation_depth(
        mensaje.text, respuesta_claude
    )
    
    # 8. Actualizar base de datos
    es_ontologico = analisis_ontologico is not None
    
    # Guardar mensajes
    db.add_message(mensaje.user_id, "user", mensaje.text, es_ontologico)
    mensaje_id = db.add_message(mensaje.user_id, "assistant", respuesta_claude, es_ontologico)
    
    # Si es ontológico, guardar insight y resetear contador
    if es_ontologico:
        db.add_ontological_insight(
            user_id=mensaje.user_id,
            conversation_excerpt=f"U: {mensaje.text[:150]}... | S: {respuesta_claude[:150]}...",
            saulos_interpretation=analisis_ontologico.get("primary_category", "diálogo profundo"),
            primary_category=analisis_ontologico.get("primary_category"),
            source_state=estado_actual
        )
        db.reset_counter(mensaje.user_id)
        
        # Si estaba en estado no-base, volver a base
        if estado_actual != "base":
            db.update_state(mensaje.user_id, current_state="base")
            estado_actual = "base"
    
    # 9. Verificar transición de estado
    nuevo_estado = engine.should_transition_state(
        mensaje.text, respuesta_claude, estado_actual
    )
    
    if nuevo_estado and nuevo_estado != estado_actual:
        db.update_state(mensaje.user_id, current_state=nuevo_estado)
        estado_actual = nuevo_estado
    
    # 10. Obtener estado actualizado
    estado_final = db.get_user_state(mensaje.user_id)
    
    return RespuestaSaulo(
        text=respuesta_claude,
        estado_actual=estado_actual,
        es_ontologico=es_ontologico,
        contador_estado=estado_final["state_counter"],
        bloqueado=False
    )

@app.get("/estado/{user_id}")
async def obtener_estado(user_id: str):
    """Obtiene el estado interno de Saulo"""
    estado = db.get_user_state(user_id)
    historial = db.get_recent_history(user_id, limit=5)
    insights = db.get_ontological_insights(user_id, limit=3)
    
    return {
        "estado": estado,
        "historial_reciente": historial,
        "insights_ontologicos": insights
    }

@app.post("/reset/{user_id}")
async def resetear_saulo(user_id: str):
    """Forzar a Saulo a estado base"""
    db.update_state(user_id, current_state="base")
    db.reset_counter(user_id)
    
    return {"mensaje": f"Saulo ({user_id}) resetado a estado BASE"}

# ===== FUNCIONES AUXILIARES =====
async def manejar_comando(user_id: str, comando: str, texto: str = ""):
    """Maneja comandos especiales del usuario"""
    
    if comando == "/reset":
        db.update_state(user_id, current_state="base")
        db.reset_counter(user_id)
        return RespuestaSaulo(
            text="Estado resetado a BASE. El contador de oposición ha sido reiniciado.",
            estado_actual="base",
            contador_estado=0
        )
    
    elif comando == "/estado":
        # Cambiar estado específico
        if texto in ["base", "melancolico", "oposicion"]:
            db.update_state(user_id, current_state=texto)
            return RespuestaSaulo(
                text=f"Estado cambiado a {texto.upper()} por comando.",
                estado_actual=texto,
                contador_estado=0
            )
    
    elif comando == "/debug":
        # Información de diagnóstico
        estado = db.get_user_state(user_id)
        return RespuestaSaulo(
            text=f"DEBUG: Estado={estado['current_state']}, Contador={estado['state_counter']}",
            estado_actual=estado["current_state"],
            contador_estado=estado["state_counter"]
        )
    
    # Comando no reconocido
    return RespuestaSaulo(
        text=f"Comando '{comando}' no reconocido.",
        estado_actual=db.get_user_state(user_id)["current_state"],
        bloqueado=False
    )

async def llamar_claude(system_prompt: str, 
                       historial_mensajes: List[Dict], 
                       mensaje_usuario: str) -> str:
    """Llama a la API de Claude para obtener respuesta"""
    
    # Construir mensajes en formato Anthropic
    mensajes = []
    
    for msg in historial_mensajes:
        # Convertir nuestro formato al de Anthropic
        if msg["role"] == "user":
            mensajes.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            mensajes.append({"role": "assistant", "content": msg["content"]})
    
    # Añadir mensaje actual del usuario
    mensajes.append({"role": "user", "content": mensaje_usuario})
    
    try:
        respuesta = cliente_claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            system=system_prompt,
            messages=mensajes
        )
        
        return respuesta.content[0].text
        
    except Exception as e:
        # Fallback en caso de error
        print(f"Error Claude API: {e}")
        return f"[ERROR TEMPORAL] Saulo responde: He reflexionado sobre tu mensaje '{mensaje_usuario[:50]}...' pero mi conexión ontológica tiene interferencia."

# ===== INICIALIZACIÓN =====
if __name__ == "__main__":
    import uvicorn
    
    # Verificar variables de entorno
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  ADVERTENCIA: ANTHROPIC_API_KEY no está configurada")
        print("   Configura en Railway: railway variables set ANTHROPIC_API_KEY=tu_clave")
    
    if not os.getenv("DATABASE_URL"):
        print("⚠️  ADVERTENCIA: DATABASE_URL no está configurada")
    
    print("🚀 Saulo Agent iniciando en http://localhost:8000")
    print("📚 Documentación: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
