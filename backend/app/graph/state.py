from __future__ import annotations

from typing import TypedDict, Optional, Literal
from pydantic import BaseModel

class CandidateProfile(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    linkedin_url: Optional[str] = None
    leetcode_url: Optional[str] = None
    skills: list[str]
    experience_years: float
    summary: str


class JobProfile(BaseModel):
    required_skills: list[str]
    responsibilities: str
    experience_required: float


class CompanyProfile(BaseModel):
    name: str
    industry: Optional[str] = None
    size: Optional[str] = None
    culture_notes: Optional[str] = None


class MatchResult(BaseModel):
    overall_score: float
    strengths: list[str]
    weaknesses: list[str]
    gap_areas: list[str]


class ATSReport(BaseModel):
    keyword_match: float
    section_score: dict[str, int]
    recommendations: str


class TailoredResume(BaseModel):
    content: str
    changes_made: str


class CoverLetter(BaseModel):
    content: str


class ApplicationState(TypedDict):
    resume_raw: str                # raw text of uploaded resume
    job_url: str                   # input URL or raw JD text
    resume_profile: Optional[CandidateProfile]
    job_profile: Optional[JobProfile]
    company_profile: Optional[CompanyProfile]
    match_result: Optional[MatchResult]
    ats_report: Optional[ATSReport]
    tailored_resume: Optional[TailoredResume]
    cover_letter: Optional[CoverLetter]
    approval_status: Optional[Literal["approved", "rejected", "pending"]]
    rejection_feedback: Optional[str]   # user's feedback on rejection
    submission_status: Optional[Literal["applied", "failed", "skipped"]]
    error: Optional[str]                # last error message for retries
