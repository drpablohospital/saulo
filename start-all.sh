#!/bin/bash
# Saulo + Stable Diffusion Launcher
# Inicia todos los servicios necesarios

echo "🚀 Saulo + SD Launcher"
echo "======================"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para verificar si un puerto está libre
check_port() {
    lsof -i :$1 >/dev/null 2>&1
    return $?
}

# 1. Verificar/iniciar Stable Diffusion
echo ""
echo "📸 Verificando Stable Diffusion..."
if check_port 7860; then
    echo -e "${YELLOW}⚠️  SD ya está corriendo en puerto 7860${NC}"
else
    echo "🔄 Iniciando Stable Diffusion WebUI..."
    cd /home/xiu/stable-diffusion-webui || exit 1
    
    export COMMANDLINE_ARGS="--listen --port 7860 --xformers --enable-insecure-extension-access --api --no-half-vae --autolaunch"
    
    # Verificar que existe el entorno virtual
    if [ ! -d "venv" ]; then
        echo -e "${RED}❌ No se encontró venv en SD. Creando...${NC}"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        source venv/bin/activate
    fi
    
    nohup python webui.py > /tmp/sd.log 2>&1 &
    SD_PID=$!
    echo $SD_PID > /tmp/sd.pid
    echo -e "${GREEN}✅ SD iniciado (PID: $SD_PID)${NC}"
    
    # Esperar a que SD esté listo
    echo "⏳ Esperando a que SD esté listo..."
    for i in {1..60}; do
        sleep 2
        if curl -s http://localhost:7860/sdapi/v1/progress >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Stable Diffusion listo!${NC}"
            break
        fi
        echo -n "."
    done
fi

# 2. Verificar Ollama
echo ""
echo "🦙 Verificando Ollama..."
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama corriendo${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama no detectado. Iniciando...${NC}"
    # Intentar iniciar ollama si está instalado
    if command -v ollama >/dev/null 2>&1; then
        ollama serve &
        sleep 3
    else
        echo -e "${YELLOW}⚠️  Ollama no instalado. Saltando...${NC}"
    fi
fi

# 3. Iniciar Saulo
echo ""
echo "🤖 Iniciando Saulo..."
cd /home/xiu/.openclaw/workspace/saulo-unified || exit 1

# Verificar entorno virtual
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ No se encontró venv en Saulo${NC}"
    exit 1
fi

source venv/bin/activate

# Detener instancia anterior si existe
pkill -f "python.*main.py" 2>/dev/null
sleep 2

# Iniciar Saulo
export SAULO_PORT=8000
export SD_URL=http://127.0.0.1:7860
export OLLAMA_URL=http://127.0.0.1:11434

nohup python main.py > /tmp/saulo.log 2>&1 &
SAULO_PID=$!
echo $SAULO_PID > /tmp/saulo.pid

echo -e "${GREEN}✅ Saulo iniciado (PID: $SAULO_PID)${NC}"

# Esperar a que Saulo esté listo
echo "⏳ Verificando Saulo..."
for i in {1..30}; do
    sleep 1
    if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Saulo listo!${NC}"
        break
    fi
    echo -n "."
done

echo ""
echo "======================"
echo -e "${GREEN}🎉 Todo listo!${NC}"
echo ""
echo "📊 URLs de acceso:"
echo "   • Saulo UI:      http://localhost:8000"
echo "   • Saulo Health:  http://localhost:8000/api/health"
echo "   • SD WebUI:      http://localhost:7860"
echo "   • SD API:        http://localhost:7860/sdapi/v1"
echo ""
echo "📝 Logs:"
echo "   • Saulo: tail -f /tmp/saulo.log"
echo "   • SD:    tail -f /tmp/sd.log"
echo ""
echo "🛑 Para detener:"
echo "   • Saulo: kill $(cat /tmp/saulo.pid)"
echo "   • SD:    kill $(cat /tmp/sd.pid)"
echo ""
