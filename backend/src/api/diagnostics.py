from fastapi import APIRouter
from pydantic import BaseModel
import psutil
import GPUtil

router = APIRouter()

class GPUInfo(BaseModel):
    id: int
    name: str
    vram_total_mb: float
    vram_free_mb: float

class SystemDiagnostics(BaseModel):
    ram_total_gb: float
    ram_available_gb: float
    gpus: list[GPUInfo]
    recommendation: str
    can_run_local_llm: bool

@router.get("/", response_model=SystemDiagnostics)
def get_diagnostics():
    # RAM calculation
    ram_info = psutil.virtual_memory()
    ram_total_gb = ram_info.total / (1024 ** 3)
    ram_available_gb = ram_info.available / (1024 ** 3)

    # GPU calculation
    gpus_info = []
    try:
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            gpus_info.append(GPUInfo(
                id=gpu.id,
                name=gpu.name,
                vram_total_mb=gpu.memoryTotal,
                vram_free_mb=gpu.memoryFree
            ))
    except Exception:
        pass # GPUtil might fail if no NVIDIA driver or on Mac

    # Recommendation Logic
    # Llama 3 8B 4-bit quantization requires roughly 6-8GB of unified memory or VRAM.
    # Let's say we need > 8GB RAM minimum, and ideally a GPU with > 6GB VRAM or system with > 16GB RAM.
    
    can_run_local_llm = False
    recommendation = "Your system lacks the required memory. Please use the Gemini API option."

    if gpus_info and any(g.vram_total_mb > 6000 for g in gpus_info):
        can_run_local_llm = True
        recommendation = "Your GPU meets criteria! The app will run smoothly locally via Ollama."
    elif ram_total_gb >= 15.0: # 16GB systems usually show ~15.x
        can_run_local_llm = True
        recommendation = "Your 16GB+ RAM matches our criteria, so the app will run smoothly locally via Ollama."

    return SystemDiagnostics(
        ram_total_gb=round(ram_total_gb, 2),
        ram_available_gb=round(ram_available_gb, 2),
        gpus=gpus_info,
        recommendation=recommendation,
        can_run_local_llm=can_run_local_llm
    )
