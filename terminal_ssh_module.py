"""
Módulo de Terminal SSH para Saulo
Acceso remoto protegido al desktop
"""

import os
import subprocess
import asyncio
from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from datetime import datetime

# Configuración
SSH_KEY_PATH = "/home/xiu/.ssh/langosta_key"
DESKTOP_USER = "xiu"
DESKTOP_HOST = "localhost"  # O la IP de Tailscale si es remoto
ADMIN_PASSWORD = "e1416"  # Misma que Sinapsid

class CommandRequest(BaseModel):
    command: str
    password: str

class TerminalSSH:
    def __init__(self):
        self.session_history = []
        
    def verify_password(self, password: str) -> bool:
        """Verificar contraseña de admin"""
        return password == ADMIN_PASSWORD
    
    async def execute_ssh_command(self, command: str) -> dict:
        """Ejecutar comando vía SSH"""
        try:
            # Construir comando SSH
            ssh_cmd = [
                "ssh",
                "-i", SSH_KEY_PATH,
                "-o", "StrictHostKeyChecking=no",
                "-o", "BatchMode=yes",
                f"{DESKTOP_USER}@{DESKTOP_HOST}",
                command
            ]
            
            # Ejecutar
            process = await asyncio.create_subprocess_exec(
                *ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=30.0
            )
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "returncode": process.returncode,
                "timestamp": datetime.now().isoformat()
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Timeout: comando tomó más de 30 segundos",
                "returncode": -1,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_terminal_html(self) -> str:
        """HTML de la terminal"""
        return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Saulo Terminal SSH</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: #1a1a2e;
            color: #eee;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: #16213e;
            padding: 15px 20px;
            border-bottom: 2px solid #0f3460;
        }
        
        .header h1 {
            font-size: 1.2rem;
            color: #e94560;
        }
        
        .header .subtitle {
            font-size: 0.8rem;
            color: #888;
            margin-top: 5px;
        }
        
        .terminal-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 20px;
            overflow: hidden;
        }
        
        #output {
            flex: 1;
            background: #0f0f23;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 15px;
            overflow-y: auto;
            font-size: 0.9rem;
            line-height: 1.5;
            white-space: pre-wrap;
            word-break: break-all;
        }
        
        .output-line {
            margin: 2px 0;
        }
        
        .output-line.error {
            color: #ff6b6b;
        }
        
        .output-line.success {
            color: #51cf66;
        }
        
        .output-line.prompt {
            color: #e94560;
            font-weight: bold;
        }
        
        .input-area {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            padding: 15px;
            background: #16213e;
            border-radius: 8px;
        }
        
        .input-area input {
            flex: 1;
            background: #0f0f23;
            border: 1px solid #333;
            color: #eee;
            padding: 12px 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.95rem;
            border-radius: 6px;
            outline: none;
        }
        
        .input-area input:focus {
            border-color: #e94560;
        }
        
        .input-area button {
            background: #e94560;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            font-size: 0.9rem;
            transition: background 0.2s;
        }
        
        .input-area button:hover {
            background: #c73e54;
        }
        
        .input-area button:disabled {
            background: #555;
            cursor: not-allowed;
        }
        
        .password-modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .password-box {
            background: #1a1a2e;
            padding: 40px;
            border-radius: 12px;
            border: 2px solid #e94560;
            text-align: center;
            max-width: 400px;
        }
        
        .password-box h2 {
            color: #e94560;
            margin-bottom: 20px;
        }
        
        .password-box input {
            width: 100%;
            padding: 15px;
            margin: 10px 0;
            background: #0f0f23;
            border: 1px solid #333;
            color: #eee;
            border-radius: 6px;
            font-size: 1rem;
        }
        
        .password-box button {
            width: 100%;
            padding: 15px;
            margin-top: 10px;
            background: #e94560;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            cursor: pointer;
        }
        
        .hidden {
            display: none !important;
        }
        
        .status-bar {
            display: flex;
            justify-content: space-between;
            padding: 10px 20px;
            background: #16213e;
            font-size: 0.8rem;
            color: #888;
            border-top: 1px solid #333;
        }
        
        .status-connected {
            color: #51cf66;
        }
        
        .status-disconnected {
            color: #ff6b6b;
        }
    </style>
</head>
<body>
    <div id="passwordModal" class="password-modal">
        <div class="password-box">
            <h2>🔐 Terminal SSH</h2>
            <p style="color: #888; margin-bottom: 20px;">Acceso protegido a Desktop</p>
            <input type="password" id="passwordInput" placeholder="Contraseña de admin" onkeypress="handleKeyPress(event)">
            <button onclick="verifyPassword()">Acceder</button>
            <p id="errorMsg" style="color: #ff6b6b; margin-top: 10px; display: none;">Contraseña incorrecta</p>
        </div>
    </div>
    
    <div class="header">
        <h1>🖥️ Saulo Terminal SSH</h1>
        <div class="subtitle">Desktop @ ''' + DESKTOP_HOST + ''' | User: ''' + DESKTOP_USER + '''</div>
    </div>
    
    <div class="terminal-container">
        <div id="output"></div>
        
        <div class="input-area">
            <span style="color: #e94560; font-weight: bold; padding: 12px 0;">$</span>
            <input type="text" id="commandInput" placeholder="Escribe un comando (ej: ls, pwd, ps aux)" autocomplete="off">
            <button id="sendBtn" onclick="sendCommand()">Ejecutar</button>
        </div>
    </div>
    
    <div class="status-bar">
        <span id="statusText">Esperando autenticación...</span>
        <span id="lastCmd">Sin comandos ejecutados</span>
    </div>
    
    <script>
        let authenticated = false;
        let commandHistory = [];
        let historyIndex = -1;
        
        function verifyPassword() {
            const password = document.getElementById('passwordInput').value;
            // Guardar password para requests
            window.terminalPassword = password;
            
            document.getElementById('passwordModal').classList.add('hidden');
            authenticated = true;
            
            addOutput('🔓 Acceso concedido. Terminal SSH lista.', 'success');
            addOutput('💡 Comandos útiles: ls, pwd, ps aux, df -h, free -h', 'prompt');
            addOutput('⚠️ Ten cuidado con comandos destructivos (rm, etc.)\\n', 'prompt');
            
            document.getElementById('statusText').innerHTML = '<span class="status-connected">●</span> Conectado';
            document.getElementById('commandInput').focus();
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                verifyPassword();
            }
        }
        
        async function sendCommand() {
            const input = document.getElementById('commandInput');
            const btn = document.getElementById('sendBtn');
            const command = input.value.trim();
            
            if (!command) return;
            
            // Guardar en historial
            commandHistory.push(command);
            historyIndex = commandHistory.length;
            
            // Mostrar comando
            addOutput('$ ' + command, 'prompt');
            
            // Deshabilitar input
            input.disabled = true;
            btn.disabled = true;
            btn.textContent = 'Ejecutando...';
            
            try {
                const response = await fetch('/api/terminal/execute', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        command: command,
                        password: window.terminalPassword
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    if (result.stdout) addOutput(result.stdout, 'success');
                    if (result.stderr) addOutput(result.stderr, 'error');
                } else {
                    addOutput('Error: ' + (result.error || 'Comando falló'), 'error');
                }
                
                document.getElementById('lastCmd').textContent = 'Último: ' + new Date().toLocaleTimeString();
                
            } catch (error) {
                addOutput('Error de conexión: ' + error.message, 'error');
            }
            
            // Rehabilitar input
            input.disabled = false;
            btn.disabled = false;
            btn.textContent = 'Ejecutar';
            input.value = '';
            input.focus();
        }
        
        function addOutput(text, className) {
            const output = document.getElementById('output');
            const line = document.createElement('div');
            line.className = 'output-line ' + className;
            line.textContent = text;
            output.appendChild(line);
            output.scrollTop = output.scrollHeight;
        }
        
        // Historial con flechas
        document.getElementById('commandInput').addEventListener('keydown', function(e) {
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (historyIndex > 0) {
                    historyIndex--;
                    this.value = commandHistory[historyIndex] || '';
                }
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (historyIndex < commandHistory.length - 1) {
                    historyIndex++;
                    this.value = commandHistory[historyIndex] || '';
                } else {
                    historyIndex = commandHistory.length;
                    this.value = '';
                }
            } else if (e.key === 'Enter') {
                sendCommand();
            }
        });
        
        // Focus inicial
        document.getElementById('passwordInput').focus();
    </script>
</body>
</html>'''

# Instancia global
terminal_ssh = TerminalSSH()

# Endpoints para integrar en main.py de Saulo
'''
# Agregar estas líneas al final de main.py antes de if __name__:

# Terminal SSH endpoints
@app.get("/terminal", response_class=HTMLResponse)
async def terminal_page():
    """Página de terminal SSH"""
    return terminal_ssh.get_terminal_html()

@app.post("/api/terminal/execute")
async def terminal_execute(request: CommandRequest):
    """Ejecutar comando SSH"""
    if not terminal_ssh.verify_password(request.password):
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": "Contraseña incorrecta"}
        )
    
    # Validar comando (lista negra básica)
    dangerous = ['rm -rf /', 'mkfs', 'dd if=/dev/zero', ':(){ :|:& };:']
    if any(d in request.command for d in dangerous):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Comando peligroso bloqueado"}
        )
    
    result = await terminal_ssh.execute_ssh_command(request.command)
    return result

# Agregar enlace en el menú de Saulo (index.html)
# <a href="/terminal">🖥️ Terminal</a>
'''
