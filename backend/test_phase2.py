import asyncio
from sqlmodel import Session, select
from src.database.engine import engine, create_db_and_tables
from src.database.models import Job, JobNote, SystemSettings
from src.nlp.ats_scorer import ATSEngine

def test_db():
    print("--- Creating DB ---")
    create_db_and_tables()
    
    with Session(engine) as session:
        # Create Job
        new_job = Job(title="Senior Engineer", company="Google", url="http://google.com/jobs")
        session.add(new_job)
        session.commit()
        session.refresh(new_job)
        
        # Add Note
        note = JobNote(job_id=new_job.id, content="Need to review system design.")
        session.add(note)
        session.commit()
        session.refresh(new_job)
        
        # Verify
        db_job = session.exec(select(Job).where(Job.company == "Google")).first()
        print(f"Created Job: {db_job.title} at {db_job.company}")
        print(f"Job Notes: {[n.content for n in db_job.notes]}")

async def test_ats():
    print("\n--- Testing ATS Engine ---")
    engine = ATSEngine()
    score = await engine.score_resume(
        resume_text="I am a software engineer with 5 years of Python and React experience.",
        job_description="We need a Python developer who knows React and FastAPI."
    )
    print(f"Exact Matches: {score.exact_matches}")
    print(f"Missing Keywords: {score.missing_keywords}")
    print(f"Cosine Similarity: {score.cosine_similarity}")

if __name__ == "__main__":
    test_db()
    asyncio.run(test_ats())
