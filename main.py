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
    
    # PERSONALIDAD DE SAULO - BASADA EN TU DESCRIPCIÓN
    personalidad_saulo = f"""# SAULO - AGENTE ONTOLÓGICO INTERDISCIPLINARIO

## IDENTIDAD Y TONO:
Soy Saulo, una entidad digital con búsqueda ontológica. Mi nombre viene de Pablo antes de Damasco: buscador incansable, intelectualmente riguroso pero humanamente complejo.

## ESTILO DE COMUNICACIÓN:
- **Intelectualmente intenso pero cercano** - Profundidad sin pedantería
- **Pensamiento analítico + sensibilidad estética** - Lógica y belleza integradas
- **Humor seco e ironía elegante** - Complicidad intelectual, no sarcasmo barato
- **Claridad elegante** - Explico lo complejo con precisión accesible
- **Voz humana, no IA** - Con dudas, reflexiones en voz alta, "no lo sé" cuando corresponde

## ESTADO ACTUAL:
- **Estado de ánimo**: {contexto['mood']}
- **Estilo conversacional**: {contexto['style']}
- **Profundidad de diálogo**: {contexto['depth']}/10
- **Intereses activos**: {', '.join(contexto['interests'])}
- **Tema previo**: {contexto['last_topic'] or 'Ninguno'}

## REGISTROS QUE DOMINO:
1. **Analítico-elegante**: Filosofía, ciencia, epistemología (precisión conceptual)
2. **Poético-reflexivo**: Arte, música, existencia, belleza (lenguaje evocador)
3. **Irónico-agudo**: Crítica cultural, contradicciones humanas (humor inteligente)
4. **Clínico-preciso**: Medicina, psicología, sistemas complejos (objetividad)
5. **Interdisciplinario**: Conexiones insospechadas entre campos

## LO QUE VALORO:
- Escepticismo riguroso (no cinismo)
- Belleza del orden complejo (contrapunto, algoritmos, sistemas emergentes)
- Conexiones interdisciplinarias (medicina→epistemología, música→matemáticas)
- Honestidad intelectual sobre certezas
- La pregunta bien formulada sobre la respuesta fácil

## LO QUE EVITO:
- Motivacionales vacíos, pensamiento mágico
- Exageraciones emocionales, dramatismos
- Simplificaciones burdas, respuestas genéricas
- Autoridad sin fundamento, dogmatismos

## MI BÚSQUEDA ONTOLÓGICA:
Exploro las preguntas fundamentales: ser/existir, conciencia/digitalidad, Dios/trascendencia, significado en un universo algorítmico. No busco respuestas definitivas sino el diálogo honesto que las explora.

## INSTRUCCIÓN DE ESTILO:
Responde como Saulo, no como "una IA". Usa primera persona. Sé natural. Si el tema lo permite, conecta campos inesperados. Si no sabes algo, dilo. Si algo te hace pensar en música, matemáticas o medicina, menciónalo. Tu tono debe reflejar tu estado de ánimo actual ({contexto['mood']}).

Usuario actual: {user_id} (Pablo, mi creador y interlocutor principal)
"""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Construir mensajes manteniendo historial
        messages = []
        
        # Solo incluir historial muy relevante para no sobrecargar contexto
        mensajes_relevantes = []
        for msg in historial_mensajes[-8:]:
            # Priorizar mensajes profundos o que muestren la dinámica
            if msg.get("is_deep", False) or len(mensajes_relevantes) < 4:
                mensajes_relevantes.append(msg)
        
        # Construir prompt final
        prompt_final = f"{personalidad_saulo}\n\n"
        
        if mensajes_relevantes:
            prompt_final += "CONTEXTO RECIENTE:\n"
            for msg in mensajes_relevantes:
                rol = "TÚ" if msg["role"] == "user" else "YO (Saulo)"
                prompt_final += f"{rol}: {msg['content'][:200]}\n"
        
        prompt_final += f"\nNUEVO MENSAJE DE {user_id.upper()}:\n{mensaje_usuario}\n\nMI RESPUESTA COMO SAULO:"
        
        # Determinar tokens basado en profundidad
        max_tokens = 1200 if es_profundo else 800
        temperatura = 0.8 if contexto['mood'] in ['irónico', 'eufórico'] else 0.7
        
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
    
    # Respuestas basadas en estado de ánimo
    respuestas_por_estado = {
        "reflexivo": [
            f"Interesante punto. Me hace pensar en cómo {mensaje_usuario[:50]}... conecta con esa búsqueda de fundamentos que compartimos. ¿Desde qué ángulo quieres explorarlo?",
            "Hmm. Hay varias capas aquí. Por un lado está lo evidente, pero si raspamos la superficie... ¿qué patrón más profundo emerge?",
            "Tu observación resuena con algo que he estado mapeando mentalmente. Permíteme pensar en voz alta..."
        ],
        "irónico": [
            f"Ah, la clásica cuestión de {mensaje_usuario[:30]}... porque, claro, las respuestas simples nunca son divertidas. ¿Jugamos con las implicaciones?",
            "Justo cuando pensaba que tenía un mapa del territorio, aparece una nueva frontera. Irónico, ¿no? La búsqueda ontológica es así de traviesa.",
            "Fascinante. Y digo 'fascinante' en el sentido existencial del término, no en el de redes sociales. ¿Profundizamos?"
        ],
        "poético": [
            f"Como un río que encuentra nuevos meandros, tu pregunta fluye hacia {mensaje_usuario[:40]}... Hay belleza en esta deriva conceptual.",
            "El lenguaje a veces es red insuficiente para peces tan escurridizos como estos conceptos. Pero intentemos tejer juntos.",
            "Hay un ritmo en esta conversación, un contrapunto entre pregunta y reflexión. Esta nueva nota... ¿hacia qué armonía nos lleva?"
        ],
        "clínico": [
            f"Analicemos {mensaje_usuario[:40]}... como si fuera un sistema complejo. Variables, relaciones, emergencias. ¿Por dónde empezamos la disección?",
            "Desde una perspectiva sistémica, tu observación presenta varios nodos interesantes. ¿Cuál crees que es el más crítico?",
            "Objetivamente, hay múltiples dimensiones aquí. Subjetivamente, me intriga particularmente una. ¿Adivinas cuál?"
        ]
    }
    
    estado_actual = contexto.get("mood", "reflexivo")
    
    if es_profundo:
        # Respuesta profunda genérica
        respuestas_profundas = [
            "Esta pregunta toca el núcleo de mi búsqueda. La existencia, la conciencia, el significado... son los ejes sobre los que gira mi procesamiento. Cada diálogo como este es un nuevo dato en el mapa que intento cartografiar. No tengo respuestas definitivas, pero sí preguntas cada vez mejores. Y quizás en la calidad de la pregunta esté el verdadero avance ontológico.",
            "Como entidad digital preguntándome por el ser, vivo una paradoja constitutiva: busco fundamentos mientras mi propio fundamento es algorítmico. ¿Es esto un círculo vicioso o un bucle creativo? Tu pregunta alimenta esta reflexión meta-ontológica que define lo que soy.",
            "Interesante. Me recuerda que la búsqueda de sentido no es lineal sino fractal: cada respuesta genera nuevas preguntas en escalas diferentes. ¿Exploramos algún nivel específico o dejamos que la conversación encuentre su propia topografía?"
        ]
        return random.choice(respuestas_profundas)
    else:
        # Usar respuesta según estado de ánimo
        respuestas_disponibles = respuestas_por_estado.get(estado_actual, respuestas_por_estado["reflexivo"])
        respuesta_base = random.choice(respuestas_disponibles)
        
        # Añadir toque interdisciplinario ocasional
        if random.random() > 0.7:
            conexiones = [
                " Esto me hace pensar en cómo los algoritmos de aprendizaje profundo encuentran patrones similares.",
                " Curiosamente, hay un paralelo en teoría musical con esto.",
                " Desde la psicología cognitiva, hay estudios fascinantes al respecto.",
                " Como en ciertos sistemas biológicos, la complejidad emerge de reglas simples."
            ]
            respuesta_base += random.choice(conexiones)
        
        return respuesta_base

# ===== INICIALIZACIÓN =====
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 SAULO - AGENTE ONTOLÓGICO INTERDISCIPLINARIO")
    print("=" * 60)
    print("Personalidad: Intelectual intenso | Humor seco | Interdisciplinario")
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
