"""
Vision Service - Análisis de imágenes médicas y OCR
Integra CheXNet, modelos de visión local y servicios de OCR
"""

import os
import base64
import io
from pathlib import Path
from typing import Dict, Any, Optional
import httpx

class VisionService:
    """Servicio de visión e interpretación médica de imágenes."""
    
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
        self.http = httpx.AsyncClient(timeout=60.0)
        
        # Modelos disponibles
        self.vision_models = ["llava", "llama3.2-vision", "vision-router"]
        self.medical_models = ["chexnet", "medical-vlm"]
    
    async def analyze_image(self, image_data: bytes, prompt: str = "", mode: str = "auto") -> Dict[str, Any]:
        """
        Analiza una imagen según el modo seleccionado.
        
        Modes:
        - "medical": Análisis médico especializado (CheXNet si disponible)
        - "ocr": Extracción de texto (OCR)
        - "general": Descripción general
        - "auto": Detecta automáticamente
        """
        
        # Guardar imagen temporalmente
        temp_path = "/tmp/vision_temp.png"
        with open(temp_path, "wb") as f:
            f.write(image_data)
        
        try:
            if mode == "medical" or (mode == "auto" and self._is_medical_prompt(prompt)):
                return await self._analyze_medical(image_data, prompt)
            elif mode == "ocr":
                return await self._ocr_extraction(image_data)
            else:
                return await self._analyze_general(image_data, prompt)
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    async def _analyze_medical(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        """Análisis médico especializado."""
        
        # Intentar con modelo médico local primero
        try:
            result = await self._chexnet_analysis(image_data)
            if result.get("success"):
                return result
        except Exception as e:
            print(f"CheXNet failed: {e}")
        
        # Fallback a vision general con prompt médico
        medical_prompt = prompt or "Analyze this medical image. Describe any abnormalities, findings, or relevant clinical features."
        return await self._analyze_general(image_data, medical_prompt)
    
    async def _chexnet_analysis(self, image_data: bytes) -> Dict[str, Any]:
        """Análisis con CheXNet si está disponible."""
        # TODO: Implementar integración con CheXNet local
        return {"success": False, "error": "CheXNet not configured"}
    
    async def _ocr_extraction(self, image_data: bytes) -> Dict[str, Any]:
        """Extracción de texto con OCR."""
        # Codificar imagen para enviar
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Usar modelo de visión para OCR
        payload = {
            "model": "llava",
            "messages": [
                {
                    "role": "user",
                    "content": "Extract and transcribe all text visible in this image. Return only the extracted text."
                }
            ],
            "images": [base64_image],
            "stream": False
        }
        
        try:
            response = await self.http.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                timeout=30.0
            )
            data = response.json()
            
            return {
                "success": True,
                "text": data.get("message", {}).get("content", ""),
                "source": "ocr_llava"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _analyze_general(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        """Análisis general con modelo de visión."""
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        payload = {
            "model": "llava",
            "messages": [
                {
                    "role": "user",
                    "content": prompt or "Describe this image in detail."
                }
            ],
            "images": [base64_image],
            "stream": False
        }
        
        try:
            response = await self.http.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                timeout=30.0
            )
            data = response.json()
            
            return {
                "success": True,
                "analysis": data.get("message", {}).get("content", ""),
                "source": "vision_llava"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _is_medical_prompt(self, prompt: str) -> bool:
        """Detecta si es una consulta médica."""
        medical_terms = [
            "rayos x", "radiografía", "x-ray", "xray",
            "tomografía", "ct scan", "mri", "resonancia",
            "ecografía", "ultrasound", "médico", "medical",
            "patología", "pathology", "diagnóstico", "diagnosis"
        ]
        prompt_lower = prompt.lower()
        return any(term in prompt_lower for term in medical_terms)

# Instancia global
vision_service = VisionService()
