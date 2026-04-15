"""
FIXES PARA SAULO v4 - Backend Corrections
1. Contexto en conversaciones
2. Generación de imágenes funcional
3. Búsquedas en internet
"""

import httpx
from typing import List, Dict, AsyncGenerator
import json

async def search_web(query: str, max_results: int = 5) -> str:
    """Buscar en internet usando DuckDuckGo (sin API key)."""
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            
            if not results:
                return "No se encontraron resultados en la web."
            
            summary = f"## Resultados de búsqueda para: {query}\n\n"
            for i, r in enumerate(results, 1):
                summary += f"{i}. [{r['title']}]({r['href']})\n"
                summary += f"   {r['body'][:200]}...\n\n"
            
            return summary
    except Exception as e:
        return f"Error en búsqueda web: {str(e)}"


async def chat_with_context(
    message: str,
    history: List[Dict],
    mode: str,
    ollama_client,
    cloud_client
) -> AsyncGenerator[str, None]:
    """Chat con contexto de conversación."""
    
    # Construir messages con historial
    messages = []
    
    # System prompt según modo
    system_prompts = {
        "general": "Eres Saulo, un asistente AI útil y conversacional. Mantén el contexto de la conversación.",
        "medical": "Eres Saulo, asistente médico. Usa evidencia científica. Incluye disclaimer: 'No es consejo médico profesional'.",
        "coding": "Eres Saulo, experto en código. Proporciona código funcional y explicaciones claras.",
        "image": "Eres Saulo, asistente para generación de imágenes. Ayuda a crear prompts optimizados.",
        "vision": "Eres Saulo, experto en análisis de imágenes. Describe detalladamente lo que ves."
    }
    
    messages.append({"role": "system", "content": system_prompts.get(mode, system_prompts["general"])})
    
    # Agregar historial (últimos 10 mensajes)
    if history:
        for msg in history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Agregar mensaje actual
    messages.append({"role": "user", "content": message})
    
    # Usar cloud si está disponible, sino local
    if cloud_client and cloud_client.is_configured():
        async for chunk in cloud_client.chat(messages, stream=True):
            yield chunk
    else:
        # Fallback a Ollama
        full_prompt = "\n".join([f"{'Usuario' if m['role']=='user' else 'Asistente'}: {m['content']}" for m in messages[1:]])
        async for chunk in ollama_client.generate(full_prompt):
            yield chunk


async def generate_image_sd(prompt: str, sd_url: str = "http://127.0.0.1:7860") -> Dict:
    """Generar imagen con Stable Diffusion - Función corregida."""
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "prompt": prompt,
                "negative_prompt": "low quality, blurry, distorted",
                "width": 512,
                "height": 512,
                "steps": 25,
                "cfg_scale": 7.0,
                "sampler_name": "DPM++ 2M Karras",
                "batch_size": 1,
                "n_iter": 1
            }
            
            response = await client.post(
                f"{sd_url}/sdapi/v1/txt2img",
                json=payload
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"SD error: {response.status_code}"}
            
            data = response.json()
            
            if "images" in data and len(data["images"]) > 0:
                return {
                    "success": True,
                    "image": data["images"][0],
                    "info": data.get("info", {})
                }
            else:
                return {"success": False, "error": "No image generated"}
                
    except Exception as e:
        return {"success": False, "error": str(e)}
