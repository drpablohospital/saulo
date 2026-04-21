# Guía de Instalación Completa - Saulo v4

Esta guía te lleva desde cero hasta tener Saulo funcionando en tu computadora.

---

## 📋 Requisitos Previos

- **Sistema**: Linux, macOS, o Windows con WSL
- **Python**: 3.10 o superior
- **RAM**: 8GB mínimo (16GB recomendado)
- **Espacio**: 10GB libres (para modelos)
- **GPU**: Opcional pero recomendada para Stable Diffusion

---

## Paso 1: Instalar Ollama (OBLIGATORIO)

Ollama es el motor que corre los modelos de IA localmente.

### Linux/macOS:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Verificar instalación:
```bash
ollama --version
```

### Iniciar Ollama:
```bash
ollama serve
```

Deja esta terminal abierta. Ollama debe estar corriendo para que Saulo funcione.

---

## Paso 2: Descargar Modelos de Ollama

En otra terminal, descarga los modelos que usa Saulo:

### Modelo principal (requerido):
```bash
ollama pull llama3.2
```

### Modelo para código (opcional pero recomendado):
```bash
ollama pull qwen2.5:7b
```

### Modelo para visión (opcional):
```bash
ollama pull llava
```

### Verificar modelos instalados:
```bash
ollama list
```

Deberías ver algo como:
```
NAME            ID              SIZE    MODIFIED
llama3.2:latest    ...         2.0 GB  ...
qwen2.5:7b:latest  ...         4.4 GB  ...
```

---

## Paso 3: Instalar Saulo

### 1. Clonar el repositorio:
```bash
git clone https://github.com/drpablohospital/saulo.git
cd saulo
```

### 2. Crear ambiente virtual:
```bash
python3 -m venv venv
```

### 3. Activar ambiente virtual:

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 4. Instalar dependencias:
```bash
pip install -r requirements.txt
```

Esto instalará FastAPI, Uvicorn, y todas las librerías necesarias.

### 5. Configurar variables de entorno:
```bash
cp .env.example .env
```

Opcional: Edita `.env` si quieres cambiar puertos o agregar claves de API.

---

## Paso 4: Ejecutar Saulo

### Opción A - Script automático:
```bash
./start.sh
```

### Opción B - Comando manual:
```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8090
```

### Verificar que funciona:
Abre tu navegador en: **http://localhost:8090**

O prueba la API:
```bash
curl http://localhost:8090/api/health
```

Debería responder algo como:
```json
{"status": "healthy", "version": "4.0.0", ...}
```

---

## Paso 5: Instalar Stable Diffusion (OPCIONAL)

Solo si quieres generar imágenes. Si no, Saulo usará un servicio en la nube.

### Opción recomendada: AUTOMATIC1111

```bash
# Clonar
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui

# Instalar dependencias (Linux)
python3 -m venv venv
source venv/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt

# Descargar un modelo (ejemplo: SD 1.5)
wget -P models/Stable-diffusion \
  "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.ckpt"

# Iniciar
./webui.sh --api --listen --port 7860
```

Con `--api` habilita la API REST que usa Saulo.

---

## 🐛 Solución de Problemas

### "Ollama not running":
Asegúrate de tener `ollama serve` corriendo en otra terminal.

### "Module not found":
Verifica que activaste el venv: `source venv/bin/activate`

### "Address already in use":
El puerto 8090 está ocupado. Cambia el puerto en `.env`:
```
SAULO_PORT=8091
```

### Modelos no aparecen:
Verifica que los descargaste: `ollama list`

### Problemas con permisos (Linux):
```bash
chmod +x start.sh
```

---

## 📁 Estructura del Proyecto

```
saulo/
├── main.py                 # Backend FastAPI
├── static/                 # Frontend HTML/CSS/JS
│   ├── index.html
│   ├── app.js
│   ├── quotes.js          # Frases de la mascota
│   └── sidebar-image.png   # Imagen de la mascota
├── venv/                   # Ambiente virtual (NO subir)
├── uploads/                # Archivos subidos
├── generated_images/       # Imágenes generadas
├── requirements.txt        # Dependencias
├── .env.example           # Configuración ejemplo
├── start.sh               # Script de inicio
└── README.md              # Documentación
```

---

## 🔄 Actualizar Saulo

Si hay nueva versión:
```bash
cd saulo
git pull
source venv/bin/activate
pip install -r requirements.txt  # Por si hay nuevas dependencias
```

---

## 📞 Soporte

Si tienes problemas:
1. Revisa que Ollama esté corriendo
2. Verifica que los modelos estén descargados
3. Revisa los logs: `cat /tmp/saulo.log` (si usaste start.sh)

URL de producción: https://chat.dogma.tools
