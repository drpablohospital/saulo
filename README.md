# Saulo Platform v4

**Sistema Multi-Modal de IA con Vision Router y Agentes Inteligentes**

Saulo es una plataforma de IA conversacional con múltiples modos especializados, integración con Ollama (local) y modelos cloud (Kimi, Claude), más un router inteligente para análisis de imágenes.

## 🚀 Características

### Modos de Operación
- **General**: Chat general con memoria y contexto
- **Médico**: Búsqueda en PubMed + respuestas basadas en evidencia
- **Código**: Análisis de código, debugging y sugerencias
- **Visión**: Análisis de imágenes con LLaVA y modelos especializados
- **Imágenes**: Generación con Stable Diffusion

### Integraciones
- 🤖 **Ollama**: Modelos locales (Llama, Mistral, etc.)
- ☁️ **Cloud**: Kimi k1.5, Claude 3.5 via OpenRouter
- 🏥 **PubMed**: Búsqueda de evidencia médica
- 🎨 **Stable Diffusion**: Generación de imágenes
- 🔍 **Vision Router**: Detección automática de intención en imágenes

## 📦 Instalación

```bash
# Clonar repositorio
git clone https://github.com/xiutek/saulo-platform.git
cd saulo-platform

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys

# Iniciar
uvicorn main:app --host 0.0.0.0 --port 8090
```

## ⚙️ Configuración

Variables de entorno en `.env`:
```
OLLAMA_URL=http://localhost:11434
SD_URL=http://localhost:7860
OPENROUTER_API_KEY=tu_key_aqui
SEARCH_API_KEY=tu_key_aqui
```

## 🏗️ Arquitectura

```
saulo-unified/
├── main.py                 # API FastAPI principal
├── terminal_ssh_module.py  # Integración con OpenClaw
├── static/
│   ├── app.js             # Frontend
│   └── style.css          # Estilos
├── venv/                  # Entorno virtual
└── uploads/               # Imágenes subidas
```

## 🛠️ Tecnologías

- **Backend**: FastAPI, Python 3.12
- **Frontend**: Vanilla JS, SSE streaming
- **LLMs**: Ollama, OpenRouter (Kimi, Claude)
- **Visión**: LLaVA, Vision Router personalizado
- **DB**: SQLite (conversaciones)

## 📝 Changelog

### v4.1.0 (2026-04-15)
- Fix: Variable `prompt` no definida en modo image
- Fix: Frontend mostraba JSON crudo en lugar de streaming
- Mejora: Streaming de respuestas en tiempo real

### v4.0.0 (2026-04-14)
- Vision Router con detección de intención
- Integración con OpenClaw/Langosta
- Multi-modal completo

## 👨‍💻 Autor

**Xiu** - [xiutek@dogma.tools](mailto:xiutek@dogma.tools)

## 📄 Licencia

MIT License - CIUMMP 2026
