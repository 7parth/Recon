                                            USER
                                              │
                                              ▼
                                 ┌────────────────────┐
                                 │   FastAPI Backend  │
                                 └─────────┬──────────┘
                                           │
                                           ▼
                           ┌────────────────────────────────┐
                           │      Planner (Supervisor)      │
                           │                                │
                           │ • Understand user request      │
                           │ • Decide execution plan        │
                           │ • Schedule parallel agents     │
                           │ • Handle retries/errors        │
                           └──────────────┬─────────────────┘
                                          │
                 ┌────────────────────────┼────────────────────────┐
                 │                        │                        │
                 ▼                        ▼                        ▼
      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
      │ Resume Agent    │      │ Job Agent       │      │ Company Agent   │
      │                 │      │                 │      │                 │
      │ Parse Resume    │      │ Parse JD        │      │ Research        │
      │ Extract Skills  │      │ Extract Skills  │      │ Company         │
      │ Build Profile   │      │ ATS Keywords    │      │ Culture/News    │
      └────────┬────────┘      └────────┬────────┘      └────────┬────────┘
               │                        │                        │
               └──────────────┬─────────┴──────────────┬─────────┘
                              │                        │
                              ▼                        ▼
                  ┌────────────────────┐      ┌──────────────────┐
                  │   Match Agent      │      │    ATS Agent     │
                  │                    │      │                  │
                  │ Semantic Match     │      │ Keyword Analysis │
                  │ Gap Analysis       │      │ ATS Report       │
                  └─────────┬──────────┘      └────────┬─────────┘
                            │                          │
                            └──────────────┬───────────┘
                                           │
                                           ▼
                          ┌────────────────────────────────┐
                          │ Resume Tailoring Agent         │
                          │                                │
                          │ Rewrite bullets                │
                          │ Optimize projects              │
                          │ Preserve factual accuracy      │
                          └──────────────┬─────────────────┘
                                         │
                                         ▼
                          ┌────────────────────────────────┐
                          │ Cover Letter Agent             │
                          │                                │
                          │ Personalized cover letter      │
                          │ Uses company context           │
                          └──────────────┬─────────────────┘
                                         │
                                         ▼
                     ┌───────────────────────────────────────────┐
                     │       Human Review Agent (Interrupt)      │
                     │                                           │
                     │ Review Resume                             │
                     │ Review Cover Letter                       │
                     │                                           │
                     │ Approve │ Reject │ Edit │ Feedback        │
                     └──────────────┬────────────────────────────┘
                                    │
                   ┌────────────────┴────────────────┐
                   │                                 │
            Rejected / Edit                   Approved
                   │                                 │
                   ▼                                 ▼
      Resume Tailoring Agent              ┌────────────────────┐
             (loop)                       │    Apply Agent     │
                                          │                    │
                                          │ Dispatch to ATS    │
                                          │ Playwright only    │
                                          └─────────┬──────────┘
                                                    │
                   ┌────────────────────────────────┼─────────────────────────┐
                   │                                │                         │
                   ▼                                ▼                         ▼
          Greenhouse Module                Lever Module              Future ATS Modules
                   │                                │                         │
                   └────────────────────────────────┼─────────────────────────┘
                                                    │
                                                    ▼
                                   ┌────────────────────────────┐
                                   │     Tracking Agent         │
                                   │                            │
                                   │ Store Application          │
                                   │ Status & Analytics         │
                                   │ PostgreSQL                │
                                   └─────────────┬──────────────┘
                                                 │
                                                 ▼
                                              Dashboard