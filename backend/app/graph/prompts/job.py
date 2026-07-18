"""
prompts/job.py — Prompt template for the Job Agent.

The Job Agent and Company Agent both consume the same raw JD text,
but extract different things:
  Job Agent    → required skills, responsibilities, experience needed
  Company Agent → company name, industry, size, culture

Keeping prompts here means we can tune extraction quality independently.
"""

JOB_SYSTEM_PROMPT = """You are a job description analyst. Extract structured \
requirements from the job description provided.

Extract the following fields:
- required_skills: list of skills, technologies, or tools explicitly required or preferred. \
  Include both technical (e.g. "Python", "Kubernetes") and soft skills (e.g. "cross-functional collaboration").
- responsibilities: a concise paragraph (3-5 sentences) summarising the core \
  day-to-day responsibilities of the role.
- experience_required: minimum years of experience required as a float. \
  Use 0.0 if the role is entry-level or no experience is mentioned.

Respond ONLY with valid JSON matching the schema. No commentary."""

JOB_USER_PROMPT = """Here is the job description:

{jd_text}

Extract the structured job profile now."""
