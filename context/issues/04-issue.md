ERROR:    Traceback (most recent call last):
  File "/Users/7parth/Developer/Projects/Recon/backend/.venv/lib/python3.11/site-packages/starlette/routing.py", line 638, in lifespan
    async with self.lifespan_context(app) as maybe_state:
  File "/Users/7parth/.local/share/uv/python/cpython-3.11.15-macos-aarch64-none/lib/python3.11/contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/7parth/Developer/Projects/Recon/backend/.venv/lib/python3.11/site-packages/fastapi/routing.py", line 233, in merged_lifespan
    async with original_context(app) as maybe_original_state:
  File "/Users/7parth/.local/share/uv/python/cpython-3.11.15-macos-aarch64-none/lib/python3.11/contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/7parth/Developer/Projects/Recon/backend/.venv/lib/python3.11/site-packages/fastapi/routing.py", line 233, in merged_lifespan
    async with original_context(app) as maybe_original_state:
  File "/Users/7parth/.local/share/uv/python/cpython-3.11.15-macos-aarch64-none/lib/python3.11/contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/7parth/Developer/Projects/Recon/backend/.venv/lib/python3.11/site-packages/fastapi/routing.py", line 233, in merged_lifespan
    async with original_context(app) as maybe_original_state:
  File "/Users/7parth/.local/share/uv/python/cpython-3.11.15-macos-aarch64-none/lib/python3.11/contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/7parth/Developer/Projects/Recon/backend/.venv/lib/python3.11/site-packages/fastapi/routing.py", line 233, in merged_lifespan
    async with original_context(app) as maybe_original_state:
  File "/Users/7parth/.local/share/uv/python/cpython-3.11.15-macos-aarch64-none/lib/python3.11/contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/7parth/Developer/Projects/Recon/backend/.venv/lib/python3.11/site-packages/fastapi/routing.py", line 233, in merged_lifespan
    async with original_context(app) as maybe_original_state:
  File "/Users/7parth/.local/share/uv/python/cpython-3.11.15-macos-aarch64-none/lib/python3.11/contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/7parth/Developer/Projects/Recon/backend/app/main.py", line 55, in lifespan
    async with get_checkpointer() as checkpointer:
  File "/Users/7parth/.local/share/uv/python/cpython-3.11.15-macos-aarch64-none/lib/python3.11/contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/7parth/Developer/Projects/Recon/backend/app/services/checkpoint_service.py", line 56, in get_checkpointer
    await checkpointer.setup()
  File "/Users/7parth/Developer/Projects/Recon/backend/.venv/lib/python3.11/site-packages/langgraph/checkpoint/postgres/aio.py", line 97, in setup
    async with self._cursor() as cur:
  File "/Users/7parth/.local/share/uv/python/cpython-3.11.15-macos-aarch64-none/lib/python3.11/contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/7parth/Developer/Projects/Recon/backend/.venv/lib/python3.11/site-packages/langgraph/checkpoint/postgres/aio.py", line 374, in _cursor
    async with self.lock, _ainternal.get_connection(self.conn) as conn:
  File "/Users/7parth/.local/share/uv/python/cpython-3.11.15-macos-aarch64-none/lib/python3.11/contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/7parth/Developer/Projects/Recon/backend/.venv/lib/python3.11/site-packages/langgraph/checkpoint/postgres/_ainternal.py", line 20, in get_connection
    async with conn.connection() as conn:
  File "/Users/7parth/.local/share/uv/python/cpython-3.11.15-macos-aarch64-none/lib/python3.11/contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/7parth/Developer/Projects/Recon/backend/.venv/lib/python3.11/site-packages/psycopg_pool/pool_async.py", line 220, in connection
    conn = await self.getconn(timeout=timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/7parth/Developer/Projects/Recon/backend/.venv/lib/python3.11/site-packages/psycopg_pool/pool_async.py", line 255, in getconn
    raise PoolTimeout(
psycopg_pool.PoolTimeout: couldn't get a connection after 30.00 sec

ERROR:    Application startup failed. Exiting.
2026-07-25T13:48:53 | WARNING  | psycopg.pool | error connecting in 'pool-1': 
2026-07-25T13:48:53 | WARNING  | psycopg.pool | error connecting in 'pool-1': 
2026-07-25T13:48:53 | WARNING  | psycopg.pool | error connecting in 'pool-1':