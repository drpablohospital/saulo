# Saulo v4 - Unified AI Platform

Multi-modal AI platform with medical evidence search, code assistance, Stable Diffusion image generation, and vision analysis.

## Features

- 💬 **Multi-modal Chat**: General, Medical, Coding, Images, Vision
- 🏥 **Medical Mode**: PubMed/Cochrane evidence search  
- 💻 **Code Mode**: Bug analysis and auto-fix suggestions
- 🎨 **Image Generation**: Stable Diffusion integration (local + cloud fallback)
- 👁️ **Vision**: Image analysis with LLaVA
- 🤖 **Discord Bot**: Integrated chatbot
- 🖼️ **RPG Mascot**: Random quotes and personality

## Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) installed and running
- (Optional) Stable Diffusion running on :7860

### Installation

```bash
# Clone repository
git clone https://github.com/drpablohospital/saulo.git
cd saulo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start server
uvicorn main:app --host 0.0.0.0 --port 8090
```

### Environment Variables

Create `.env` file with:

```
# Ollama (required)
OLLAMA_URL=http://127.0.0.1:11434

# Stable Diffusion (optional)
SD_URL=http://127.0.0.1:7860

# Cloud LLM fallback (optional)
OPENROUTER_API_KEY=your_key_here

# Tavily Search (optional)
TAVILY_API_KEY=your_key_here
```

## URLs

- Production: https://chat.dogma.tools

## Tech Stack

- FastAPI + Python 3.12
- Ollama (local LLMs)
- Stable Diffusion
- Cloudflare Tunnel

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/models` - Available models
- `POST /api/chat` - Chat completion (streaming)
- `POST /api/image/generate` - Image generation
- `POST /api/vision` - Vision analysis

## License

MIT - By Langosta & Xiu
