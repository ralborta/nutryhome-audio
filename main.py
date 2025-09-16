from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
import os
from datetime import datetime
import logging

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App
app = FastAPI(
    title="NutryHome Audio Service",
    description="Microservicio para streaming de audio desde ElevenLabs",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nutry-home-btvkllfm-nu41-vercel-app.vercel.app",
        "https://*.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# Variables
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

@app.get("/")
async def root():
    """Info del servicio"""
    return {
        "service": "NutryHome Audio Service",
        "status": "Online",
        "version": "1.0.0",
        "purpose": "Stream audio from ElevenLabs",
        "endpoints": {
            "/": "Service info",
            "/health": "Health check", 
            "/audio/{conversation_id}": "Stream audio"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "OK",
        "elevenlabs_configured": bool(ELEVENLABS_API_KEY),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/audio/{conversation_id}")
async def get_audio(conversation_id: str):
    """
    Stream audio desde ElevenLabs
    """
    start_time = datetime.now()
    
    logger.info(f"Audio request para: {conversation_id}")
    
    # Validaciones básicas
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="API key no configurada")
    
    if not conversation_id or len(conversation_id) < 5:
        raise HTTPException(status_code=400, detail="ID de conversación inválido")
    
    try:
        # Request a ElevenLabs
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{ELEVENLABS_BASE_URL}/convai/conversations/{conversation_id}/audio",
                headers={
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Accept": "audio/mpeg"
                }
            )
            
            logger.info(f"ElevenLabs response: {response.status_code}")
            
            # Manejo de errores
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Audio no disponible para {conversation_id}"
                )
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Error ElevenLabs: {response.status_code}"
                )
            
            # Headers para audio
            headers = {
                "Content-Type": "audio/mpeg",
                "Accept-Ranges": "bytes", 
                "Cache-Control": "public, max-age=1800",
                "Access-Control-Allow-Origin": "*"
            }
            
            # Content-Length si disponible
            content_length = response.headers.get("content-length")
            if content_length:
                headers["Content-Length"] = content_length
                logger.info(f"Audio size: {content_length} bytes")
            
            # Streaming generator
            async def stream_audio():
                total_bytes = 0
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    total_bytes += len(chunk)
                    yield chunk
                
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"Stream completed: {total_bytes} bytes in {duration:.2f}s")
            
            return StreamingResponse(
                stream_audio(),
                media_type="audio/mpeg",
                headers=headers
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout conectando con ElevenLabs")
    except httpx.RequestError as e:
        logger.error(f"Connection error: {e}")
        raise HTTPException(status_code=502, detail=f"Error de conectividad: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Middleware para logging
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = datetime.now()
    
    response = await call_next(request)
    
    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s")
    
    return response

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    print(f"Iniciando Audio Service en puerto {port}")
    print(f"ElevenLabs configurado: {bool(ELEVENLABS_API_KEY)}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
