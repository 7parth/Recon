FROM applications ORDER BY applications.created_at DESC 
 LIMIT $1::INTEGER OFFSET $2::INTEGER
2026-07-30 12:55:40,114 INFO sqlalchemy.engine.Engine [cached since 1.134s ago] (50, 0)
2026-07-30T12:55:40 | INFO     | sqlalchemy.engine.Engine | [cached since 1.134s ago] (50, 0)
2026-07-30 12:55:40,139 INFO sqlalchemy.engine.Engine COMMIT
2026-07-30T12:55:40 | INFO     | sqlalchemy.engine.Engine | COMMIT
INFO:     127.0.0.1:54791 - "GET /api/v1/history HTTP/1.1" 200 OK
2026-07-30 12:55:44,672 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-07-30T12:55:44 | INFO     | sqlalchemy.engine.Engine | BEGIN (implicit)
2026-07-30 12:55:44,672 INFO sqlalchemy.engine.Engine SELECT applications.id, applications.thread_id, applications.resume_id, applications.job_id, applications.company_id, applications.status, applications.match_score, applications.resume_storage_url, applications.tailored_resume_url, applications.cover_letter_url, applications.rejection_feedback, applications.error_message, applications.created_at, applications.updated_at 
FROM applications 
WHERE applications.thread_id = $1::VARCHAR
2026-07-30T12:55:44 | INFO     | sqlalchemy.engine.Engine | SELECT applications.id, applications.thread_id, applications.resume_id, applications.job_id, applications.company_id, applications.status, applications.match_score, applications.resume_storage_url, applications.tailored_resume_url, applications.cover_letter_url, applications.rejection_feedback, applications.error_message, applications.created_at, applications.updated_at 
FROM applications 
WHERE applications.thread_id = $1::VARCHAR
2026-07-30 12:55:44,672 INFO sqlalchemy.engine.Engine [cached since 55.75s ago] ('8967ab68-3f06-42b7-bfee-3d7db5310aa6',)
2026-07-30T12:55:44 | INFO     | sqlalchemy.engine.Engine | [cached since 55.75s ago] ('8967ab68-3f06-42b7-bfee-3d7db5310aa6',)
2026-07-30 12:55:44,697 INFO sqlalchemy.engine.Engine COMMIT
2026-07-30T12:55:44 | INFO     | sqlalchemy.engine.Engine | COMMIT
INFO:     127.0.0.1:54794 - "GET /api/v1/history/8967ab68-3f06-42b7-bfee-3d7db5310aa6 HTTP/1.1" 200 OK
2026-07-30 12:55:49,427 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-07-30T12:55:49 | INFO     | sqlalchemy.engine.Engine | BEGIN (implicit)
2026-07-30 12:55:49,427 INFO sqlalchemy.engine.Engine SELECT applications.id, applications.thread_id, applications.resume_id, applications.job_id, applications.company_id, applications.status, applications.match_score, applications.resume_storage_url, applications.tailored_resume_url, applications.cover_letter_url, applications.rejection_feedback, applications.error_message, applications.created_at, applications.updated_at 
FROM applications ORDER BY applications.created_at DESC 
 LIMIT $1::INTEGER OFFSET $2::INTEGER
2026-07-30T12:55:49 | INFO     | sqlalchemy.engine.Engine | SELECT applications.id, applications.thread_id, applications.resume_id, applications.job_id, applications.company_id, applications.status, applications.match_score, applications.resume_storage_url, applications.tailored_resume_url, applications.cover_letter_url, applications.rejection_feedback, applications.error_message, applications.created_at, applications.updated_at 
FROM applications ORDER BY applications.created_at DESC 
 LIMIT $1::INTEGER OFFSET $2::INTEGER
2026-07-30 12:55:49,427 INFO sqlalchemy.engine.Engine [cached since 10.45s ago] (50, 0)
2026-07-30T12:55:49 | INFO     | sqlalchemy.engine.Engine | [cached since 10.45s ago] (50, 0)
2026-07-30 12:55:49,453 INFO sqlalchemy.engine.Engine COMMIT
2026-07-30T12:55:49 | INFO     | sqlalchemy.engine.Engine | COMMIT
INFO:     127.0.0.1:54797 - "GET /api/v1/history HTTP/1.1" 200 OK
2026-07-30 12:55:49,508 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-07-30T12:55:49 | INFO     | sqlalchemy.engine.Engine | BEGIN (implicit)
2026-07-30 12:55:49,509 INFO sqlalchemy.engine.Engine SELECT applications.id, applications.thread_id, applications.resume_id, applications.job_id, applications.company_id, applications.status, applications.match_score, applications.resume_storage_url, applications.tailored_resume_url, applications.cover_letter_url, applications.rejection_feedback, applications.error_message, applications.created_at, applications.updated_at 
FROM applications ORDER BY applications.created_at DESC 
 LIMIT $1::INTEGER OFFSET $2::INTEGER
2026-07-30T12:55:49 | INFO     | sqlalchemy.engine.Engine | SELECT applications.id, applications.thread_id, applications.resume_id, applications.job_id, applications.company_id, applications.status, applications.match_score, applications.resume_storage_url, applications.tailored_resume_url, applications.cover_letter_url, applications.rejection_feedback, applications.error_message, applications.created_at, applications.updated_at 
FROM applications ORDER BY applications.created_at DESC 
 LIMIT $1::INTEGER OFFSET $2::INTEGER
2026-07-30 12:55:49,509 INFO sqlalchemy.engine.Engine [cached since 10.53s ago] (50, 0)
2026-07-30T12:55:49 | INFO     | sqlalchemy.engine.Engine | [cached since 10.53s ago] (50, 0)
2026-07-30 12:55:49,533 INFO sqlalchemy.engine.Engine COMMIT
2026-07-30T12:55:49 | INFO     | sqlalchemy.engine.Engine | COMMIT
INFO:     127.0.0.1:54800 - "GET /api/v1/history HTTP/1.1" 200 OK
2026-07-30 12:55:56,804 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-07-30T12:55:56 | INFO     | sqlalchemy.engine.Engine | BEGIN (implicit)
2026-07-30 12:55:56,805 INFO sqlalchemy.engine.Engine SELECT applications.id, applications.thread_id, applications.resume_id, applications.job_id, applications.company_id, applications.status, applications.match_score, applications.resume_storage_url, applications.tailored_resume_url, applications.cover_letter_url, applications.rejection_feedback, applications.error_message, applications.created_at, applications.updated_at 
FROM applications ORDER BY applications.created_at DESC 
 LIMIT $1::INTEGER OFFSET $2::INTEGER
2026-07-30T12:55:56 | INFO     | sqlalchemy.engine.Engine | SELECT applications.id, applications.thread_id, applications.resume_id, applications.job_id, applications.company_id, applications.status, applications.match_score, applications.resume_storage_url, applications.tailored_resume_url, applications.cover_letter_url, applications.rejection_feedback, applications.error_message, applications.created_at, applications.updated_at 
FROM applications ORDER BY applications.created_at DESC 
 LIMIT $1::INTEGER OFFSET $2::INTEGER
2026-07-30 12:55:56,805 INFO sqlalchemy.engine.Engine [cached since 17.82s ago] (50, 0)
2026-07-30T12:55:56 | INFO     | sqlalchemy.engine.Engine | [cached since 17.82s ago] (50, 0)
2026-07-30 12:55:56,830 INFO sqlalchemy.engine.Engine COMMIT
2026-07-30T12:55:56 | INFO     | sqlalchemy.engine.Engine | COMMIT
INFO:     127.0.0.1:54803 - "GET /api/v1/history HTTP/1.1" 200 OK
2026-07-30 12:55:56,883 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-07-30T12:55:56 | INFO     | sqlalchemy.engine.Engine | BEGIN (implicit)
2026-07-30 12:55:56,883 INFO sqlalchemy.engine.Engine SELECT applications.id, applications.thread_id, applications.resume_id, applications.job_id, applications.company_id, applications.status, applications.match_score, applications.resume_storage_url, applications.tailored_resume_url, applications.cover_letter_url, applications.rejection_feedback, applications.error_message, applications.created_at, applications.updated_at 
FROM applications ORDER BY applications.created_at DESC 
 LIMIT $1::INTEGER OFFSET $2::INTEGER
2026-07-30T12:55:56 | INFO     | sqlalchemy.engine.Engine | SELECT applications.id, applications.thread_id, applications.resume_id, applications.job_id, applications.company_id, applications.status, applications.match_score, applications.resume_storage_url, applications.tailored_resume_url, applications.cover_letter_url, applications.rejection_feedback, applications.error_message, applications.created_at, applications.updated_at 
FROM applications ORDER BY applications.created_at DESC 
 LIMIT $1::INTEGER OFFSET $2::INTEGER
2026-07-30 12:55:56,884 INFO sqlalchemy.engine.Engine [cached since 17.9s ago] (50, 0)
2026-07-30T12:55:56 | INFO     | sqlalchemy.engine.Engine | [cached since 17.9s ago] (50, 0)
2026-07-30 12:55:56,910 INFO sqlalchemy.engine.Engine COMMIT
2026-07-30T12:55:56 | INFO     | sqlalchemy.engine.Engine | COMMIT
INFO:     127.0.0.1:54806 - "GET /api/v1/history HTTP/1.1" 200 OK