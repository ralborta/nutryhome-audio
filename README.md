# NutryHome Audio Service

Microservicio para streaming de audio desde ElevenLabs API.

## 🚀 Características

- **Streaming de audio** desde ElevenLabs por conversation_id
- **API REST** con FastAPI
- **CORS habilitado** para integración web
- **Logging completo** de requests y respuestas
- **Manejo de errores** robusto
- **Deploy automático** en Railway

## 📋 Requisitos

- Python 3.8+
- API Key de ElevenLabs
- Cuenta en Railway (para deploy)

## 🛠️ Setup Local

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/nutryhome-audio.git
cd nutryhome-audio
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
export ELEVENLABS_API_KEY="tu_api_key_aqui"
```

5. **Ejecutar el servidor**
```bash
python main.py
```

El servidor estará disponible en `http://localhost:8000`

## 🌐 Endpoints

### GET /
Información del servicio
```json
{
  "service": "NutryHome Audio Service",
  "status": "Online",
  "version": "1.0.0",
  "purpose": "Stream audio from ElevenLabs",
  "endpoints": {...},
  "timestamp": "2024-01-01T00:00:00"
}
```

### GET /health
Health check del servicio
```json
{
  "status": "OK",
  "elevenlabs_configured": true,
  "timestamp": "2024-01-01T00:00:00"
}
```

### GET /audio/{conversation_id}
Stream de audio desde ElevenLabs

**Parámetros:**
- `conversation_id` (string): ID de la conversación en ElevenLabs

**Respuesta:**
- Content-Type: `audio/mpeg`
- Streaming response

**Ejemplo de uso:**
```javascript
const audioUrl = 'https://tu-service.railway.app/audio/conv_12345';
const audio = new Audio(audioUrl);
audio.play();
```

## 🚀 Deploy en Railway

1. **Conectar con GitHub**
   - Crear repositorio en GitHub
   - Subir el código
   - Conectar con Railway

2. **Configurar variables de entorno**
   - `ELEVENLABS_API_KEY`: Tu API key de ElevenLabs

3. **Deploy automático**
   - Railway detectará automáticamente que es un proyecto Python
   - Instalará dependencias desde `requirements.txt`
   - Ejecutará `python main.py`

## 🔧 Configuración

### Variables de entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `ELEVENLABS_API_KEY` | API key de ElevenLabs | ✅ |
| `PORT` | Puerto del servidor (default: 8000) | ❌ |

### Logging

El servicio incluye logging completo:
- Requests HTTP con duración
- Respuestas de ElevenLabs
- Errores y excepciones
- Métricas de streaming

## 📊 Monitoreo

- **Health check**: `/health` para verificar estado
- **Logs**: Disponibles en Railway dashboard
- **Métricas**: Tiempo de respuesta y tamaño de audio

## 🛡️ Seguridad

- CORS configurado para permitir requests desde cualquier origen
- Validación de conversation_id
- Timeout de 30s para requests a ElevenLabs
- Manejo seguro de errores sin exponer información sensible

## 📝 Notas

- El servicio actúa como proxy para ElevenLabs
- No almacena audio localmente
- Optimizado para streaming con chunks de 8KB
- Cache headers configurados para 30 minutos

## 🤝 Contribuir

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.
