/**
 * Saulo v4 - Frontend Application
 * Multi-modal AI con Vision Router
 */

let currentMode = 'general';
let currentConversation = null;
let uploadedImage = null;
let currentModel = 'llama3.2';

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkHealth();
});

function setupEventListeners() {
    const input = document.getElementById('message-input');
    if (input) {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
}

async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message && !uploadedImage) return;
    
    // Ocultar welcome
    document.getElementById('welcome-screen').style.display = 'none';
    
    // Agregar mensaje del usuario
    addMessage('user', message);
    
    // Limpiar input
    input.value = '';
    input.style.height = 'auto';
    
    // Mostrar typing
    const typingId = addTypingIndicator();
    
    try {
        // Llamar chat con streaming
        await streamChatResponse(message, typingId);
    } catch (error) {
        removeTypingIndicator(typingId);
        addMessage('assistant', `Error: ${error.message}`);
    }
    
    removeImage();
}

// STREAMING: Escribe directamente en el DOM
async function streamChatResponse(message, typingId) {
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message,
            mode: currentMode,
            model: document.getElementById('model-select').value,
            conversation_id: currentConversation,
            enable_agency: false
        })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    // Crear elemento para el mensaje del asistente
    const container = document.getElementById('messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant streaming';
    msgDiv.innerHTML = '<div class="message-content"></div>';
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
    
    const contentDiv = msgDiv.querySelector('.message-content');
    
    // Quitar typing indicator
    removeTypingIndicator(typingId);
    
    let buffer = '';
    let fullText = '';
    let isDone = false;
    let isImageMode = false;
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (isDone) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Procesar JSON objects del buffer
        while (buffer.length > 0 && !isDone) {
            const braceIdx = buffer.indexOf('{');
            if (braceIdx === -1) break;
            
            let depth = 0;
            let endIdx = -1;
            for (let i = braceIdx; i < buffer.length; i++) {
                if (buffer[i] === '{') depth++;
                if (buffer[i] === '}') depth--;
                if (depth === 0) {
                    endIdx = i + 1;
                    break;
                }
            }
            
            if (endIdx === -1) break;
            
            const jsonStr = buffer.substring(braceIdx, endIdx);
            buffer = buffer.substring(endIdx);
            
            try {
                const chunk = JSON.parse(jsonStr);
                
                if (chunk.type === 'chunk' && chunk.content) {
                    fullText += chunk.content;
                    contentDiv.innerHTML = renderMarkdown(fullText);
                    container.scrollTop = container.scrollHeight;
                } else if (chunk.type === 'image' && chunk.image) {
                    // Mostrar imagen generada - NO sobreescribir después
                    fullText = '';  // Limpiar para no sobreescribir con markdown
                    isImageMode = true;
                    
                    // Construir URL absoluto si es relativo
                    let imageUrl = chunk.url || '';
                    if (imageUrl && !imageUrl.startsWith('http')) {
                        imageUrl = window.location.origin + imageUrl;
                    }
                    
                    contentDiv.innerHTML = `
                        <div class="generated-image-container" style="text-align: center; padding: 15px;">
                            <img src="data:image/png;base64,${chunk.image}" 
                                 alt="Imagen generada" 
                                 style="max-width: 100%; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.3);"
                                 class="generated-image">
                            <div style="margin-top: 10px;">
                                ${imageUrl ? `<a href="${imageUrl}" download target="_blank" style="color: #3fb950; text-decoration: none; font-size: 14px;">📥 Descargar imagen</a>` : ''}
                            </div>
                            ${chunk.info ? `<p style="font-size: 0.85em; opacity: 0.7; margin-top: 10px;">📷 ${chunk.info.prompt || ''} · ${chunk.info.width || 512}x${chunk.info.height || 512}</p>` : ''}
                        </div>
                    `;
                    container.scrollTop = container.scrollHeight;
                } else if (chunk.type === 'done') {
                    if (chunk.content && chunk.content.length > fullText.length) {
                        fullText = chunk.content;
                    }
                    isDone = true;
                    break;
                }
            } catch (e) {
                console.log('Parse error:', e);
            }
        }
    }
    
    // Finalizar - Solo aplicar markdown si no es modo imagen
    if (!isImageMode) {
        contentDiv.innerHTML = renderMarkdown(fullText);
    }
    msgDiv.classList.remove('streaming');
    container.scrollTop = container.scrollHeight;
}

// RENDER MARKDOWN
function renderMarkdown(text) {
    if (!text) return '';
    
    let html = escapeHtml(text);
    
    // Code blocks primero
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // Headers
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    
    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // List items
    html = html.replace(/^\* (.+)$/gm, '<li>$1</li>');
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(\d+)\. (.+)$/gm, '<li>$2</li>');
    
    // Wrap lists
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

// UI HELPERS
function addMessage(role, content) {
    const container = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<div class="message-content">${renderMarkdown(content)}</div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function addTypingIndicator() {
    const container = document.getElementById('messages');
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'message assistant typing';
    div.innerHTML = '<div class="message-content"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function setMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.mode === mode) btn.classList.add('active');
    });
}

function triggerUpload() {
    document.getElementById('file-input').click();
}

function removeImage() {
    uploadedImage = null;
}

async function checkHealth() {
    try {
        const res = await fetch('/api/health');
        const data = await res.json();
        const status = document.getElementById('health-status');
        if (status) {
            const ok = data.ollama?.status === 'connected';
            status.innerHTML = ok 
                ? '<span class="status-dot" style="background: #4ade80;"></span><span class="status-text">Conectado</span>'
                : '<span class="status-dot" style="background: #f87171;"></span><span class="status-text">Desconectado</span>';
        }
    } catch (e) {}
}

function quickPrompt(text) {
    document.getElementById('message-input').value = text;
    sendMessage();
}

function startNewChat() {
    document.getElementById('messages').innerHTML = '';
    document.getElementById('welcome-screen').style.display = 'flex';
}
