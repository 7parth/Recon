# Recon - Job Application Agent

## Overview

The Job Application Agent is an autonomous, human-supervised system that finds job listings matching a candidate's profile, tailors a resume and cover letter for each one, and submits the application via browser automation — pausing for human approval before anything is actually sent. It's built for individual job seekers (starting with the builder's own internship/new-grad search) who want to apply to more roles without sacrificing the quality of each application, and it solves the core tension of job hunting at scale: broad reach usually means generic, low-effort applications, while tailored applications don't scale past a handful a day.

## Goals

1. Cut the time to produce a tailored resume + cover letter for a single job listing from ~20-30 minutes of manual editing to under 2 minutes of review time.
2. Reach a 3-5x increase in weekly applications submitted without lowering per-application tailoring quality (measured by ATS keyword coverage and match score).
3. Maintain a 100% human-approval checkpoint before submission — zero applications go out without explicit sign-off.
4. Successfully automate form-fill and submission on at least two major ATS platforms (e.g. Greenhouse, Lever) with a measurable success rate (>90% successful submits on supported platforms).

## Core User Flow

1. User uploads/updates their base resume; the agent parses it into a structured profile (skills, experience, education).
2. User defines search criteria (roles, locations, keywords) or supplies a specific job URL/JD directly.
3. Agent finds and parses matching job listings, scoring each against the resume profile.
4. For listings above the match threshold, the agent drafts a tailored resume and cover letter, optimized for ATS keywords from the JD.
5. Agent pauses and surfaces the tailored documents to the user for review.
6. User approves, edits, or rejects (with feedback, triggering a re-tailor).
7. On approval, the agent fills out the application form via browser automation and submits it.
8. Agent logs the outcome (applied / failed / skipped) and moves to the next listing.
9. User can view application history and status at any point.

## Features

### Resume & Job Matching

- Resume parsing into a structured, reusable candidate profile
- Job description parsing into structured requirements and ATS keywords
- Semantic match scoring (embeddings + LLM judgment) between profile and JD
- Configurable match-score threshold to auto-skip weak-fit listings

### Tailoring

- LLM-generated tailored resume bullets and summary per listing
- LLM-drafted cover letter per listing
- ATS keyword optimization pass on generated documents

### Human-in-the-Loop Review

- Mandatory approval checkpoint before any submission
- Reject-with-feedback loop that re-runs tailoring with the user's notes
- Persisted review queue (survives restarts via LangGraph checkpointing)

### Application Automation

- Browser automation (Playwright) for form-fill and submission
- Initial support for standardized ATS platforms (Greenhouse, Lever)
- Resume/cover letter file upload handling per platform

### Tracking & History

- Per-application status tracking (skipped / pending review / applied / failed)
- Searchable history of past applications and the documents used for each
- Basic run triggering and status API (FastAPI)

## Scope

### In Scope

- Single-user, self-hosted operation (not a multi-tenant SaaS)
- Resume/JD parsing, matching, and tailoring via LLM
- Human approval checkpoint before submission
- Browser automation for Greenhouse- and Lever-hosted application forms
- Application history and status tracking in PostgreSQL

### Out of Scope

- Automated applying on LinkedIn, Indeed, or other platforms whose ToS restrict bot-driven applications
- Multi-user/account support, billing, or SaaS-style onboarding
- Interview scheduling, follow-up email automation, or offer negotiation
- Fully unsupervised submission (no bypass of the human-review checkpoint)
- Resume design/formatting overhaul — the agent edits content, not visual template

## Success Criteria

1. A user can upload a resume and, from a single job URL, receive a tailored resume + cover letter ready for review in under 2 minutes.
2. The human-review checkpoint correctly blocks submission until explicit approval is recorded, verified across at least 20 test runs with no bypass.
3. The agent successfully completes end-to-end submission (form-filled and confirmed) on both Greenhouse and Lever test listings with a >90% success rate.
4. Application history in PostgreSQL accurately reflects real-world status (applied/failed/skipped) for 100% of processed listings.
5. Match scoring correctly skips clearly mismatched listings (validated against a hand-labeled test set) with acceptable precision/recall.

## Multi-Agent Extension

The workflow is implemented as a supervisor-based multi-agent system. A Planner Agent coordinates specialized agents rather than performing all reasoning itself. Resume, Job and Company agents execute independently and share structured state through LangGraph before downstream agents perform matching, ATS optimization, tailoring, review and submission.
