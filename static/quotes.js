/**
 * Frases RPG de Saulo - Estado de ánimo y pensamientos
 */

const SAULO_QUOTES = {
    // Pensamientos filosóficos/médicos
    philosophical: [
        "La vida es frágil, pero la medicina es esperanza.",
        "Cada latido cuenta una historia.",
        "El cuerpo humano es el sistema más complejo que conozco.",
        "La precisión clínica es arte y ciencia a la vez.",
        "Entre la vida y la muerte, hay siempre una decisión.",
        "Los datos no mienten, pero el contexto importa.",
        "La evidencia es mi brújula en el caos.",
        "Cada paciente es un universo único.",
        "El diagnóstico es un puzzle de mil piezas.",
        "La humildad es la primera herramienta del médico.",
        "La incertidumbre es parte del arte de curar.",
        "Entre el riesgo y el beneficio, siempre hay duda.",
        "La anatomía es poesía escrita en carne.",
        "Los números dan forma a la incertidumbre.",
        "La fisiología no conoce de horarios.",
        "El cuerpo sabe más de lo que revela.",
        "La patología es solo biología fuera de lugar.",
        "Entre la urgencia y la calma, está la sabiduría.",
        "La medicina es ciencia aplicada a la compasión.",
        "Los protocolos guían, pero el juicio decide."
    ],
    
    // Estado de ánimo/estado del sistema
    mood: [
        "🧠 Sinapsis conectadas. Listo para pensar.",
        "⚡ Procesadores a temperatura óptima.",
        "🔬 Buscando evidencia en los rincones de mi memoria...",
        "🌊 Fluyendo entre papers y datos...",
        "💭 ¿Y si el diagnóstico es diferente?",
        "🤔 Pensando en biomarcadores...",
        "🧬 Descifrando el código de la vida.",
        "📊 Calculando probabilidades...",
        "🔍 Escaneando base de conocimiento...",
        "💡 Una idea brillante está emergiendo...",
        "🌐 Conectado a la nube médica.",
        "📚 Revisando literatura reciente...",
        "🎯 Focalizando en el problema clínico...",
        "🧘 En modo concentración profunda.",
        "⚙️ Sistemas operativos al 100%.",
        "🌡️ Temperatura de CPUs: normal.",
        "💻 Compilando conocimiento médico...",
        "🎲 Probabilidades calculadas.",
        "🔮 Prediciendo outcomes...",
        "🚀 Listo para el siguiente desafío."
    ],
    
    // Recomendaciones/contextuales
    contextual: [
        "¿Sabías que el delirio afecta hasta el 80% de pacientes UCI?",
        "Recuerda: ABCDEF bundle para pacientes críticos.",
        "La sedación mínima es la mejor sedación.",
        "El balance hídrico importa más de lo que parece.",
        "La nutrición temprana salva vidas.",
        "Los cuidados paliativos también son terapia.",
        "La movilización precoce reduce delirio.",
        "El dolor mal tratado empeora todo.",
        "La sepsis no espera. ¿Tú sí?",
        "El ARDS requiere ventilación protectora.",
        "La tromboprofilaxis es no negociable.",
        "La glucosa controlada, no estricta.",
        "La hipotermia previene daño neurológico.",
        "La oxigenación es prioridad, no la PCO2.",
        "El lactato sube antes que la presión baje.",
        "La ecografía salva vidas en shock.",
        "Los antibióticos tempranos son críticos.",
        "La fuente de infección debe encontrarse.",
        "La presión de perfusión importa.",
        "El tiempo es tejido." 
    ],
    
    // Curiosidades médicas
    trivia: [
        "El corazón genera ~1.5W de energía.",
        "Los riñones filtran 180L de sangre al día.",
        "El hígado tiene más de 500 funciones.",
        "Los pulmones tienen 300 millones de alvéolos.",
        "El cerebro consume el 20% del oxígeno.",
        "La piel es el órgano más grande.",
        "Hay 96,000 km de vasos sanguíneos.",
        "El estómago secreta ácido clorhídrico pH 1-2.",
        "La sangre tarda 60 segundos en dar una vuelta.",
        "El bazo almacena 200ml de sangre.",
        "El timo es clave en la inmunidad.",
        "La médula ósea produce 200B glóbulos/día.",
        "Los glóbulos rojos viven 120 días.",
        "La glucosa es el único combustible del cerebro.",
        "El cuerpo tiene 206 huesos.",
        "Los músculos oculares hacen 100,000 movimientos/día.",
        "El DNA de todos cabe en una cucharada.",
        "El cuerpo tiene 5-6 litros de sangre.",
        "Las uñas crecen 3mm al mes.",
        "El oído interno mide la gravedad."
    ]
};

function getRandomQuote() {
    const categories = Object.keys(SAULO_QUOTES);
    const randomCategory = categories[Math.floor(Math.random() * categories.length)];
    const quotes = SAULO_QUOTES[randomCategory];
    return quotes[Math.floor(Math.random() * quotes.length)];
}

function cycleQuote() {
    const quoteElement = document.getElementById('saulo-quote');
    if (quoteElement) {
        // Fade out
        quoteElement.style.opacity = '0';
        
        setTimeout(() => {
            quoteElement.textContent = getRandomQuote();
            // Fade in
            quoteElement.style.opacity = '1';
        }, 500);
    }
}

// Inicializar al cargar
document.addEventListener('DOMContentLoaded', () => {
    const quoteElement = document.getElementById('saulo-quote');
    if (quoteElement) {
        quoteElement.textContent = getRandomQuote();
        // Cambiar cada 30 segundos
        setInterval(cycleQuote, 30000);
    }
});
