## Tylmus Backend — Project Instructions



Python 3.11 FastAPI application. Serves daily Connections game data, validates guesses, and tracks user progress via cookies. Uses SQLite for word/category storage.



### Project Structure

```

backend/

├── main.py              # FastAPI app, middleware, endpoints

├── daily\_game.py        # Daily game generator (deterministic by date)

├── database.py          # SQLite connection helpers

├── game\_logic.py        # Core game logic (shuffle, check selection)

├── models.py            # Pydantic/dataclass models (Category)

├── requirements.txt     # Python dependencies

├── Dockerfile           # Container definition

├── .env                 # Environment variables (local)

├── wordsdb.db           # SQLite database (not committed)

└── tests/               # Pytest suite (to be added)

```



### Code Style

- \*\*Python version\*\*: 3.11

- \*\*PEP 8\*\* compliant, 4-space indent, line length ~100 characters.

- `snake\_case` for functions/variables, `UPPER\_SNAKE\_CASE` for constants, `PascalCase` for classes.

- \*\*Type hints\*\* required on all function signatures:  

&nbsp; `def get\_categories\_from\_db(user\_hash: str) -> list\[dict]:`

- Imports grouped: standard library → third-party → local modules, with blank line between groups.

- \*\*Error handling\*\*: Catch specific exceptions (`sqlite3.Error`, `KeyError`). Return `None`/`\[]`/`False` on failure; do not re-raise in route handlers unless propagating to middleware.

- \*\*Async\*\*: Use `async def` for endpoints that perform I/O (already done).



### Logging

- Use custom logging helpers from `main.py`:  

&nbsp; `log\_message(user\_hash: str, message: str)`  

&nbsp; `log\_error(user\_hash: str, message: str, error: Exception = None)`

- Format: `\[YYYY-MM-DD HH:MM:SS TZ] \[USER:hash] message`

- Always include `user\_hash` in logs for traceability.

- For unexpected errors, include traceback: `traceback.print\_exc()` inside `log\_error`.



### Testing

- Run with `pytest` (to be set up). Use `pytest-asyncio` if needed.

- Mock `database.get\_categories` and `get\_words\_by\_category` to avoid real DB.

- Use `TestClient` from FastAPI for endpoint testing.

- Fixtures in `conftest.py` (e.g., `mock\_db`, `client`).

- Naming: `test\_<function>\_<scenario>.py`, test functions `test\_<scenario>`.



### Deployment

- \*\*Docker\*\*: Base image `python:3.11-slim`.

- Copy `requirements.txt`, install dependencies, then copy entire backend.

- Expose port `8000`.

- Run with `CMD \["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]`.

- Ensure proper handling of `SIGTERM` (uvicorn does it by default).

- Use non-root user (optional but recommended).

- Environment variables can be passed via `-e` or an env file.







