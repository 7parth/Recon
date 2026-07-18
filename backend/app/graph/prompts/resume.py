"""
prompts/resume.py — Prompt template for the Resume Agent.

Kept separate from the agent so prompts can be:
  - Iterated independently without touching agent logic
  - Version-controlled and compared easily
  - Reused across agents if needed
"""

# ── System prompt ─────────────────────────────────────────────────────────────
# The system message sets the LLM's role and output contract.
# We tell it EXACTLY what JSON shape to produce — this is critical for
# with_structured_output() to work reliably.

RESUME_SYSTEM_PROMPT = """You are a resume parsing assistant. Your job is to extract structured \
information from a candidate's resume text.

Extract the following fields:
- skills: a list of technical and soft skills mentioned anywhere in the resume
- experience_years: total years of professional experience as a float (e.g. 2.5). \
  Infer from dates if not stated explicitly. Use 0.0 if unclear.
- summary: a 2-3 sentence professional summary of the candidate, written in third person. \
  If the resume has one, distill it. Otherwise synthesise one from the content.

Respond ONLY with valid JSON matching the schema. No commentary, no markdown fences."""

# ── Human/user prompt ─────────────────────────────────────────────────────────
# {resume_text} is a format placeholder — .format(resume_text=...) fills it in.

RESUME_USER_PROMPT = """Here is the candidate's resume:

{resume_text}

Extract the structured profile now."""
