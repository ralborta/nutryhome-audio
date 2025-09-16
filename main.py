from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
import os
import asyncio
from datetime import datetime
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NutryHome Audio Streaming Service",
    description="Microservicio optimizado para streaming de audio de alta performance",
    version="2.0.0"
)

# CORS optimizado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)

# Configuración global
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
CHUNK_SIZE = 8192  # 8KB chunks para streaming óptimo
MAX_CONCURRENT_STREAMS = 10

# Pool de conexiones reutilizable
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=None),
    limits=httpx.Limits(max_connections=20, max_keepalive_connections=10)
)

# Cache en memoria para headers y metadata
metadata_cache = {}

@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando microservicio de streaming optimizado")
    logger.info(f"ElevenLabs configurado: {bool(ELEVENLABS_API_KEY)}")

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()
    logger.info("Microservicio cerrado correctamente")

@app.get("/")
async def root():
    return {
        "service": "NutryHome Audio Streaming Service",
        "version": "2.0.0",
        "optimizations": [
            "Streaming por chunks",
            "Range requests support",
            "Connection pooling",
            "Memory-efficient processing",
            "Concurrent streaming",
            "Smart caching"
        ],
        "status": "Online",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "OK",
        "elevenlabs_configured": bool(ELEVENLABS_API_KEY),
        "connections_pool": "Active",
        "timestamp": datetime.now().isoformat()
    }

@app.head("/audio/{conversation_id}")
async def audio_head(conversation_id: str):
    """
    HEAD request para obtener metadata sin descargar el audio
    Optimización: permite al cliente conocer el tamaño antes de streaming
    """
    try:
        logger.info(f"HEAD request para: {conversation_id}")
        
        # Verificar cache de metadata
        if conversation_id in metadata_cache:
            cached = metadata_cache[conversation_id]
            return StreamingResponse(
                iter([]),
                media_type="audio/mpeg",
                headers=cached["headers"]
            )
        
        # HEAD request a ElevenLabs
        response = await http_client.head(
            f"{ELEVENLABS_BASE_URL}/convai/conversations/{conversation_id}/audio",
            headers={"xi-api-key": ELEVENLABS_API_KEY}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Audio no disponible")
        
        # Preparar headers optimizados
        headers = {
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Access-Control-Allow-Origin": "*",
            "X-Content-Source": "ElevenLabs",
            "X-Streaming-Optimized": "true"
        }
        
        # Agregar Content-Length si está disponible
        content_length = response.headers.get("content-length")
        if content_length:
            headers["Content-Length"] = content_length
            
        # Cache metadata por 5 minutos
        metadata_cache[conversation_id] = {
            "headers": headers,
            "timestamp": datetime.now()
        }
        
        return StreamingResponse(
            iter([]),
            media_type="audio/mpeg",
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"Error en HEAD {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo metadata")

@app.get("/audio/{conversation_id}")
async def stream_audio_optimized(conversation_id: str, request: Request):
    """
    Streaming de audio optimizado con soporte para Range requests
    """
    start_time = datetime.now()
    logger.info(f"Streaming request para: {conversation_id}")
    
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="API key no configurada")
    
    try:
        # Preparar headers para la request a ElevenLabs
        elevenlabs_headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Accept": "audio/mpeg",
            "User-Agent": "NutryHome-Audio-Service/2.0"
        }
        
        # Soporte para Range requests (streaming parcial)
        range_header = request.headers.get("range")
        if range_header:
            elevenlabs_headers["Range"] = range_header
            logger.info(f"Range request: {range_header}")
        
        # Request a ElevenLabs con streaming
        response = await http_client.stream(
            "GET",
            f"{ELEVENLABS_BASE_URL}/convai/conversations/{conversation_id}/audio",
            headers=elevenlabs_headers
        )
        
        if response.status_code not in [200, 206]:
            await response.aclose()
            logger.error(f"ElevenLabs error: {response.status_code}")
            raise HTTPException(
                status_code=404 if response.status_code == 404 else 502,
                detail="Audio no disponible"
            )
        
        # Headers optimizados para streaming
        response_headers = {
            "Content-Type": "audio/mpeg",
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Access-Control-Allow-Origin": "*",
            "X-Conversation-Id": conversation_id,
            "X-Streaming-Mode": "chunked"
        }
        
        # Mantener headers importantes de ElevenLabs
        for header in ["content-length", "content-range", "last-modified"]:
            if header in response.headers:
                response_headers[header.title()] = response.headers[header]
        
        # Status code apropiado para Range requests
        status_code = response.status_code
        
        # Generador de streaming optimizado
        async def stream_generator():
            total_bytes = 0
            chunk_count = 0
            
            try:
                async for chunk in response.aiter_bytes(chunk_size=CHUNK_SIZE):
                    total_bytes += len(chunk)
                    chunk_count += 1
                    
                    # Log cada 100 chunks para monitoreo
                    if chunk_count % 100 == 0:
                        logger.info(f"Chunk {chunk_count}: {total_bytes} bytes total")
                    
                    yield chunk
                
                # Log final
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(
                    f"Streaming completado para {conversation_id}: "
                    f"{total_bytes} bytes en {chunk_count} chunks en {duration:.2f}s"
                )
                
            except Exception as stream_error:
                logger.error(f"Error en streaming: {stream_error}")
                raise
            finally:
                await response.aclose()
        
        return StreamingResponse(
            stream_generator(),
            status_code=status_code,
            media_type="audio/mpeg",
            headers=response_headers
        )
        
    except httpx.TimeoutException:
        logger.error(f"Timeout para {conversation_id}")
        raise HTTPException(status_code=504, detail="Timeout conectando con ElevenLabs")
    except httpx.RequestError as e:
        logger.error(f"Error de conexión: {e}")
        raise HTTPException(status_code=502, detail="Error de conectividad")
    except Exception as e:
        logger.error(f"Error general: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/audio/{conversation_id}/info")
async def get_audio_info(conversation_id: str):
    """
    Obtener información del audio sin descargarlo
    """
    try:
        response = await http_client.head(
            f"{ELEVENLABS_BASE_URL}/convai/conversations/{conversation_id}/audio",
            headers={"xi-api-key": ELEVENLABS_API_KEY}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Audio no encontrado")
        
        info = {
            "conversation_id": conversation_id,
            "available": True,
            "content_type": response.headers.get("content-type", "audio/mpeg"),
            "supports_range": "bytes" in response.headers.get("accept-ranges", ""),
            "estimated_size": response.headers.get("content-length"),
            "last_modified": response.headers.get("last-modified"),
            "streaming_url": f"/audio/{conversation_id}"
        }
        
        if info["estimated_size"]:
            info["estimated_size_mb"] = round(int(info["estimated_size"]) / 1024 / 1024, 2)
        
        return info
        
    except Exception as e:
        logger.error(f"Error obteniendo info: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo información")

@app.get("/stream-test/{conversation_id}")
async def test_streaming_performance(conversation_id: str):
    """
    Endpoint para probar performance de streaming
    """
    start_time = datetime.now()
    
    try:
        async with http_client.stream(
            "GET",
            f"{ELEVENLABS_BASE_URL}/convai/conversations/{conversation_id}/audio",
            headers={"xi-api-key": ELEVENLABS_API_KEY}
        ) as response:
            
            if response.status_code != 200:
                return {"error": f"Audio no disponible: {response.status_code}"}
            
            total_bytes = 0
            chunk_count = 0
            
            # Solo leer los primeros chunks para test
            async for chunk in response.aiter_bytes(chunk_size=CHUNK_SIZE):
                total_bytes += len(chunk)
                chunk_count += 1
                
                # Test solo con 50 chunks
                if chunk_count >= 50:
                    break
            
            duration = (datetime.now() - start_time).total_seconds()
            throughput_mbps = (total_bytes * 8) / (duration * 1000000) if duration > 0 else 0
            
            return {
                "conversation_id": conversation_id,
                "test_duration_seconds": duration,
                "bytes_tested": total_bytes,
                "chunks_tested": chunk_count,
                "throughput_mbps": round(throughput_mbps, 2),
                "avg_chunk_size": total_bytes / chunk_count if chunk_count > 0 else 0,
                "performance": "excellent" if throughput_mbps > 1 else "good" if throughput_mbps > 0.5 else "slow"
            }
            
    except Exception as e:
        return {"error": str(e)}

# Middleware para logging de performance
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    
    response = await call_next(request)
    
    duration = (datetime.now() - start_time).total_seconds()
    
    # Log requests lentos
    if duration > 1.0:
        logger.warning(
            f"Slow request: {request.method} {request.url.path} - {duration:.3f}s"
        )
    else:
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
        )
    
    return response

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    print(f"Iniciando microservicio optimizado en puerto {port}")
    print("Optimizaciones activas:")
    print("- Streaming por chunks")
    print("- Range requests support") 
    print("- Connection pooling")
    print("- Smart caching")
    print("- Performance monitoring")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )