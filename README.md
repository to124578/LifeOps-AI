# LifeOps AI

Paste or upload a confusing email, notice, bill or screenshot and get back an action plan: what to do, by when, what you need first, and what can go wrong. Every item comes with a quote from the original text, and that quote is checked in code against the source.

Built for WCC Launchpad 30 by Tushar.

## What it does

- Input: pasted text, PDF, image/screenshot, .txt
- Extracts actions, deadlines, requirements, risks and open questions
- Deadline Shield: hard vs suggested vs event dates, days left, what you still need before each deadline
- Action graph: requirements -> dependent tasks -> deadlines -> done
- What-if questions (5 presets + free text). If the document doesn't say, it says so instead of guessing
- Checklist you can tick off, saved in SQLite
- Export: `.ics` calendar file, Action Pack as JSON and Markdown
- "Delete my session data" button

## How the pipeline works

Five steps run one after another and the UI shows each one while it runs:

1. **Intake** - reads the file/text (OCR through the vision model for images and scanned PDFs), guesses language and type
2. **Understanding** - AI call that extracts the structured data, each item with a verbatim quote
3. **Planning** - AI call that orders tasks and finds dependencies (cycles are removed in code; if this step fails it falls back to date/priority ordering)
4. **Verification** - no AI. Every quote is matched against the source text. Quotes that aren't there get "Low confidence / Needs verification", and a "stated in the document" risk with a fake quote is downgraded to an inference
5. **Action** - builds the checklist, calendar events and the Action Pack

## Run it locally

You need Python 3.11+ and Node 20+.

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # then put your GEMINI_API_KEY in it
uvicorn app.main:app --reload --port 8000

# frontend (second terminal)
cd frontend
npm install
npm run dev                                          # http://localhost:5173
```

No API key yet? Set `AI_PROVIDER=mock` in `backend/.env`. The three built-in sample documents work in that mode (the UI shows a demo-mode banner). Your own documents need a real key.

Free Gemini key: https://aistudio.google.com/apikey

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest app/tests
```

Covers the 10 acceptance checks (empty input 400, bad file type 415, analysis created, tasks stored, deadline kept, completion persists, valid .ics, JSON export, session delete, missing-key error), evidence verification, the Gemini code path with a fake HTTP layer (malformed JSON retry, planning fallback), and the what-if grounding.

## Deploy (one service on Render)

The Dockerfile builds the frontend and serves it from FastAPI, so there is one URL.

1. Push this repo to GitHub
2. Render -> New -> Blueprint -> pick the repo (it reads `render.yaml`)
3. Set `GEMINI_API_KEY` in the Render dashboard
4. Open `/api/health` to check it's up

The free tier sleeps after ~15 min idle and takes ~50 s to wake. Open the site a few minutes before you present.

## API

```
POST   /api/analyze                      multipart: file or text
POST   /api/analyze/text                 json: {text}
GET    /api/analysis/{id}                full result (poll while status = processing)
GET    /api/analysis/{id}/tasks
POST   /api/tasks/{id}/complete          {completed: bool}
POST   /api/deadlines/{id}/complete
POST   /api/analysis/{id}/whatif         {preset} or {question}
GET    /api/analysis/{id}/calendar.ics   ?deadline_id= for a single event
GET    /api/analysis/{id}/export/json
GET    /api/analysis/{id}/export/markdown
GET    /api/actionpack/schema            JSON schema of the Action Pack
DELETE /api/session/{id}
GET    /api/health
GET    /api/samples
```

## Project layout

```
backend/app/
  api/routes.py          endpoints
  services/agents/       intake, understanding, planning, verification
  services/              ai_provider, pipeline, verify, calendar, export, whatif, samples
  models/db_models.py    SQLAlchemy tables
  schemas/extraction.py  pydantic models for the AI output
  tests/
frontend/src/
  pages/                 Landing, Analyze, Results, Privacy
  components/            ActionList (+Deadline Shield), ActionGraph, Panels, PipelineProgress
docs/                    original planning docs
```

## Limitations

- Not legal, medical, financial or government advice; the app says so on those documents
- SQLite on a free host is wiped on redeploy. Production would use PostgreSQL and object storage
- No accounts; a random session id in the browser separates users
- OCR can misread text. "Within 24 hours" style deadlines are counted from when you analyzed the document unless you enter a received time
- Calendar events use floating local time (no timezone is assumed)
- Effort estimates and "suggestions" are model guesses and are labelled as such
- Nothing is sent, submitted or paid automatically
- Voice input and cloud accounts are not built

## Credits

**Tushar** - B.Tech CSE, Quantum University
- Product idea and scope: PRD, architecture, 30-hour plan, demo script and judge checklist (see `docs/`)
- Project owner: direction, feature decisions, testing, deployment and presentation

**Implementation support:** the code was written with Claude (Anthropic) as an AI coding assistant, working from Tushar's spec.

**Tools:** FastAPI, SQLAlchemy, pydantic, pypdf, React, Vite, Tailwind CSS, Google Gemini API.
