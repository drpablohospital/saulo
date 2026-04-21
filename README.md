# Saulo v4 - Unified AI Platform

Multi-modal AI platform with medical evidence search, code assistance, Stable Diffusion image generation, and vision analysis.

## Features

- 💬 **Multi-modal Chat**: General, Medical, Coding, Images, Vision
- 🏥 **Medical Mode**: PubMed/Cochrane evidence search
- 💻 **Code Mode**: Bug analysis and auto-fix suggestions
- 🎨 **Image Generation**: Stable Diffusion integration
- 👁️ **Vision**: Image analysis with LLaVA
- 🤖 **Discord Bot**: Integrated chatbot
- 🖼️ **RPG Mascot**: Random quotes and personality

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn main:app --host 0.0.0.0 --port 8090
```

## URLs

- Production: https://chat.dogma.tools

## Tech Stack

- FastAPI + Python 3.12
- Ollama (local LLMs)
- Stable Diffusion
- Cloudflare Tunnel

## License

MIT - By Langosta & Xiu
