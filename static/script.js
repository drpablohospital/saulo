class SauloChat {
    constructor() {
        this.apiUrl = window.location.origin; // Usar la misma URL actual
        this.userId = 'pablo_main';
        this.messagesContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.checkConnection();
        this.loadSauloState();
        
        // Configurar URL automáticamente
        document.getElementById('apiUrl').value = this.apiUrl;
        document.getElementById('welcomeTime').textContent = new Date().toLocaleTimeString();
    }
    
    setupEventListeners() {
        // Enviar mensaje con Enter
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Enviar mensaje con botón
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Contador de caracteres
        this.messageInput.addEventListener('input', () => {
            const count = this.messageInput.value.length;
            document.getElementById('charCount').textContent = `${count}/1000`;
        });
        
        // Botones de estado
        document.querySelectorAll('.state-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const state = e.target.dataset.state;
                this.changeSauloState(state);
            });
        });
        
        // Reset Saulo
        document.getElementById('resetBtn').addEventListener('click', () => {
            this.sendCommand('/reset');
        });
        
        // Actualizar estado
        document.getElementById('refreshState').addEventListener('click', () => {
            this.loadSauloState();
        });
        
        // Configuración dinámica
        document.getElementById('apiUrl').addEventListener('change', (e) => {
            this.apiUrl = e.target.value;
            this.checkConnection();
        });
        
        document.getElementById('userId').addEventListener('change', (e) => {
            this.userId = e.target.value;
            this.loadSauloState();
        });
    }
    
    async checkConnection() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            const data = await response.json();
            
            document.getElementById('statusDot').className = 'status-dot connected';
            document.getElementById('statusText').textContent = 'Conectado';
            
            console.log('✅ Conexión establecida');
            return true;
        } catch (error) {
            document.getElementById('statusDot').className = 'status-dot';
            document.getElementById('statusText').textContent = 'Desconectado';
            
            console.error('❌ Error de conexión:', error);
            this.showMessage('system', 'No se pudo conectar con el servidor de Saulo.');
            return false;
        }
    }
    
    async loadSauloState() {
        try {
            const response = await fetch(`${this.apiUrl}/estado/${this.userId}`);
            const data = await response.json();
            this.updateUIState(data);
        } catch (error) {
            console.error('Error cargando estado:', error);
        }
    }
    
    updateUIState(data) {
        const { estado, insights_ontologicos } = data;
        
        // Actualizar estado
        const currentStateEl = document.getElementById('currentState');
        currentStateEl.textContent = estado.current_state;
        currentStateEl.className = estado.current_state;
        document.getElementById('stateCounter').textContent = estado.state_counter;
        document.getElementById('ontologicalExchanges').textContent = estado.total_ontological_exchanges || 0;
        document.getElementById('lastTopic').textContent = estado.last_deep_topic || 'Ninguno';
        
        // Actualizar botones de estado activo
        document.querySelectorAll('.state-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.state === estado.current_state);
        });
        
        // Actualizar insights
        const insightsContainer = document.getElementById('insights');
        insightsContainer.innerHTML = '';
        
        if (insights_ontologicos && insights_ontologicos.length > 0) {
            insights_ontologicos.forEach(insight => {
                const insightEl = document.createElement('div');
                insightEl.className = 'insight-item';
                insightEl.innerHTML = `
                    <div style="color: #a78bfa; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.25rem;">
                        ${insight.category || 'Ontológico'}
                    </div>
                    <div style="font-size: 0.85rem; color: #cbd5e1;">
                        ${insight.interpretation}
                    </div>
                `;
                insightsContainer.appendChild(insightEl);
            });
        }
    }
    
    async sendMessage() {
        const text = this.messageInput.value.trim();
        if (!text) return;
        
        // Verificar si es un comando
        if (text.startsWith('/')) {
            this.sendCommand(text);
            this.messageInput.value = '';
            return;
        }
        
        // Agregar mensaje del usuario
        this.addMessage('user', text);
        
        // Limpiar y deshabilitar
        this.messageInput.value = '';
        this.sendButton.disabled = true;
        
        try {
            const response = await fetch(`${this.apiUrl}/conversar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    text: text
                })
            });
            
            const data = await response.json();
            
            // Agregar respuesta de Saulo
            const messageClass = data.bloqueado ? 'saulo blocked' : 
                               data.es_ontologico ? 'saulo ontological' : 'saulo';
            
            this.addMessage(messageClass, data.text, 'Saulo');
            this.updateUIFromResponse(data);
            
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('system', 'Error de conexión con Saulo.');
        } finally {
            this.sendButton.disabled = false;
            this.messageInput.focus();
        }
    }
    
    async sendCommand(command) {
        this.addMessage('user', command);
        
        try {
            const response = await fetch(`${this.apiUrl}/conversar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    text: command.includes(' ') ? command.split(' ')[1] : '',
                    comando_especial: command.split(' ')[0]
                })
            });
            
            const data = await response.json();
            this.addMessage('system', data.text);
            this.loadSauloState();
            
        } catch (error) {
            this.addMessage('system', `Error: ${error.message}`);
        }
    }
    
    async changeSauloState(newState) {
        try {
            const response = await fetch(`${this.apiUrl}/conversar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    comando_especial: '/estado',
                    text: newState
                })
            });
            
            const data = await response.json();
            this.addMessage('system', data.text);
            this.loadSauloState();
            
        } catch (error) {
            console.error('Error cambiando estado:', error);
        }
    }
    
    addMessage(type, text, sender = null) {
        const messageEl = document.createElement('div');
        const timestamp = new Date().toLocaleTimeString();
        const senderName = sender || (type === 'user' ? 'Tú' : type.includes('saulo') ? 'Saulo' : 'Sistema');
        
        messageEl.className = `message ${type}`;
        messageEl.innerHTML = `
            <div class="avatar">
                <i class="fas ${type === 'user' ? 'fa-user' : type.includes('saulo') ? 'fa-robot' : 'fa-cog'}"></i>
            </div>
            <div class="content">
                <div class="sender">${senderName}</div>
                <div class="text">${text.replace(/\n/g, '<br>')}</div>
                <div class="timestamp">${timestamp}</div>
            </div>
        `;
        
        this.messagesContainer.appendChild(messageEl);
        messageEl.scrollIntoView({ behavior: 'smooth' });
    }
    
    showMessage(type, text) {
        this.addMessage(type, text);
    }
    
    updateUIFromResponse(response) {
        const currentStateEl = document.getElementById('currentState');
        currentStateEl.textContent = response.estado_actual;
        currentStateEl.className = response.estado_actual;
        document.getElementById('stateCounter').textContent = response.contador_estado;
        
        // Actualizar botón de estado activo
        document.querySelectorAll('.state-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.state === response.estado_actual);
        });
        
        // Recargar estado completo
        setTimeout(() => this.loadSauloState(), 500);
    }
}

// Inicializar cuando se cargue la página
document.addEventListener('DOMContentLoaded', () => {
    window.sauloChat = new SauloChat();
});
