# LifeOps AI — Technical Architecture

## High-level
Browser → React/Vite UI → FastAPI → Processing Layer → AI Provider
                                      ↘ SQLite
                                      ↘ File/Text Extraction
                                      ↘ Calendar/Export

## Frontend
- React
- TypeScript
- Tailwind
- React Router
- Fetch/Axios
- React Flow for Action Graph if available

## Backend
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite

## Services
backend/app/
  main.py
  api/
  models/
  schemas/
  services/
    extraction.py
    ai_provider.py
    agents/
      intake.py
      understanding.py
      planning.py
      verification.py
      action.py
    calendar.py
    export.py
  core/
  tests/

## Agent pipeline
raw input
→ intake
→ understanding
→ planning
→ verification
→ action pack

## Security
- API keys server-side
- no secrets in frontend
- temporary files
- delete-session endpoint
- input size limits
- file type validation

## Production upgrade path
SQLite → PostgreSQL
local file processing → object storage
single process → queue/workers
single provider → provider router
anonymous sessions → authenticated accounts
