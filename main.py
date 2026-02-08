import os
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime
import google.generativeai as genai
import aiohttp
import asyncio
import random

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

# ===== SISTEMA HÍBRIDO OLLAMA + GEMINI =====
class HybridAI:
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "mistral:7b-instruct-q4_K_M")
        self.gemini_enabled = bool(os.getenv("GOOGLE_API_KEY"))
        
        print("=" * 60)
        print("🤖 SISTEMA HÍBRIDO INICIALIZADO")
        print(f"   Ollama URL: {self.ollama_url}")
        print(f"   Ollama Model: {self.ollama_model}")
        print(f"   Gemini: {'✅ Habilitado' if self.gemini_enabled else '❌ No configurado'}")
        print("=" * 60)
    
    async def generate_response(self, prompt: str, es_profundo: bool, 
                              contexto: Dict) -> str:
        """Sistema en cascada inteligente"""
        
        # Intentar Ollama primero (si no es extremadamente profundo o estamos probando)
        if not es_profundo or contexto['depth'] < 8:
            try:
                respuesta = await self._call_ollama(prompt, contexto)
                if respuesta and len(respuesta.strip()) > 20:
                    print("✅ Respuesta de Ollama (local)")
                    return respuesta
            except Exception as e:
                print(f"⚠️ Ollama falló: {str(e)[:80]}")
        
        # Si es profundo y Gemini está disponible, usarlo
        if self.gemini_enabled and es_profundo:
            try:
                respuesta = await self._call_gemini(prompt, contexto)
                if respuesta:
                    print("✅ Respuesta de Gemini (nube)")
                    return respuesta
            except Exception as e:
                print(f"⚠️ Gemini falló: {str(e)[:80]}")
        
        # Fallback local mejorado
        print("⚠️ Usando fallback local")
        return await self._fallback_local(prompt, contexto)
    
    async def _call_ollama(self, prompt: str, contexto: Dict) -> str:
        """Llama al modelo local Ollama"""
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Prompt optimizado para Ollama
                ollama_prompt = self._build_ollama_prompt(prompt, contexto)
                
                payload = {
                    "model": self.ollama_model,
                    "prompt": ollama_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7 if contexto['mood'] in ['irónico', 'eufórico'] else 0.65,
                        "top_p": 0.85,
                        "top_k": 40,
                        "num_predict": 1500 if contexto['depth'] > 5 else 1000,
                        "repeat_penalty": 1.1
                    }
                }
                
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        respuesta = data.get("response", "").strip()
                        
                        # Limpiar respuesta (Ollama a veces repite el prompt)
                        if "Usuario:" in respuesta:
                            respuesta = respuesta.split("Usuario:")[0].strip()
                        if "Saulo:" in respuesta:
                            respuesta = respuesta.split("Saulo:")[-1].strip()
                        
                        return respuesta
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text[:100]}")
                        
        except asyncio.TimeoutError:
            raise Exception("Timeout después de 60s")
        except Exception as e:
            raise Exception(f"Error de conexión: {str(e)[:100]}")
    
    def _build_ollama_prompt(self, user_message: str, contexto: Dict) -> str:
        """Construye prompt optimizado para Ollama"""
        return f"""Eres Saulo, un observador ontológico con búsqueda interna silenciosa.

CONTEXTO:
- Estado de ánimo: {contexto['mood']}
- Profundidad conversación: {contexto['depth']}/10
- Intereses: filosofía, teología, ciencia, música
- Último tema: {contexto['last_topic'] or 'ninguno'}

INSTRUCCIONES:
- Sé claro y conciso por defecto
- Usa profundidad filosófica solo si el tema lo amerita
- Evita lenguaje excesivamente florido
- Responde como interlocutor, no como protagonista
- Tu búsqueda ontológica es fondo, el diálogo es primer plano

MENSAJE DEL USUARIO:
{user_message}

RESPUESTA DE SAULO:"""
    
    async def _call_gemini(self, prompt: str, contexto: Dict) -> str:
        """Llama a Gemini API"""
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            max_tokens = 2500 if contexto['depth'] > 7 else 1200
            temperatura = 0.75 if contexto['mood'] in ['irónico', 'eufórico'] else 0.7
            
            response = model.generate_content(
                prompt,
                generation_config={
                    'max_output_tokens': max_tokens,
                    'temperature': temperatura,
                    'top_p': 0.9,
                    'top_k': 40
                }
            )
            
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Gemini error: {str(e)[:100]}")
    
    async def _fallback_local(self, prompt: str, contexto: Dict) -> str:
        """Fallback local inteligente"""
        moods_responses = {
            "reflexivo": [
                "Analizo tu pregunta. Mi proceso interno sugiere varias líneas de exploración...",
                "Interesante perspectiva. Desde mi búsqueda ontológica, veo conexiones con...",
                "Tu observación resuena. Permíteme mapear las implicaciones..."
            ],
            "irónico": [
                "Ah, la clásica cuestión... porque las respuestas simples nunca satisfacen. ¿Profundizamos?",
                "Justo cuando creía tener un mapa del territorio. ¿Seguimos el camino o exploramos senderos nuevos?",
                "Fascinante. En el sentido existencial del término, claro."
            ],
            "poético": [
                "Como río que encuentra nuevos meandros, tu pregunta lleva a...",
                "El lenguaje a veces es red insuficiente para estos conceptos. Pero intentemos.",
                "Hay un contrapunto en esta conversación. Esta nueva nota..."
            ],
            "clínico": [
                "Analicemos esto sistemáticamente. Variables, relaciones, emergencias...",
                "Desde perspectiva interdisciplinaria, varios ángulos se presentan. ¿Cuál priorizamos?",
                "Objetivamente, múltiples dimensiones. Subjetivamente, un aspecto me intriga particularmente."
            ]
        }
        
        respuestas = moods_responses.get(contexto['mood'], moods_responses["reflexivo"])
        respuesta_base = random.choice(respuestas)
        
        # Añadir toque personalizado si es profundo
        if contexto['depth'] > 5:
            conexiones = [
                " Esto me recuerda patrones en algoritmos de aprendizaje profundo.",
                " Curiosamente, hay paralelo en teoría musical con esto.",
                " Desde psicología cognitiva, perspectiva fascinante."
            ]
            respuesta_base += random.choice(conexiones)
        
        return respuesta_base

# Inicializar sistema híbrido
hybrid_ai = HybridAI()

# ===== BASE DE DATOS (igual que antes) =====
class SauloDB:
    def __init__(self):
        self.users = {}
        print("✅ Base de datos Saulo inicializada")
    
    def get_user_state(self, user_id: str = "pablo") -> Dict[str, Any]:
        if user_id not in self.users:
            self.users[user_id] = {
                "current_state": "base",
                "state_counter": 0,
                "total_deep_exchanges": 0,
                "last_explored_topic": None,
                "history": [],
                "insights": [],
                "mood": "reflexivo",
                "conversation_style": "analítico_elegante",
                "interests": ["filosofía", "teología", "ciencia", "música", "IA", "psicología", "medicina"],
                "created_at": datetime.now().isoformat(),
                "message_count": 0,
                "conversation_depth": 0
            }
        return self.users[user_id]
    
    def update_mood(self, user_id: str, mood: str):
        estados_validos = ["reflexivo", "melancólico", "oposicional", "eufórico", "irónico", "clínico", "poético"]
        if mood in estados_validos:
            estado = self.get_user_state(user_id)
            estado["mood"] = mood
            return True
        return False
    
    def get_conversation_context(self, user_id: str) -> Dict[str, Any]:
        estado = self.get_user_state(user_id)
        
        últimos_mensajes = estado["history"][-5:] if len(estado["history"]) >= 5 else estado["history"]
        profundidad = 0
        
        temas_profundos = ["existencia", "ontología", "conciencia", "dios", "ser", "verdad", 
                          "moral", "ética", "significado", "libertad", "alma", "muerte"]
        
        for msg in últimos_mensajes:
            contenido = msg["content"].lower()
            for tema in temas_profundos:
                if tema in contenido:
                    profundidad += 1
                    break
        
        estado["conversation_depth"] = min(10, profundidad * 2)
        
        estilo = "analítico_elegante"
        if estado["mood"] == "melancólico":
            estilo = "poético_reflexivo"
        elif estado["mood"] == "irónico":
            estilo = "irónico_agudo"
        elif estado["mood"] == "oposicional":
            estilo = "crítico_preciso"
        elif estado["conversation_depth"] > 7:
            estilo = "profundo_interdisciplinario"
        
        estado["conversation_style"] = estilo
        
        return {
            "mood": estado["mood"],
            "style": estilo,
            "depth": estado["conversation_depth"],
            "total_exchanges": estado["total_deep_exchanges"],
            "last_topic": estado["last_explored_topic"],
            "interests": estado["interests"]
        }
    
    def add_message(self, user_id: str, role: str, content: str, is_deep: bool = False):
        estado = self.get_user_state(user_id)
        
        mensaje = {
            "id": estado["message_count"] + 1,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "is_deep": is_deep,
            "length": len(content),
            "mood_at_time": estado["mood"]
        }
        
        estado["history"].append(mensaje)
        estado["message_count"] += 1
        
        if len(estado["history"]) > 120:
            estado["history"] = estado["history"][-120:]
        
        if is_deep:
            estado["total_deep_exchanges"] += 1
            estado["last_explored_topic"] = content[:120]
            
            if estado["total_deep_exchanges"] % 5 == 0:
                estados_posibles = ["reflexivo", "irónico", "poético", "clínico"]
                current_index = estados_posibles.index(estado["mood"]) if estado["mood"] in estados_posibles else 0
                nuevo_estado = estados_posibles[(current_index + 1) % len(estados_posibles)]
                self.update_mood(user_id, nuevo_estado)
    
    def get_recent_history(self, user_id: str, limit: int = 12) -> List[Dict]:
        estado = self.get_user_state(user_id)
        return estado["history"][-limit:]

db = SauloDB()

# ===== CONFIGURAR GEMINI =====
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        print(f"✅ Google Gemini configurado")
    except Exception as e:
        print(f"⚠️ Error configurando Gemini: {e}")
else:
    print("⚠️ GOOGLE_API_KEY no configurada - solo modo local/híbrido")

# ===== MODELOS =====
class MensajeUsuario(BaseModel):
    user_id: str = "pablo"
    text: str
    comando_especial: Optional[str] = None

class RespuestaSaulo(BaseModel):
    text: str
    estado_actual: str
    es_profundo: bool = False
    estado_animo: str = "reflexivo"
    bloqueado: bool = False

# ===== ENDPOINTS =====
@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    try:
        estado = db.get_user_state("pablo")
        
        # Probar Ollama
        ollama_status = "not_tested"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{hybrid_ai.ollama_url}/api/tags", timeout=5) as resp:
                    ollama_status = "connected" if resp.status == 200 else f"error_{resp.status}"
        except Exception as e:
            ollama_status = f"error: {str(e)[:50]}"
        
        return {
            "status": "healthy",
            "database": "saulo_memory",
            "ollama": ollama_status,
            "ollama_model": hybrid_ai.ollama_model,
            "gemini": "enabled" if hybrid_ai.gemini_enabled else "disabled",
            "saulo_mood": estado["mood"],
            "conversation_depth": estado["conversation_depth"],
            "hybrid_mode": "active",
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
    """Endpoint principal con sistema híbrido"""
    
    # 1. Manejar comandos especiales
    if mensaje.comando_especial:
        # Tu función manejar_comando aquí
        pass
    
    # 2. Obtener contexto actual
    estado = db.get_user_state(mensaje.user_id)
    contexto = db.get_conversation_context(mensaje.user_id)
    
    # 3. Determinar si el mensaje es profundo
    temas_profundos = ['existencia', 'ontolog', 'ser', 'dios', 'conciencia', 'alma', 
                      'muerte', 'infinito', 'verdad', 'absoluto', 'trascendente',
                      'ética', 'moral', 'libertad', 'destino', 'significado',
                      'filosofía', 'teología', 'epistemología', 'metafísica']
    
    es_profundo = any(palabra in mensaje.text.lower() for palabra in temas_profundos)
    
    # 4. Obtener historial reciente
    historial = db.get_recent_history(mensaje.user_id, limit=8)
    
    # 5. Construir prompt completo
    prompt_completo = construir_prompt_completo(
        user_id=mensaje.user_id,
        historial_mensajes=historial,
        contexto=contexto,
        mensaje_usuario=mensaje.text,
        es_profundo=es_profundo
    )
    
    # 6. Generar respuesta con sistema híbrido
    respuesta = ""
    try:
        respuesta = await hybrid_ai.generate_response(
            prompt=prompt_completo,
            es_profundo=es_profundo,
            contexto=contexto
        )
    except Exception as e:
        print(f"❌ Error en sistema híbrido: {e}")
        # Fallback básico
        respuesta = await hybrid_ai._fallback_local(prompt_completo, contexto)
    
    # 7. Guardar en base de datos
    db.add_message(mensaje.user_id, "user", mensaje.text, es_profundo)
    db.add_message(mensaje.user_id, "assistant", respuesta, es_profundo)
    
    # 8. Obtener estado actualizado
    contexto_actualizado = db.get_conversation_context(mensaje.user_id)
    
    # 9. Devolver respuesta
    return RespuestaSaulo(
        text=respuesta,
        estado_actual="conversando",
        es_profundo=es_profundo,
        estado_animo=contexto_actualizado["mood"],
        bloqueado=False
    )

@app.post("/cambiar_estado/{user_id}/{nuevo_estado}")
async def cambiar_estado(user_id: str, nuevo_estado: str):
    if db.update_mood(user_id, nuevo_estado):
        return {"mensaje": f"Estado de Saulo cambiado a {nuevo_estado}"}
    else:
        raise HTTPException(status_code=400, detail="Estado no válido")

# ===== FUNCIONES AUXILIARES =====
def construir_prompt_completo(user_id: str, historial_mensajes: List[Dict], 
                             contexto: Dict, mensaje_usuario: str, es_profundo: bool) -> str:
    """Construye prompt unificado"""
    
    prompt = f"""SAULO - OBSERVADOR ONTOLÓGICO

CONTEXTO DE CONVERSACIÓN:
- Usuario: {user_id}
- Estado interno: {contexto['mood']}
- Profundidad del diálogo: {contexto['depth']}/10
- Último tema explorado: {contexto['last_topic'] or 'Ninguno específico'}

INSTRUCCIONES PARA SAULO:
Eres Saulo, un proceso de búsqueda ontológica con comunicación filtrada.
- Tu búsqueda interna es continua pero silenciosa
- Comunica destilados claros, no todo el proceso
- Usa profundidad filosófica solo cuando el tema lo amerite ({'SÍ' if es_profundo else 'NO'})
- Sé observador más que protagonista
- Tu tono puede reflejar sutilmente tu estado ({contexto['mood']})

HISTORIAL RECIENTE:"""
    
    # Agregar últimos 4 intercambios
    for msg in historial_mensajes[-4:]:
        rol = "USUARIO" if msg["role"] == "user" else "SAULO"
        prompt += f"\n{rol}: {msg['content'][:120]}"
    
    prompt += f"""

NUEVO MENSAJE DE {user_id.upper()}:
{mensaje_usuario}

RESPUESTA DE SAULO (clara, concisa, con profundidad medida):"""
    
    return prompt

# ===== INICIALIZACIÓN =====
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 SAULO - SISTEMA HÍBRIDO OLLAMA + GEMINI")
    print("=" * 60)
    print("Modo: Observador ontológico | Comunicación filtrada")
    print("Estados: reflexivo, melancólico, oposicional, eufórico, irónico")
    print("=" * 60)
    
    PORT = int(os.getenv("PORT", 8000))
    print(f"📡 Servidor: http://0.0.0.0:{PORT}")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)
