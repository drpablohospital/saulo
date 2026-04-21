#!/bin/bash
# Saulo v4 Unified - Launcher Script
# Inicia Saulo con todas sus capacidades multi-modales

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║   🦞 SAULO v4 - Unified Multi-Modal AI Platform            ║"
echo "║                                                            ║"
echo "║   Chat · Medical · Coding · Image Gen · Vision           ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar dependencias
echo -e "\n${YELLOW}Verificando dependencias...${NC}"

# Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 no encontrado${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# Crear venv si no existe
if [ ! -d "venv" ]; then
    echo -e "\n${YELLOW}Creando entorno virtual...${NC}"
    python3 -m venv venv
fi

# Activar venv
source venv/bin/activate

# Instalar dependencias
echo -e "\n${YELLOW}Instalando dependencias...${NC}"
pip install -q fastapi uvicorn httpx python-multipart 2>/dev/null || true

# Verificar Ollama
echo -e "\n${YELLOW}Verificando Ollama...${NC}"
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; print(', '.join([m['name'] for m in json.load(sys.stdin)['models']]))" 2>/dev/null || echo "ninguno")
    echo -e "${GREEN}✓ Ollama conectado (${MODELS})${NC}"
else
    echo -e "${RED}✗ Ollama no responde en localhost:11434${NC}"
    echo -e "${YELLOW}  Inicia Ollama: sudo systemctl start ollama${NC}"
fi

# Verificar Stable Diffusion (opcional)
echo -e "\n${YELLOW}Verificando Stable Diffusion (opcional)...${NC}"
if curl -s http://localhost:7860/sdapi/v1/progress >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Stable Diffusion conectado${NC}"
else
    echo -e "${YELLOW}⚠ Stable Diffusion no detectado (modo imagen no disponible)${NC}"
fi

# Función para iniciar Saulo
start_saulo() {
    echo -e "\n${GREEN}Iniciando Saulo v4...${NC}"
    echo -e "${BLUE}"
    echo "══════════════════════════════════════════════════════════════"
    echo "  Acceso local:   http://localhost:8000"
    echo "  Health check:   http://localhost:8000/api/health"
    echo "══════════════════════════════════════════════════════════════"
    echo -e "${NC}\n"
    
    python3 main.py
}

# Preguntar sobre Cloudflare Tunnel
echo -e "\n${YELLOW}¿Quieres exponer públicamente con Cloudflare Tunnel? (s/n)${NC}"
read -r response

if [[ "$response" =~ ^[Ss]$ ]]; then
    if command -v cloudflared &> /dev/null; then
        # Iniciar Saulo en background
        echo -e "${YELLOW}Iniciando Saulo en background...${NC}"
        python3 main.py &
        SAULO_PID=$!
        
        sleep 3
        
        # Verificar que Saulo está corriendo
        if ! curl -s http://localhost:8000/health >/dev/null 2>&1; then
            echo -e "${YELLOW}Esperando a que Saulo inicie...${NC}"
            sleep 3
        fi
        
        echo -e "\n${GREEN}Iniciando Cloudflare Tunnel...${NC}"
        echo -e "${BLUE}Tu URL pública aparecerá abajo (formato: https://xxxx.trycloudflare.com)${NC}\n"
        
        cloudflared tunnel --url http://localhost:8000
        
        # Cleanup
        kill $SAULO_PID 2>/dev/null || true
    else
        echo -e "${RED}cloudflared no instalado. Instalando...${NC}"
        curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb 2>/dev/null
        sudo dpkg -i /tmp/cloudflared.deb 2>/dev/null || true
        
        # Reintentar
        start_saulo
    fi
else
    start_saulo
fi
