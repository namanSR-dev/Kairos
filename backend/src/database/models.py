from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone
import uuid

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Job(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    title: str
    company: str
    url: str | None = None
    status: str = Field(default="Saved") # Saved, Applied, Interviewing, Offer, Rejected
    raw_job_description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    notes: list["JobNote"] = Relationship(back_populates="job", cascade_delete=True)

class JobNote(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    job_id: str = Field(foreign_key="job.id")
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    job: Job = Relationship(back_populates="notes")

class SkillRoadmap(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    skill_name: str
    priority_level: int = Field(default=1) # 1=High, 2=Med, 3=Low
    json_checklist: str # Stored as JSON string
    is_completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProfileOptimization(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    platform: str # e.g., "GitHub", "LinkedIn"
    artifact_type: str # e.g., "README.md", "Headline"
    generated_content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Notification(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    type: str # New Match, Daily Summary, Storage Alert
    title: str
    message: str
    action_url: str | None = None
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SystemSettings(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True) # Singleton row
    auto_apply_enabled: bool = Field(default=False)
    ats_strict_mode: bool = Field(default=True)
