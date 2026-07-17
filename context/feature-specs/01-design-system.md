Read `AGENTS.md` before starting.

we are adding the design system.

backend/
│
├── app/
│   │
│   ├── main.py                     # FastAPI entrypoint
│   ├── config.py                   # Settings
│   ├── dependencies.py             # Dependency injection
│   │
│   ├── graph/
│   │   ├── builder.py              # Builds LangGraph
│   │   ├── state.py                # ApplicationState
│   │   ├── router.py               # Conditional routing
│   │   ├── constants.py
│   │   │
│   │   ├── agents/
│   │   │   ├── planner.py
│   │   │   ├── resume_agent.py
│   │   │   ├── job_agent.py
│   │   │   ├── company_agent.py
│   │   │   ├── match_agent.py
│   │   │   ├── ats_agent.py
│   │   │   ├── tailoring_agent.py
│   │   │   ├── cover_letter_agent.py
│   │   │   ├── human_review_agent.py
│   │   │   ├── apply_agent.py
│   │   │   └── tracking_agent.py
│   │   │
│   │   ├── prompts/
│   │   │   ├── planner.py
│   │   │   ├── resume.py
│   │   │   ├── job.py
│   │   │   ├── tailoring.py
│   │   │   └── cover_letter.py
│   │   │
│   │   └── tools/
│   │       ├── resume_parser.py
│   │       ├── jd_parser.py
│   │       ├── embeddings.py
│   │       ├── search.py
│   │       ├── browser.py
│   │       └── llm.py
│   │
│   ├── automation/
│   │   ├── greenhouse.py
│   │   ├── lever.py
│   │   ├── workday.py
│   │   ├── ashby.py
│   │   ├── smartrecruiters.py
│   │   └── dispatcher.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── application.py
│   │   │   ├── review.py
│   │   │   ├── resume.py
│   │   │   ├── jobs.py
│   │   │   ├── history.py
│   │   │   └── health.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── application.py
│   │   │   ├── resume.py
│   │   │   ├── review.py
│   │   │   └── common.py
│   │   │
│   │   └── middleware/
│   │
│   ├── db/
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── application.py
│   │   │   ├── resume.py
│   │   │   ├── company.py
│   │   │   ├── job.py
│   │   │   └── review.py
│   │   │
│   │   ├── repositories/
│   │   │   ├── application_repo.py
│   │   │   ├── resume_repo.py
│   │   │   └── job_repo.py
│   │   │
│   │   └── migrations/
│   │
│   ├── services/
│   │   ├── embedding_service.py
│   │   ├── resume_service.py
│   │   ├── jd_service.py
│   │   ├── company_service.py
│   │   ├── ats_service.py
│   │   └── notification_service.py
│   │
│   ├── vectorstore/
│   │   ├── faiss.py
│   │   └── indexing.py
│   │
│   ├── workers/
│   │   ├── celery_app.py
│   │   ├── application_tasks.py
│   │   └── indexing_tasks.py
│   │
│   ├── utils/
│   │   ├── logger.py
│   │   ├── helpers.py
│   │   ├── enums.py
│   │   └── exceptions.py
│   │
│   └── tests/
│       ├── graph/
│       ├── agents/
│       ├── api/
│       └── automation/
│
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── requirements.txt
├── .env
└── README.md