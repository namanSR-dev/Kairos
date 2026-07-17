import sys
import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.api.diagnostics import router as diagnostics_router
from src.api.jobs import router as jobs_router
from src.api.settings import router as settings_router
from src.api.ollama_api import router as ollama_router
from src.database.engine import create_db_and_tables
from src.core.pipeline import kairos_pipeline
from src.nlp.ollama_manager import OllamaManager
import logging

async def background_model_pull():
    import json
    import time
    if await OllamaManager.is_running():
        missing = await OllamaManager.get_missing_models()
        for m in missing:
            print(f"\n[Kairos] Auto-pulling missing model: {m} (this may take a few minutes)...")
            start_time = time.time()
            last_print_time = 0
            
            async for chunk_str in OllamaManager.pull_model(m):
                try:
                    data = json.loads(chunk_str)
                    if "completed" in data and "total" in data:
                        completed = data["completed"]
                        total = data["total"]
                        if total > 0:
                            percent = (completed / total) * 100
                            now = time.time()
                            
                            # Print progress every 0.5 seconds to avoid spamming terminal
                            if now - last_print_time > 0.5 or completed == total:
                                elapsed = now - start_time
                                speed_mbps = (completed / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                                remaining_bytes = total - completed
                                eta_seconds = remaining_bytes / (speed_mbps * 1024 * 1024) if speed_mbps > 0 else 0
                                
                                # Format ETA
                                eta_mins, eta_secs = divmod(int(eta_seconds), 60)
                                eta_str = f"{eta_mins}m {eta_secs}s" if speed_mbps > 0 else "Calculating..."
                                
                                # Use \r to overwrite the same line in terminal
                                print(f"\r[Kairos] {m}: {percent:.1f}% | Speed: {speed_mbps:.1f} MB/s | ETA: {eta_str}    ", end="", flush=True)
                                last_print_time = now
                except json.JSONDecodeError:
                    pass
            print(f"\n[Kairos] Successfully pulled {m}.")
    else:
        logger = logging.getLogger("uvicorn")
        logger.warning("Ollama is offline. Skipping model auto-pull.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database on startup
    create_db_and_tables()
    
    # [TEMPORARY TEST HOOK]
    # Fire and forget the model pull so it doesn't block FastAPI startup!
    import asyncio
    # asyncio.create_task(background_model_pull())

    # Start the background daemon
    kairos_pipeline.start()
    
    yield
    
    # Shutdown the daemon gracefully
    kairos_pipeline.stop()

app = FastAPI(
    title="Kairos API",
    description="Backend engine for the Kairos AI Career Architect",
    version="0.1.0",
    lifespan=lifespan
)

# Allow Electron frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the Electron origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagnostics_router, prefix="/api/diagnostics", tags=["Diagnostics"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])
app.include_router(ollama_router, prefix="/api", tags=["Ollama"])

@app.get("/")
def read_root():
    return {"status": "Kairos API is running"}
