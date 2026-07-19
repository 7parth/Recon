1. project-overview.md (Highest Priority)
Current
Database | PostgreSQL via SQLAlchemy async

Replace with

Database | Supabase PostgreSQL
ORM | SQLAlchemy Async
Authentication | Supabase Auth (Future)
Storage | Supabase Storage
Realtime | Supabase Realtime (Future)
Update Technical Stack

Current

PostgreSQL

↓

Supabase PostgreSQL

SQLAlchemy Async

Supabase Storage
Update Features

Current

Application history in PostgreSQL

↓

Application history persisted in Supabase PostgreSQL

Also replace

LangGraph checkpoints in PostgreSQL

↓

LangGraph checkpoints stored in Supabase PostgreSQL
2. architecture.md

This file needs the biggest update.

Current

Database

PostgreSQL

Replace with

Database

Supabase PostgreSQL

Update the Stack table

Current

Database

PostgreSQL

↓

Database

Supabase PostgreSQL

(SQLAlchemy Async)

Supabase Storage

Update Storage Model

Current

Database

Postgres

↓

Database

Supabase PostgreSQL

Hosted PostgreSQL

Automatic backups

Connection pooling

Update Session/File Storage

Currently you store files locally.

Instead use

Supabase Storage

resume.pdf

tailored_resume.pdf

cover_letter.pdf

Playwright screenshots

This is a major improvement because your documents become accessible from anywhere instead of being tied to one machine.

3. progress-tracker.md

Current Goal

Current

Database layer

SQLAlchemy models

Alembic

Replace with

Supabase integration

Async SQLAlchemy

Storage bucket integration

Alembic migration

LangGraph checkpoint persistence

Completed section

Add

Supabase project created

Storage bucket configured

Environment variables configured

once you finish those steps.

Next Up

Replace

Database.py

with

Supabase connection

Storage upload service

Checkpoint saver
4. code-standards.md

Update the Data section.

Current

Structured metadata belongs in PostgreSQL

↓

Structured metadata belongs in Supabase PostgreSQL.

Current

Tailored resume belongs in PostgreSQL

I'd actually change this.

Store metadata in DB.

Store documents in Storage.

Example

Database

resume_url

cover_letter_url

tailored_resume_url

Storage

resume.pdf

tailored_resume.pdf

cover_letter.pdf

This is much more scalable.

5. AI Workflow Rules

No large changes.

Only add something like

Never access Supabase directly from graph nodes.

All database access must go through repositories/services.

Agents remain pure functions.

This keeps your graph testable.

6. Backend Folder Changes

Current

db/

I'd expand it.

db/

database.py

supabase.py

models/

repositories/

migrations/

Add

storage/

storage.py

resume_storage.py

document_storage.py

Responsibilities

Storage

↓

Upload resume

↓

Return URL

Graph agents never upload files directly.

7. Config

Your config should change from

DATABASE_URL

to

SUPABASE_URL=

SUPABASE_ANON_KEY=

SUPABASE_SERVICE_ROLE_KEY=

DATABASE_URL=

SUPABASE_STORAGE_BUCKET=resumes

SUPABASE_CHECKPOINT_BUCKET=checkpoints
8. New Services

I'd add

services/

storage_service.py

checkpoint_service.py

Responsibilities

storage_service

↓

Upload Resume

↓

Upload Cover Letter

↓

Return Public URL
9. Database Models

Instead of storing

resume_text

I'd store

resume_storage_url

tailored_resume_url

cover_letter_url

Large documents belong in Storage.

Metadata belongs in SQL.

10. LangGraph Checkpointer

This is one place many people overlook.

Instead of

SQLite Saver

or

Local Postgres

configure

AsyncPostgresSaver

↓

Supabase PostgreSQL

This allows interrupted workflows to survive server restarts while using your hosted database.

Summary of Required Changes
File	Change Required	Priority
project-overview.md	Replace PostgreSQL references with Supabase PostgreSQL and Supabase Storage	⭐⭐⭐
architecture.md	Update stack, storage model, and persistence architecture	⭐⭐⭐
progress-tracker.md	Change current DB milestone to Supabase integration	⭐⭐
code-standards.md	Update storage conventions (metadata in DB, files in Storage)	⭐⭐
ai-workflow-rules.md	Add rule that graph nodes must not access Supabase directly	⭐⭐
app/config.py	Add Supabase environment variables	⭐⭐⭐
app/db/	Add supabase.py alongside database.py	⭐⭐⭐
app/storage/	New module for Supabase Storage uploads	⭐⭐⭐
Application ORM models	Store file URLs instead of large document contents	⭐⭐⭐
LangGraph checkpointer	Use PostgreSQL checkpointer pointed at Supabase