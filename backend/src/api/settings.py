from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
import os
import traceback

from src.database.engine import engine
from src.database.models import UserPreference, SystemSettings
from src.scraper.engine import ScraperEngine, Platform
from src.core.gatekeeper import Gatekeeper
from src.applier.auto_applier import AutoApplier
from src.core.pipeline import kairos_pipeline
from src.nlp.llm_generator import LLMTailor

router = APIRouter(tags=["Settings"])

def get_session():
    with Session(engine) as session:
        yield session

class ResumePayload(BaseModel):
    content: str

class PreferencePayload(BaseModel):
    category: str
    value: str
    is_strict: bool

@router.post("/resume")
def save_resume(payload: ResumePayload):
    """Save the base resume to the local filesystem."""
    resumes_dir = os.path.join(os.getenv('APPDATA', ''), 'Kairos', 'resumes')
    os.makedirs(resumes_dir, exist_ok=True)
    resume_path = os.path.join(resumes_dir, "B_default_resume.md")
    
    with open(resume_path, "w", encoding="utf-8") as f:
        f.write(payload.content)
    return {"message": "Resume saved successfully", "path": resume_path}

@router.get("/resume")
def get_resume():
    """Get the current base resume."""
    resumes_dir = os.path.join(os.getenv('APPDATA', ''), 'Kairos', 'resumes')
    resume_path = os.path.join(resumes_dir, "B_default_resume.md")
    
    if os.path.exists(resume_path):
        with open(resume_path, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    return {"content": ""}

@router.get("/preferences")
def get_preferences(session: Session = Depends(get_session)):
    return session.exec(select(UserPreference)).all()

@router.post("/preferences")
def add_preference(payload: PreferencePayload, session: Session = Depends(get_session)):
    pref = UserPreference(category=payload.category, value=payload.value, is_strict=payload.is_strict)
    session.add(pref)
    session.commit()
    session.refresh(pref)
    return pref

@router.delete("/preferences/{pref_id}")
def delete_preference(pref_id: str, session: Session = Depends(get_session)):
    pref = session.get(UserPreference, pref_id)
    if pref:
        session.delete(pref)
        session.commit()
    return {"message": "Deleted"}

@router.post("/trigger_test")
async def trigger_pipeline_test(session: Session = Depends(get_session)):
    """Visually tests the pipeline by returning the LLM outputs to the UI."""
    try:
        prefs = session.exec(select(UserPreference)).all()
        
        resume_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "base_resume.md")
        if not os.path.exists(resume_path):
            raise HTTPException(status_code=400, detail="Please upload a base resume first.")
            
        with open(resume_path, "r") as f:
            base_resume = f.read()

        # 1. Scrape
        scraper = ScraperEngine()
        gatekeeper = Gatekeeper()
        tailor = LLMTailor(model="llama3.1")
        
        # We will just fetch 1 mock job for testing
        jobs = await scraper.fetch_jobs(Platform.INTERNSHALA, "Python Developer")
        if not jobs:
            return {"status": "error", "message": "No jobs found"}
            
        job = jobs[0] # TechCorp job

        # 2. Gatekeeper
        evaluated = await gatekeeper.evaluate_job(job, prefs, base_resume)
        if not evaluated['is_match']:
            return {
                "status": "discarded",
                "message": f"Job discarded due to strict constraints: {evaluated['failed_strict_prefs']}"
            }
            
        # 3. LLM Tailor
        tailored_resume = await tailor.tailor_resume(base_resume, job["description"])
        cover_letter = await tailor.generate_cover_letter(base_resume, job)
        
        # 4. Auto-Applier
        applier = AutoApplier(headless=False)
        success = await applier.apply_to_job(job["url"], tailored_resume, cover_letter)
        
        return {
            "status": "success" if success else "error",
            "job": job,
            "tailored_resume": tailored_resume,
            "cover_letter": cover_letter,
            "message": "Dry Run Application Complete!" if success else "Failed to auto-apply"
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}

@router.post("/trigger_sweep")
async def trigger_sweep():
    try:
        kairos_pipeline.sweep_now()
        return {"status": "success", "message": "Career Agent sweep triggered in the background!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/system")
def get_system_settings(session: Session = Depends(get_session)):
    settings = session.exec(select(SystemSettings)).first()
    if not settings:
        settings = SystemSettings()
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return {
        "auto_apply_enabled": settings.auto_apply_enabled,
        "is_daemon_running": kairos_pipeline.is_running
    }

@router.post("/system/toggle_auto_apply")
def toggle_auto_apply(session: Session = Depends(get_session)):
    settings = session.exec(select(SystemSettings)).first()
    if not settings:
        settings = SystemSettings()
        session.add(settings)
    settings.auto_apply_enabled = not settings.auto_apply_enabled
    session.commit()
    return {"auto_apply_enabled": settings.auto_apply_enabled}
