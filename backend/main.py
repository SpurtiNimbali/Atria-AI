"""
Atria AI API gateway — FastAPI + WebSockets.
Agent logic lives in ./agent (ConversationalDoctor + tools).
"""
import json
import logging
import os
import sys
import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict

import certifi
if not hasattr(certifi, "where"):
    import ssl
    import os as _os

    def certifi_where():
        if hasattr(certifi, "__file__") and certifi.__file__:
            cert_path = _os.path.join(_os.path.dirname(certifi.__file__), "cacert.pem")
            if _os.path.exists(cert_path):
                return cert_path
        default_paths = ssl.get_default_verify_paths()
        return default_paths.cafile or default_paths.capath or "/etc/ssl/cert.pem"

    certifi.where = certifi_where

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

_backend_dir = Path(__file__).resolve().parent
_repo_root = _backend_dir.parent
for _env_path, _override in ((_repo_root / ".env", False), (_backend_dir / ".env", True)):
    if _env_path.is_file():
        try:
            load_dotenv(_env_path, override=_override)
        except PermissionError:
            logger.warning("Could not load .env from %s — using process env only", _env_path)

if not os.getenv("ELASTIC_URL"):
    os.environ.setdefault("ELASTIC_URL", "http://localhost:9200")

AGENT_DIR = os.path.join(os.path.dirname(__file__), "agent")
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Default on: ensure Sophia demo (synthetic-001) exists after ES comes up (Docker / fresh volume).
    if os.getenv("AUTO_INGEST_SYNTHETIC_DEMO", "1").strip() != "0":
        try:
            from elastic_client import get_elastic_client
            from local_ingest import ingest_patient_local as _ingest_patient_local
            from ingest_synthetic import ingest_synthetic_patient

            patient_id = (os.getenv("SYNTHETIC_DEMO_PATIENT_ID", "synthetic-001").strip() or "synthetic-001")
            index_name = "ehr_chunks"
            es = get_elastic_client()
            loop = asyncio.get_running_loop()

            force = os.getenv("FORCE_REINGEST_SYNTHETIC_DEMO", "").strip().lower() in (
                "1",
                "true",
                "yes",
            )

            def _count_docs() -> int:
                try:
                    count_result = es.count(
                        index=index_name,
                        query={"term": {"patient_id": patient_id}},
                    )
                except TypeError:
                    count_result = es.count(
                        index=index_name,
                        body={"query": {"term": {"patient_id": patient_id}}},
                    )
                return int(count_result.get("count", 0))

            needs_ingest = force or (not es.indices.exists(index=index_name)) or (_count_docs() == 0)

            if not needs_ingest:
                logger.info(
                    "AUTO_INGEST_SYNTHETIC_DEMO: %s already has data for %s; skip (set FORCE_REINGEST_SYNTHETIC_DEMO=1 to redo)",
                    index_name,
                    patient_id,
                )
            else:
                logger.info(
                    "AUTO_INGEST_SYNTHETIC_DEMO: indexing %s into %s (force=%s)...",
                    patient_id,
                    index_name,
                    force,
                )

                def _primary():
                    return _ingest_patient_local(patient_id)

                try:
                    out = await loop.run_in_executor(None, _primary)
                    if not isinstance(out, dict) or out.get("status") != "success":
                        raise RuntimeError(out or "ingest_patient_local did not succeed")
                except Exception as e:
                    logger.warning(
                        "AUTO_INGEST_SYNTHETIC_DEMO: primary ingest failed (%s); trying ingest_synthetic fallback",
                        e,
                    )
                    synthetic_json = _backend_dir / "agent" / "synthetic_patient.json"

                    def _fallback():
                        return ingest_synthetic_patient(str(synthetic_json))

                    out2 = await loop.run_in_executor(None, _fallback)
                    if not isinstance(out2, dict) or out2.get("status") != "success":
                        raise RuntimeError(out2 or "ingest_synthetic fallback did not succeed")

                try:
                    es.indices.refresh(index=index_name)
                except Exception:
                    logger.debug("index refresh skipped", exc_info=True)

                n = _count_docs()
                if n == 0:
                    logger.error(
                        "AUTO_INGEST_SYNTHETIC_DEMO: verification failed — 0 chunks for %s. "
                        "Check Elasticsearch connectivity, ELASTIC_URL, JINA_API_KEY, or set DEMO_PLACEHOLDER_EMBEDDINGS=1 for demo-only zeros.",
                        patient_id,
                    )
                else:
                    logger.info("AUTO_INGEST_SYNTHETIC_DEMO: verified %s chunks for %s", n, patient_id)
        except Exception:
            logger.exception(
                "AUTO_INGEST_SYNTHETIC_DEMO: startup ingest failed — set keys in .env or see logs above"
            )
    yield


app = FastAPI(title="Atria AI API", lifespan=lifespan)

allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
]
if os.getenv("ALLOWED_ORIGINS"):
    allowed_origins.extend([o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()])

# Vercel production + preview URLs (*.vercel.app) without listing each branch (set ALLOW_VERCEL_CORS_REGEX=0 to disable)
_cors: dict = {
    "allow_origins": allowed_origins,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if os.getenv("ALLOW_VERCEL_CORS_REGEX", "1").strip() != "0":
    _cors["allow_origin_regex"] = r"https://.*\.vercel\.app"

app.add_middleware(CORSMiddleware, **_cors)


def _apply_certifi_fix_for_es():
    """Elasticsearch client may import certifi; keep Python 3.14-friendly fallback."""
    if not hasattr(certifi, "where"):
        import ssl

        def certifi_where():
            if hasattr(certifi, "__file__") and certifi.__file__:
                cert_path = os.path.join(os.path.dirname(certifi.__file__), "cacert.pem")
                if os.path.exists(cert_path):
                    return cert_path
            default_paths = ssl.get_default_verify_paths()
            return default_paths.cafile or default_paths.capath or "/etc/ssl/cert.pem"

        certifi.where = certifi_where


from conversational_doctor import ConversationalDoctor  # noqa: E402
from local_ingest import ingest_patient_local  # noqa: E402

conversational_doctor = ConversationalDoctor()
logger.info("ConversationalDoctor ready")


class TTSRequest(BaseModel):
    text: str


@app.get("/")
async def root():
    return {
        "service": "Atria AI API",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    try:
        import httpx
        from fastapi.responses import StreamingResponse
        import io

        api_key = os.getenv("ELEVENLABS_API_KEY")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
        model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
        if not api_key:
            raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not configured")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        payload = {
            "text": request.text,
            "model_id": model_id,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return StreamingResponse(
                io.BytesIO(response.content),
                media_type="audio/mpeg",
                headers={"Content-Disposition": "inline", "Cache-Control": "no-cache"},
            )
    except httpx.HTTPStatusError as e:
        logger.error("ElevenLabs API error: %s", e)
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("TTS error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/patients/{patient_id}/refresh")
async def refresh_patient(patient_id: str):
    try:
        result = ingest_patient_local(patient_id)
        return {"status": "success", "patient_id": patient_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/patients/{patient_id}/summary")
async def get_patient_summary_ep(patient_id: str):
    return {
        "patient_id": patient_id,
        "status": "available",
        "message": "Use /patients/{id}/refresh to re-ingest; dashboard at /patients/{id}/dashboard",
    }


@app.get("/patients/{patient_id}/dashboard")
async def get_patient_dashboard(patient_id: str):
    try:
        _apply_certifi_fix_for_es()
        from ehr_parser import get_dashboard_data

        return get_dashboard_data(patient_id)
    except Exception as e:
        err = str(e)
        # Self-heal missing demo index/docs on first dashboard hit, then retry once.
        if patient_id == "synthetic-001" and "index_not_found_exception" in err:
            try:
                logger.warning(
                    "Dashboard missing index for %s; attempting automatic ingest and retry",
                    patient_id,
                )
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, lambda: ingest_patient_local(patient_id))
                from ehr_parser import get_dashboard_data as _retry_dashboard_data

                return _retry_dashboard_data(patient_id)
            except Exception as retry_err:
                logger.error("Dashboard auto-heal retry failed: %s", retry_err, exc_info=True)
                raise HTTPException(status_code=500, detail=str(retry_err))

        logger.error("Dashboard error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=err)


async def _stream_agent_response(websocket: WebSocket, patient_id: str, transcript: str) -> None:
    from elastic_client import get_elastic_client
    from search import get_patient_summary

    es = get_elastic_client()
    patient_context = get_patient_summary(es, patient_id)

    async for event in conversational_doctor.process_query(patient_id, transcript, patient_context):
        await websocket.send_json(event)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("WebSocket connection attempt")
    await websocket.accept()
    logger.info("WebSocket accepted")

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
            except asyncio.TimeoutError:
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
                continue
            except WebSocketDisconnect:
                break

            message = json.loads(data)

            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if message.get("type") not in ("voice_transcript", "text_query"):
                await websocket.send_json(
                    {"type": "error", "message": f"Unknown message type: {message.get('type')}"}
                )
                continue

            patient_id = message.get("patient_id")
            transcript = message.get("transcript")
            if not patient_id or not transcript:
                await websocket.send_json({"type": "error", "message": "Missing patient_id or transcript"})
                continue

            await websocket.send_json({"type": "ack", "message": "Processing query..."})

            try:
                await _stream_agent_response(websocket, patient_id, transcript)
            except Exception as e:
                logger.error("Agent stream error: %s", e, exc_info=True)
                try:
                    await websocket.send_json({"type": "error", "message": str(e)})
                except Exception:
                    pass

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error("WebSocket error: %s", e, exc_info=True)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", os.getenv("GATEWAY_PORT", "8000")))
    uvicorn.run(app, host="0.0.0.0", port=port)
