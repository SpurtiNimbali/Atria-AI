"""
FastAPI WebSocket gateway for EHR Copilot.
Thin proxy between frontend and agent (local or Modal).
"""
import json
import time
# #region agent log
try:
    with open('/Users/spurtinimbali/Desktop/TreeHacks/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"runId":"startup","hypothesisId":"A","location":"main.py:6","message":"Module import started","data":{},"timestamp":int(time.time()*1000)}) + '\n')
except (PermissionError, OSError):
    pass  # Logging disabled due to permissions
# #endregion
# Fix certifi compatibility issue with Python 3.14
import certifi
if not hasattr(certifi, 'where'):
    import ssl
    import os as os_module
    def certifi_where():
        # Fallback to system certs or certifi's cert file
        if hasattr(certifi, '__file__') and certifi.__file__:
            cert_path = os_module.path.join(os_module.path.dirname(certifi.__file__), 'cacert.pem')
            if os_module.path.exists(cert_path):
                return cert_path
        # Use system default
        default_paths = ssl.get_default_verify_paths()
        return default_paths.cafile or default_paths.capath or '/etc/ssl/cert.pem'
    certifi.where = certifi_where

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import json
import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load .env file (handle permission errors gracefully)
try:
    load_dotenv()
except PermissionError:
    logger.warning("⚠️ Could not load .env file (permission denied) - using environment variables")
    pass

logger.info("🚀 Gateway starting up...")
# #region agent log
try:
    with open('/Users/spurtinimbali/Desktop/TreeHacks/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"runId":"startup","hypothesisId":"B","location":"main.py:43","message":"After .env load","data":{"openai_key_set":bool(os.getenv("OPENAI_API_KEY"))},"timestamp":int(time.time()*1000)}) + '\n')
except (PermissionError, OSError):
    pass  # Logging disabled due to permissions
# #endregion

# Set required environment variables (only if not already set)
if not os.getenv("OPENAI_API_KEY"):
    logger.warning("⚠️ OPENAI_API_KEY not set in environment")
if not os.getenv("JINA_API_KEY"):
    logger.warning("⚠️ JINA_API_KEY not set in environment")
if not os.getenv("ELASTIC_URL"):
    os.environ.setdefault("ELASTIC_URL", "http://localhost:9200")

# Modal app configuration
MODAL_APP_NAME = os.getenv("MODAL_APP_NAME", "ehr-copilot")  # Default app name
MODAL_APP_ID = os.getenv("MODAL_APP_ID")  # Optional: specific app ID if needed

# Add modal directory to path for local agent imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../modal"))

app = FastAPI(title="EHR Copilot Gateway")

# CORS configuration - supports both local dev and production
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001", 
    "http://localhost:5173",
]

# Add production origins from environment variable if set
if os.getenv("ALLOWED_ORIGINS"):
    allowed_origins.extend(os.getenv("ALLOWED_ORIGINS").split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use local agent (Option 2 - Hybrid Approach)
USE_LOCAL_AGENT = True  # Set to False to use Modal (requires Modal deployment - currently has path issues)

# Initialize function references (will be set based on USE_LOCAL_AGENT)
ingest_patient_fn = None
answer_fn = None

if not USE_LOCAL_AGENT:
    # Connect to deployed Modal app
    try:
        import sys
        import modal
        modal_path = os.path.join(os.path.dirname(__file__), "../modal")
        if modal_path not in sys.path:
            sys.path.insert(0, modal_path)
        
        # Import the app module - functions will be available
        import modal_app
        
        # Access the app instance
        _app = modal_app.app
        
        # Access functions directly - they're bound to the app
        ingest_patient_fn = modal_app.ingest_patient
        answer_fn = modal_app.answer
        
        # CRITICAL: Hydrate functions by ensuring app is served
        # Modal functions need the app to be "active" to work
        # We'll serve the app in the background or ensure it's deployed
        try:
            # Try to ensure app is served by accessing it
            # This might trigger hydration
            _ = _app.name
            logger.info(f"✅ Modal app module loaded: {_app.name}")
        except Exception as e:
            logger.warning(f"⚠️ App access warning: {e}")
        
        # Log app info
        app_info = f"Modal app: {MODAL_APP_NAME}"
        if MODAL_APP_ID:
            app_info += f" (ID: {MODAL_APP_ID})"
        logger.info(f"✅ Connected to Modal app - {app_info}")
        logger.warning(f"⚠️  IMPORTANT: Modal functions require the app to be served.")
        logger.warning(f"   Run: cd modal && modal serve modal_app.py")
        logger.warning(f"   Or ensure the app is deployed: modal deploy modal_app.py")
    except ImportError as e:
        logger.error(f"❌ Failed to import Modal app: {e}")
        logger.error(f"   Make sure Modal is installed: pip install modal")
        logger.error(f"   And that modal_app.py exists in the modal directory")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to initialize Modal: {e}", exc_info=True)
        raise
else:
    # Import conversational doctor - single AI with tools
    # #region agent log
    try:
        with open('/Users/spurtinimbali/Desktop/TreeHacks/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"runId":"startup","hypothesisId":"C","location":"main.py:125","message":"Before importing conversational_doctor","data":{"sys_path":sys.path[:3]},"timestamp":int(time.time()*1000)}) + '\n')
    except (PermissionError, OSError):
        pass  # Logging disabled due to permissions
    # #endregion
    try:
        # #region agent log
        try:
            with open('/Users/spurtinimbali/Desktop/TreeHacks/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"runId":"startup","hypothesisId":"C","location":"main.py:128","message":"About to import ConversationalDoctor","data":{},"timestamp":int(time.time()*1000)}) + '\n')
        except (PermissionError, OSError):
            pass  # Logging disabled due to permissions
        # #endregion
        from conversational_doctor import ConversationalDoctor
        # #region agent log
        try:
            with open('/Users/spurtinimbali/Desktop/TreeHacks/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"runId":"startup","hypothesisId":"C","location":"main.py:131","message":"Successfully imported ConversationalDoctor","data":{},"timestamp":int(time.time()*1000)}) + '\n')
        except (PermissionError, OSError):
            pass  # Logging disabled due to permissions
        # #endregion
        from local_ingest import ingest_patient_local
        # #region agent log
        try:
            with open('/Users/spurtinimbali/Desktop/TreeHacks/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"runId":"startup","hypothesisId":"D","location":"main.py:134","message":"About to initialize ConversationalDoctor","data":{},"timestamp":int(time.time()*1000)}) + '\n')
        except (PermissionError, OSError):
            pass  # Logging disabled due to permissions
        # #endregion
        
        # Initialize conversational doctor
        conversational_doctor = ConversationalDoctor()
        # #region agent log
        try:
            with open('/Users/spurtinimbali/Desktop/TreeHacks/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"runId":"startup","hypothesisId":"D","location":"main.py:139","message":"Successfully initialized ConversationalDoctor","data":{},"timestamp":int(time.time()*1000)}) + '\n')
        except (PermissionError, OSError):
            pass  # Logging disabled due to permissions
        # #endregion
        logger.info("✅ ConversationalDoctor initialized - ready for queries")
    except ImportError as e:
        # #region agent log
        try:
            with open('/Users/spurtinimbali/Desktop/TreeHacks/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"runId":"startup","hypothesisId":"C","location":"main.py:145","message":"ImportError caught","data":{"error":str(e),"error_type":type(e).__name__},"timestamp":int(time.time()*1000)}) + '\n')
        except (PermissionError, OSError):
            pass  # Logging disabled due to permissions
        # #endregion
        logger.error(f"❌ Failed to import local agent modules: {e}")
        logger.error(f"   Make sure the modal directory is accessible and all dependencies are installed")
        logger.error(f"   Current sys.path includes: {sys.path[:3]}")
        raise
    except Exception as e:
        # #region agent log
        try:
            with open('/Users/spurtinimbali/Desktop/TreeHacks/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"runId":"startup","hypothesisId":"D","location":"main.py:152","message":"Exception during initialization","data":{"error":str(e),"error_type":type(e).__name__},"timestamp":int(time.time()*1000)}) + '\n')
        except (PermissionError, OSError):
            pass  # Logging disabled due to permissions
        # #endregion
        logger.error(f"❌ Failed to initialize ConversationalDoctor: {e}", exc_info=True)
        raise


class VoiceTranscript(BaseModel):
    patient_id: str
    transcript: str


class RefreshRequest(BaseModel):
    patient_id: str


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "EHR Copilot Gateway",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}


class TTSRequest(BaseModel):
    text: str


@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using ElevenLabs API.
    Returns audio/mpeg stream.
    """
    try:
        import httpx
        
        api_key = os.getenv("ELEVENLABS_API_KEY")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
        model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
        
        if not api_key:
            raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not configured")
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": request.text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Return audio as streaming response
            from fastapi.responses import StreamingResponse
            import io
            
            audio_content = response.content
            return StreamingResponse(
                io.BytesIO(audio_content),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline",
                    "Cache-Control": "no-cache"
                }
            )
    
    except httpx.HTTPStatusError as e:
        logger.error(f"ElevenLabs API error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"ElevenLabs API error: {str(e)}")
    except Exception as e:
        logger.error(f"TTS error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/patients/{patient_id}/refresh")
async def refresh_patient(patient_id: str):
    """
    Trigger re-ingestion of patient FHIR data.
    
    Calls either local or Modal ingest function based on USE_LOCAL_AGENT.
    """
    try:
        if USE_LOCAL_AGENT:
            # Call local ingest function
            result = ingest_patient_local(patient_id)
        else:
            # Call Modal function
            result = ingest_patient_fn.remote(patient_id)
        
        return {
            "status": "success",
            "patient_id": patient_id,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/patients/{patient_id}/summary")
async def get_patient_summary(patient_id: str):
    """
    Get summary of available patient data from Elasticsearch.
    """
    try:
        # This could call a Modal function or directly query Elastic
        # For now, return a placeholder
        return {
            "patient_id": patient_id,
            "status": "available",
            "message": "Use refresh endpoint to update data"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/patients/{patient_id}/dashboard")
async def get_patient_dashboard(patient_id: str):
    """
    Get comprehensive dashboard data for a patient from Elasticsearch.
    """
    try:
        if USE_LOCAL_AGENT:
            import sys
            import os
            modal_path = os.path.join(os.path.dirname(__file__), "../modal")
            if modal_path not in sys.path:
                sys.path.insert(0, modal_path)
            
            # Apply certifi fix before importing elasticsearch-dependent modules
            import certifi
            if not hasattr(certifi, 'where'):
                import ssl
                def certifi_where():
                    if hasattr(certifi, '__file__') and certifi.__file__:
                        cert_path = os.path.join(os.path.dirname(certifi.__file__), 'cacert.pem')
                        if os.path.exists(cert_path):
                            return cert_path
                    default_paths = ssl.get_default_verify_paths()
                    return default_paths.cafile or default_paths.capath or '/etc/ssl/cert.pem'
                certifi.where = certifi_where
            
            from ehr_parser import get_dashboard_data
            dashboard_data = get_dashboard_data(patient_id)
            return dashboard_data
        else:
            # For Modal, would call a function
            return {
                "patient_id": patient_id,
                "error": "Modal dashboard endpoint not implemented"
            }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def map_doctor_event_to_frontend(event: dict) -> dict:
    """
    Map conversational doctor events to frontend format.
    """
    event_type = event.get("type")
    
    if event_type == "text_chunk":
        # Text chunks go as reasoning steps for visual feedback
        return {
            "type": "reasoning_step",
            "emoji": "👩‍⚕️",
            "step": "Dr. Chen",
            "content": event["text"]
        }
    
    elif event_type == "tool_start":
        # Show tool being used
        tool_name = event["tool"]
        tool_emojis = {
            "search_medical_literature": "📚",
            "check_drug_interactions": "💊",
            "analyze_lab_trends": "📊",
            "predict_treatment_risk": "⚠️",
            "calculate_personalized_dose": "🧮",
            "query_knowledge_graph": "🧬",
            "search_clinical_trials": "🔬"
        }
        return {
            "type": "reasoning_step",
            "emoji": tool_emojis.get(tool_name, "🔧"),
            "step": f"Using: {tool_name.replace('_', ' ').title()}",
            "content": f"Checking {tool_name.replace('_', ' ')}..."
        }
    
    elif event_type == "tool_complete":
        # Show tool completion
        tool_name = event["tool"]
        return {
            "type": "reasoning_step",
            "emoji": "✅",
            "step": f"Completed: {tool_name.replace('_', ' ').title()}",
            "content": "Data retrieved"
        }
    
    elif event_type == "response_complete":
        # Final response
        return {
            "type": "response",
            "content": event["full_text"]
        }
    
    else:
        return event


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice interaction.
    
    Receives: {"type": "voice_transcript", "patient_id": "...", "transcript": "..."}
    Sends: Stream of events from Modal agent
    """
    logger.info("🔌 WebSocket connection attempt")
    await websocket.accept()
    logger.info("✅ WebSocket accepted, waiting for messages...")
    
    try:
        while True:
            try:
                # Receive message from frontend (with timeout)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                    continue
                except:
                    logger.info("Connection closed during ping")
                    break
            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break
            
            logger.info(f"📨 Raw data received: {data[:200]}")
            message = json.loads(data)
            logger.info(f"📨 Parsed message: {message}")
            
            if message.get("type") == "voice_transcript":
                patient_id = message.get("patient_id")
                transcript = message.get("transcript")
                
                if not patient_id or not transcript:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Missing patient_id or transcript"
                    })
                    continue
                
                # Send acknowledgment
                await websocket.send_json({
                    "type": "ack",
                    "message": "Processing query..."
                })
                
                try:
                    logger.info(f"👩‍⚕️ Dr. Chen speaking with patient {patient_id}: {transcript}")
                    
                    if USE_LOCAL_AGENT:
                        # Get patient context
                        try:
                            from elastic_client import get_elastic_client
                            from search import get_patient_summary
                        except ImportError as import_err:
                            logger.error(f"❌ Failed to import elastic_client or search: {import_err}")
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Backend configuration error: {str(import_err)}"
                            })
                            continue
                        
                        try:
                            es = get_elastic_client()
                            patient_context = get_patient_summary(es, patient_id)
                        except Exception as es_err:
                            logger.error(f"❌ Failed to get patient context: {es_err}", exc_info=True)
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Failed to retrieve patient data: {str(es_err)}"
                            })
                            continue
                        
                        # Stream conversation with tools
                        full_response_text = ""
                        
                        try:
                            logger.info(f"🚀 Starting process_query for: {transcript[:50]}...")
                            event_count = 0
                            async for event in conversational_doctor.process_query(
                                patient_id,
                                transcript,
                                patient_context
                            ):
                                event_count += 1
                                event_type = event.get('type', 'unknown')
                                logger.info(f"📤 Event #{event_count}: {event_type}")
                                
                                # Forward raw events to frontend (frontend handles display)
                                try:
                                    await websocket.send_json(event)
                                    logger.info(f"✅ Sent event #{event_count} ({event_type}) to frontend")
                                except Exception as send_error:
                                    logger.error(f"⚠️ Failed to send event #{event_count}: {send_error}")
                                    if "closed" in str(send_error).lower():
                                        logger.error("❌ WebSocket closed")
                                        break  # Break inner loop only
                            
                            logger.info(f"✅ Conversation completed - sent {event_count} events total")
                        except Exception as doctor_error:
                            logger.error(f"❌ Doctor error: {doctor_error}", exc_info=True)
                            import traceback
                            logger.error(f"Full traceback: {traceback.format_exc()}")
                            try:
                                await websocket.send_json({
                                    "type": "error",
                                    "message": f"Doctor error: {doctor_error}"
                                })
                            except Exception as send_err:
                                logger.error(f"Failed to send error to frontend: {send_err}")
                        # Continue to next iteration - process next query
                        continue
                    
                    else:
                        # Call Modal agent function (synchronous remote call)
                        try:
                            result = answer_fn.remote(patient_id, transcript)
                            
                            for event in result.get("events", []):
                                await websocket.send_json(event)
                        except Exception as modal_error:
                            error_msg = str(modal_error)
                            if "not been hydrated" in error_msg or "not running" in error_msg:
                                logger.error("❌ Modal app not served. Functions need app to be running.")
                                logger.error("   Solution: Run 'cd modal && modal serve modal_app.py' in a separate terminal")
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "Modal app needs to be served. Please run: cd modal && modal serve modal_app.py"
                                })
                            else:
                                raise
                    
                except Exception as e:
                    logger.error(f"❌ Agent error: {e}", exc_info=True)
                    try:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Agent error: {str(e)}"
                        })
                    except:
                        pass  # WebSocket might be closed
                    # Continue loop - process next query
                    logger.info("🔄 Ready for next query after error")
                    continue
            
            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue  # Don't break the loop, just respond to ping
            
            elif message.get("type") == "text_query":
                # Handle text queries (fallback for voice)
                patient_id = message.get("patient_id")
                transcript = message.get("transcript")
                
                if not patient_id or not transcript:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Missing patient_id or transcript"
                    })
                    continue
                
                await websocket.send_json({
                    "type": "ack",
                    "message": "Processing query..."
                })
                
                try:
                    logger.info(f"👩‍⚕️ Dr. Chen processing text query for patient {patient_id}: {transcript}")
                    
                    if USE_LOCAL_AGENT:
                        try:
                            from elastic_client import get_elastic_client
                            from search import get_patient_summary
                        except ImportError as import_err:
                            logger.error(f"❌ Failed to import elastic_client or search: {import_err}")
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Backend configuration error: {str(import_err)}"
                            })
                            continue
                        
                        try:
                            es = get_elastic_client()
                            patient_context = get_patient_summary(es, patient_id)
                        except Exception as es_err:
                            logger.error(f"❌ Failed to get patient context: {es_err}", exc_info=True)
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Failed to retrieve patient data: {str(es_err)}"
                            })
                            continue
                        
                        full_response_text = ""
                        
                        try:
                            async for event in conversational_doctor.process_query(
                                patient_id,
                                transcript,
                                patient_context
                            ):
                                logger.info(f"📤 Streaming event: {event.get('type')}")
                                
                                if event["type"] == "text_chunk":
                                    full_response_text += event["text"]
                                
                                try:
                                    await websocket.send_json(event)
                                except Exception as send_error:
                                    logger.error(f"⚠️ Failed to send event: {send_error}")
                                    if "closed" in str(send_error).lower():
                                        logger.error("❌ WebSocket closed")
                                        break
                            
                            logger.info("✅ Conversation completed successfully")
                        except Exception as doctor_error:
                            logger.error(f"Doctor error: {doctor_error}", exc_info=True)
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Doctor error: {str(doctor_error)}"
                            })
                    else:
                        # Call Modal agent function (synchronous remote call)
                        try:
                            result = answer_fn.remote(patient_id, transcript)
                            
                            for event in result.get("events", []):
                                await websocket.send_json(event)
                        except Exception as modal_error:
                            error_msg = str(modal_error)
                            if "not been hydrated" in error_msg or "not running" in error_msg:
                                logger.error("❌ Modal app not served. Functions need app to be running.")
                                logger.error("   Solution: Run 'cd modal && modal serve modal_app.py' in a separate terminal")
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "Modal app needs to be served. Please run: cd modal && modal serve modal_app.py"
                                })
                            else:
                                raise
                
                except Exception as e:
                    logger.error(f"❌ Agent error: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Agent error: {str(e)}"
                    })
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message.get('type')}"
                })
    
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass


if __name__ == "__main__":
    # #region agent log
    try:
        with open('/Users/spurtinimbali/Desktop/TreeHacks/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"runId":"startup","hypothesisId":"E","location":"main.py:567","message":"About to start uvicorn","data":{"port":int(os.getenv("GATEWAY_PORT", 8000))},"timestamp":int(time.time()*1000)}) + '\n')
    except (PermissionError, OSError):
        pass  # Logging disabled due to permissions
    # #endregion
    import uvicorn
    port = int(os.getenv("GATEWAY_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
