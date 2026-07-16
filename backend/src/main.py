from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import diagnostics

app = FastAPI(
    title="Kairos API",
    description="Backend engine for the Kairos AI Career Architect",
    version="0.1.0",
)

# Allow Electron frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the Electron origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagnostics.router, prefix="/api/diagnostics", tags=["Diagnostics"])

@app.get("/")
def read_root():
    return {"status": "Kairos API is running"}
