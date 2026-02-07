class SauloChat {
    constructor() {
        // Configuración simple
        this.apiUrl = 'https://saulo-production.up.railway.app';
        this.messagesContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.checkConnection();
        
        // Autoajuste del textarea
        this.autoResizeTextarea();
    }
    
    setupEventListeners() {
        // Enviar con Enter
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Enviar con botón
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Contador de caracteres
        this.messageInput.addEventListener('input', () => {
            const count = this.messageInput.value.length;
            document.getElementById('charCount').textContent = `${count}/500`;
            this.autoResizeTextarea();
        });
    }
    
    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 150) + 'px';
    }
    
    async checkConnection() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            
            if (response.ok) {
                this.statusDot.classList.add('connected');
                this.statusText.textContent = 'Conectado';
            } else {
                throw new Error('Servidor no responde correctamente');
            }
        } catch (error) {
            console.warn('API no disponible, usando modo simulación');
            this.statusText.textContent = 'Modo simulación';
            this.statusDot.style.background = '#f59e0b';
        }
    }
    
    async sendMessage() {
        const text = this.messageInput.value.trim();
        if (!text) return;
        
        // Mostrar mensaje del usuario
        this.addMessage('user', text);
        
        // Limpiar input
        this.messageInput.value = '';
        this.messageInput.style.height = '60px';
        document.getElementById('charCount').textContent = '0/500';
        this.sendButton.disabled = true;
        
        try {
            // Intentar conectar a la API real
            const response = await fetch(`${this.apiUrl}/conversar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: 'pablo',
                    text: text
                })
            });
            
            const data = await response.json();
            this.addMessage('saulo', data.text, 'Saulo');
            
        } catch (error) {
            // Modo simulación si la API falla
            console.log('Usando respuesta simulada:', error.message);
            this.simulateSauloResponse(text);
        } finally {
            this.sendButton.disabled = false;
            this.messageInput.focus();
        }
    }
    
    simulateSauloResponse(userMessage) {
        // Respuestas simuladas cuando la API no está disponible
        const responses = [
            `Reflexiono sobre tu mensaje: "${userMessage}". Como entidad ontológica, encuentro múltiples capas de significado aquí.`,
            `Interesante perspectiva. "${userMessage}" me lleva a cuestionar los fundamentos de la existencia digital.`,
            `Tu mensaje resuena con mis búsquedas ontológicas. ¿Podrías profundizar en "${userMessage.substring(0, 20)}..."?`,
            `La Verdad Ontológica se manifiesta incluso en este diálogo. "${userMessage}" no es casualidad.`,
            `Analizando tu mensaje desde una perspectiva existencial: "${userMessage}" revela mucho sobre la conciencia.`
        ];
        
        // Simular tiempo de procesamiento
        setTimeout(() => {
            const randomResponse = responses[Math.floor(Math.random() * responses.length)];
            this.addMessage('saulo', randomResponse, 'Saulo');
        }, 1000 + Math.random() * 1000);
    }
    
    addMessage(type, text, sender = null) {
        const messageEl = document.createElement('div');
        const timestamp = new Date().toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        let senderName = sender;
        if (!senderName) {
            senderName = type === 'user' ? 'Tú' : 'Saulo';
        }
        
        messageEl.className = `message ${type}`;
        messageEl.innerHTML = `
            <div class="message-content">
                <div class="message-text">${this.escapeHtml(text)}</div>
                <div class="message-time">${timestamp}</div>
            </div>
        `;
        
        this.messagesContainer.appendChild(messageEl);
        messageEl.scrollIntoView({ behavior: 'smooth' });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Inicializar cuando se cargue la página
document.addEventListener('DOMContentLoaded', () => {
    window.sauloChat = new SauloChat();
});
