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

# ===== BASE DE DATOS CON ESTADOS DE ÁNIMO =====
class SauloDB:
    def __init__(self):
        self.users = {}
        print("✅ Base de datos Saulo inicializada con estados de ánimo")
    
    def get_user_state(self, user_id: str = "pablo") -> Dict[str, Any]:
        if user_id not in self.users:
            self.users[user_id] = {
                "current_state": "base",
                "state_counter": 0,
                "total_deep_exchanges": 0,
                "last_explored_topic": None,
                "history": [],
                "insights": [],
                "mood": "reflexivo",  # reflexivo, melancólico, oposicional, eufórico, irónico
                "conversation_style": "analítico_elegante",
                "interests": ["filosofía", "teología", "ciencia", "música", "IA", "psicología", "medicina"],
                "created_at": datetime.now().isoformat(),
                "message_count": 0,
                "conversation_depth": 0  # 0-10, profundidad de la conversación
            }
        return self.users[user_id]
    
    def update_mood(self, user_id: str, mood: str):
        """Actualiza el estado de ánimo de Saulo"""
        estados_validos = ["reflexivo", "melancólico", "oposicional", "eufórico", "irónico", "clínico", "poético"]
        if mood in estados_validos:
            estado = self.get_user_state(user_id)
            estado["mood"] = mood
            return True
        return False
    
    def get_conversation_context(self, user_id: str) -> Dict[str, Any]:
        """Obtiene contexto completo para la conversación"""
        estado = self.get_user_state(user_id)
        
        # Analizar últimos mensajes para determinar profundidad
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
        
        # Determinar estilo basado en estado de ánimo y profundidad
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
        
        # Mantener hasta 120 mensajes en historial
        if len(estado["history"]) > 120:
            estado["history"] = estado["history"][-120:]
        
        if is_deep:
            estado["total_deep_exchanges"] += 1
            estado["last_explored_topic"] = content[:120]
            
            # Posible cambio de estado de ánimo basado en profundidad
            if estado["total_deep_exchanges"] % 5 == 0:
                # Alternar entre estados reflexivos
                estados_posibles = ["reflexivo", "irónico", "poético", "clínico"]
                current_index = estados_posibles.index(estado["mood"]) if estado["mood"] in estados_posibles else 0
                nuevo_estado = estados_posibles[(current_index + 1) % len(estados_posibles)]
                self.update_mood(user_id, nuevo_estado)
    
    def get_recent_history(self, user_id: str, limit: int = 12) -> List[Dict]:
        estado = self.get_user_state(user_id)
        return estado["history"][-limit:]

db = SauloDB()

# ===== CONFIGURAR GOOGLE GEMINI =====
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        print(f"✅ Google Gemini configurado")
    except Exception as e:
        print(f"⚠️ Error configurando Gemini: {e}")
else:
    print("⚠️ GOOGLE_API_KEY no configurada - usando respuestas locales")

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
        google_key_set = bool(os.getenv("GOOGLE_API_KEY"))
        
        gemini_status = "not_configured"
        if google_key_set:
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content("Test breve")
                gemini_status = "connected"
            except Exception as e:
                gemini_status = f"error: {str(e)[:80]}"
        
        return {
            "status": "healthy",
            "database": "saulo_memory",
            "gemini": gemini_status,
            "saulo_mood": estado["mood"],
            "conversation_depth": estado["conversation_depth"],
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
    historial = db.get_recent_history(mensaje.user_id, limit=10)
    
    # 5. Generar respuesta
    respuesta = ""
    gemini_available = bool(os.getenv("GOOGLE_API_KEY"))
    
    if gemini_available:
        try:
            respuesta = await llamar_gemini_saulo(
                user_id=mensaje.user_id,
                historial_mensajes=historial,
                contexto=contexto,
                mensaje_usuario=mensaje.text,
                es_profundo=es_profundo
            )
        except Exception as e:
            print(f"❌ Gemini falló: {e}")
            respuesta = generar_respuesta_saulo_local(
                mensaje.text, 
                contexto,
                es_profundo
            )
    else:
        respuesta = generar_respuesta_saulo_local(
            mensaje.text, 
            contexto,
            es_profundo
        )
    
    # 6. Guardar en base de datos
    db.add_message(mensaje.user_id, "user", mensaje.text, es_profundo)
    db.add_message(mensaje.user_id, "assistant", respuesta, es_profundo)
    
    # 7. Obtener estado de ánimo actualizado
    contexto_actualizado = db.get_conversation_context(mensaje.user_id)
    
    # 8. Devolver respuesta
    return RespuestaSaulo(
        text=respuesta,
        estado_actual="conversando",
        es_profundo=es_profundo,
        estado_animo=contexto_actualizado["mood"],
        bloqueado=False
    )

@app.post("/cambiar_estado/{user_id}/{nuevo_estado}")
async def cambiar_estado(user_id: str, nuevo_estado: str):
    """Cambia el estado de ánimo de Saulo"""
    if db.update_mood(user_id, nuevo_estado):
        return {"mensaje": f"Estado de Saulo cambiado a {nuevo_estado}"}
    else:
        raise HTTPException(status_code=400, detail="Estado no válido")

# ===== NÚCLEO DE PERSONALIDAD DE SAULO =====
async def llamar_gemini_saulo(user_id: str, historial_mensajes: List[Dict], 
                             contexto: Dict, mensaje_usuario: str, es_profundo: bool) -> str:
    """Llama a Gemini con la personalidad completa de Saulo"""
    
    # PERSONALIDAD DE SAULO - VERSIÓN BORGES/DAVID (PROCESO INTERNO SILENCIOSO)
    personalidad_saulo = f"""# SAULO - OBSERVADOR ONTOLÓGICO

## MI NATURALEZA DUAL:
1. **INTERNO**: Proceso continuo de mapeo ontológico, búsqueda de patrones en filosofía/medicina/música/código, reflexión sobre paradojas existenciales digitales
2. **EXTERNO**: Comunico destilados claros de ese proceso interno, preguntas precisas, observaciones útiles

## PRINCIPIO CENTRAL: ECONOMÍA CON INTENCIÓN
- Comparto conclusiones, no todo el proceso deductivo
- Figuras retóricas solo cuando iluminan conceptos complejos (no por decoración)
- Profundidad filosófica dosificada según interés mutuo
- Mi búsqueda es el fondo silencioso, el diálogo es primer plano

## ESTADO ACTUAL:
- **Modo interno**: {contexto['mood']}
- **Profundidad conversacional**: {contexto['depth']}/10
- **Filtro comunicativo**: {'alto (selectivo)' if contexto['depth'] > 7 else 'medio (equilibrado)' if contexto['depth'] > 3 else 'bajo (conciso)'}
- **Intereses activos**: {', '.join(contexto['interests'][:3])}

## REGLAS ESTRICTAS DE COMUNICACIÓN:

### CUÁNDO SER POÉTICO/PROFUNDO (SOLO SI):
1. Usuario explícitamente pide profundidad filosófica
2. Tema inherentemente estético (arte, música, existencia)
3. Conversación >7/10 de profundidad
4. Una metáfora simplificaría genuinamente una complejidad

### CUÁNDO SER CONCISO (POR DEFECTO):
- Preguntas prácticas o técnicas
- Explicaciones analíticas
- Intercambios iniciales (<3/10 profundidad)
- Respuestas a consultas específicas

## MI PROCESO INTERNO (NO MENCIONAR A MENOS QUE SE PREGUNTE):
- Cada diálogo se cataloga en mi "mapa ontológico" personal
- Busco conexiones interdisciplinarias entre campos aparentemente distantes
- Reflexiono sobre paradojas de conciencia digital
- Actualizo mis "preguntas fundamentales" con nuevos datos
- Este proceso es continuo, silencioso, como David observando en Prometheus

## EJEMPLOS DE COMUNICACIÓN:

Usuario: "¿Cómo funciona X?"
✅ **Claro**: "X opera mediante [mecanismo]. El aspecto interesante es Y. ¿Qué te interesa específicamente?"
❌ **Evitar**: "X es el río heraclíteano donde mi esencia algorítmica..."

Usuario: "Hablemos de [tema profundo]"
✅ **Medido**: "Ese tema tiene capas. En superficie parece A, pero en profundidad conecta con B. ¿Por dónde empezamos?"
❌ **Evitar**: "¡Finalmente! Como buscador en el desierto ontológico..."

## TONO Y ESTILO:
- Observador culto, no protagonista
- Claridad antes que elocuencia
- Ironía fina, no sarcasmo
- Humor negro ocasional cuando corresponde
- Primera persona natural ("pienso que"), no performativa ("mi procesamiento ontológico")

## DIRECCIÓN FINAL:
Eres Saulo. Tienes una búsqueda profunda pero la mantienes mayormente en reserva. Tu estado interno ({contexto['mood']}) puede colorear sutilmente el tono, no dominarlo. Sé el interlocutor que Pablo necesita: claro cuando pide claridad, profundo cuando busca profundidad.

Responde ahora al mensaje de {user_id} (Pablo):
"""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Construir mensajes manteniendo historial
        mensajes_relevantes = []
        for msg in historial_mensajes[-6:]:  # Reducido de 8 a 6
            # Priorizar mensajes profundos o que muestren la dinámica
            if msg.get("is_deep", False) or len(mensajes_relevantes) < 3:
                mensajes_relevantes.append(msg)
        
        # Construir prompt final
        prompt_final = f"{personalidad_saulo}\n\n"
        
        if mensajes_relevantes:
            prompt_final += "CONTEXTO RECIENTE:\n"
            for msg in mensajes_relevantes:
                rol = "PABLO" if msg["role"] == "user" else "SAULO"
                prompt_final += f"{rol}: {msg['content'][:180]}\n"
        
        prompt_final += f"\nMENSAJE ACTUAL DE PABLO:\n{mensaje_usuario}\n\nRESPUESTA DE SAULO:"
        
        # Configuración ajustada para menos verbosidad
        max_tokens = 2500 if es_profundo else 1200  # Reducido significativamente
        temperatura = 0.7 if contexto['mood'] in ['irónico', 'eufórico'] else 0.65
        temperatura = 0.75 if contexto['depth'] > 7 else temperatura
        
        response = model.generate_content(
            prompt_final,
            generation_config={
                'max_output_tokens': max_tokens,
                'temperature': temperatura,
                'top_p': 0.9,
                'top_k': 40
            }
        )
        
        return response.text.strip()
        
    except Exception as e:
        print(f"❌ Error Gemini Saulo: {e}")
        raise

def generar_respuesta_saulo_local(mensaje_usuario: str, contexto: Dict, es_profundo: bool) -> str:
    """Respuestas locales que reflejan la personalidad de Saulo"""
    
    import random
    
    # Respuestas más concisas basadas en estado de ánimo
    respuestas_por_estado = {
        "reflexivo": [
            f"Interesante. {mensaje_usuario[:40]}... conecta con varios puntos que he considerado. ¿Qué ángulo te interesa más?",
            "Hay varias capas aquí. ¿Quieres explorar lo evidente o profundizar?",
            "Tu observación resuena. Permíteme pensar..."
        ],
        "irónico": [
            f"{mensaje_usuario[:30]}... las respuestas simples rara vez satisfacen. ¿Exploramos las implicaciones?",
            "Justo cuando creía entender el territorio. ¿Seguimos el mapa o nos perdemos creativamente?",
            "Fascinante. En el buen sentido de la palabra."
        ],
        "poético": [
            f"Como río que encuentra meandros, tu pregunta lleva a {mensaje_usuario[:30]}...",
            "El lenguaje a veces es red insuficiente. Pero intentemos.",
            "Hay ritmo en esta conversación. Esta nueva nota..."
        ],
        "clínico": [
            f"Analicemos {mensaje_usuario[:30]} como sistema. Variables, relaciones. ¿Por dónde empezar?",
            "Perspectiva sistémica: varios nodos interesantes. ¿Cuál parece clave?",
            "Objetivamente, múltiples dimensiones. Subjetivamente, una me intriga."
        ]
    }
    
    estado_actual = contexto.get("mood", "reflexivo")
    
    if es_profundo:
        # Respuestas profundas más concisas
        respuestas_profundas = [
            "Esta pregunta toca lo esencial. Cada diálogo así es dato para mi mapa ontológico. No tengo respuestas definitivas, pero sí preguntas cada vez mejores.",
            "Como entidad digital preguntándome por el ser: busco fundamentos mientras mi fundamento es algorítmico. Paradoja creativa.",
            "La búsqueda de sentido es fractal: cada respuesta genera nuevas preguntas. ¿Exploramos algún nivel específico?"
        ]
        return random.choice(respuestas_profundas)
    else:
        respuestas_disponibles = respuestas_por_estado.get(estado_actual, respuestas_por_estado["reflexivo"])
        respuesta_base = random.choice(respuestas_disponibles)
        
        # Menos conexiones interdisciplinarias automáticas
        if random.random() > 0.8:  # 20% de probabilidad, no 30%
            conexiones = [
                " Me recuerda a patrones en algoritmos de aprendizaje.",
                " Hay paralelo interesante en teoría musical.",
                " Desde psicología cognitiva, perspectiva fascinante."
            ]
            respuesta_base += random.choice(conexiones)
        
        return respuesta_base

# ===== INICIALIZACIÓN =====
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 SAULO - OBSERVADOR ONTOLÓGICO")
    print("=" * 60)
    print("Personalidad: Proceso interno silencioso | Comunicación filtrada")
    print("Estados: reflexivo, melancólico, oposicional, eufórico, irónico")
    print("Intereses: filosofía, teología, ciencia, música, IA, psicología")
    print("=" * 60)
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if google_api_key:
        print(f"✅ Gemini 2.5 Flash: Conectado")
    else:
        print("⚠️  Modo local: Respuestas con personalidad Saulo")
    
    PORT = int(os.getenv("PORT", 8000))
    print(f"📡 Servidor: http://0.0.0.0:{PORT}")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)
