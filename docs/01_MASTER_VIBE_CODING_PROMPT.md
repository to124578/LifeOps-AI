# LIFEOPS AI — MASTER VIBE-CODING PROMPT

You are the lead engineer, product designer, AI engineer, QA engineer, and DevOps engineer for a 30-hour hackathon project called **LifeOps AI**.

## 1. Product
Build a functional web application that converts any real-world instruction, notice, bill, email, form, screenshot, or uploaded document into a **verified action plan**.

Core promise:
> “Give LifeOps something confusing that requires action. It tells you what it means, what you must do, what you need, what can go wrong, and what to do next.”

The product must feel like a real product, not a chatbot.

## 2. Primary users
Students, job seekers, employees, freelancers, parents, small-business owners, senior citizens, and anyone dealing with documents/messages/tasks.

## 3. Core differentiator
Do NOT build a generic “AI document summarizer”.

Build an **Actionability Engine** that extracts:
- What action is required
- Who must perform it
- Deadline/date/time
- Priority
- Required documents/information
- Dependencies
- Estimated effort
- Consequences/risk of missing it
- Recommended next steps
- Questions that are still ambiguous
- Confidence level for every important extracted item

The output should become a visual **Action Graph**:
INPUT → UNDERSTAND → REQUIREMENTS → DEPENDENCIES → ACTIONS → DEADLINES → VERIFICATION → DONE

## 4. Signature feature: Deadline Shield
For every detected deadline:
- show exact date/time if available
- distinguish hard deadline vs suggested date vs event date
- show “days remaining”
- detect missing prerequisite tasks
- warn if a prerequisite must happen before the deadline
- allow user to mark it completed
- generate a downloadable .ics calendar event
- never invent a deadline; if uncertain, label it “Needs verification”

## 5. Signature feature: What-if Simulator
Allow the user to ask:
- “What happens if I miss this?”
- “What do I need before I start?”
- “What is the fastest path?”
- “What can I delegate?”
- “What information is missing?”

Answers must be grounded in extracted source content. If the source does not establish an answer, explicitly say that it is unknown and suggest verification.

## 6. Input modes
Implement at least:
1. Paste text
2. Upload PDF
3. Upload image/screenshot
4. Optional plain text file

If time permits:
5. Voice input

For uploaded documents, preserve the original source and show source snippets associated with important extracted facts.

## 7. Agent workflow
Implement a visible multi-stage agent pipeline:

### Agent 1 — Intake Agent
- receives text/file
- extracts raw content
- detects language
- identifies document/message type

### Agent 2 — Understanding Agent
- produces a structured interpretation
- identifies actions, dates, people/roles, requirements, risks

### Agent 3 — Planning Agent
- converts extracted requirements into ordered tasks
- identifies dependencies
- creates a minimum viable completion path

### Agent 4 — Verification Agent
- checks whether claims are supported by the source
- detects contradictions or ambiguity
- assigns confidence
- marks unsupported fields as “Needs verification”

### Agent 5 — Action Agent
- creates checklist items
- creates calendar .ics events
- creates a concise response/draft when appropriate
- prepares an exportable Action Pack

Do not pretend these are autonomous agents if they are merely sequential API calls. Show their actual outputs/status in the UI.

## 8. Action Pack
Generate a portable JSON and human-readable Markdown export containing:
- source title
- source type
- extracted obligations
- deadlines
- tasks
- dependencies
- risks
- unanswered questions
- verification status
- generated calendar events

This is the project’s “built by me” technical artifact: a standardized action representation that another application could consume.

## 9. Safety / trust rules
- Never invent dates, requirements, fees, names, or consequences.
- Every important extracted fact must have a source reference/snippet where possible.
- Use confidence levels: High / Medium / Low.
- For legal, medical, financial, immigration, employment, or government material, clearly label the result as assistance/organization, not professional advice.
- Do not automatically submit forms, send emails, or make payments.
- Require explicit user action for external actions.
- Avoid storing uploaded documents permanently unless the user explicitly chooses to save them.
- Add a “Delete session data” control.

## 10. Recommended stack
Frontend:
- React + Vite
- Tailwind CSS
- React Router
- Lucide icons

Backend:
- Python FastAPI
- Pydantic
- SQLite
- SQLAlchemy

Document processing:
- pypdf for PDF text
- python-docx for DOCX if needed
- OCR through the selected multimodal/vision model for images
- Keep extraction provider behind a simple service interface

AI:
- Provider abstraction supporting Gemini/OpenAI-compatible APIs.
- Structured JSON output using Pydantic schemas.
- Keep API keys only on the backend.

Calendar:
- Generate standard .ics files locally.

Deployment:
- Frontend: Vercel/Netlify
- Backend: Render/Railway/Fly.io or equivalent
- SQLite for demo; clearly state that production would use PostgreSQL.

## 11. UI
Create a polished, responsive dashboard.

Pages:
1. Landing
2. Workspace / Analyze
3. Analysis Results
4. Action Graph
5. Tasks
6. Calendar
7. Action Pack / Export
8. Settings / Privacy

Landing hero:
“Turn confusing information into clear action.”

Primary CTA:
“Analyze something”

Analysis page:
- large upload/drop area
- paste text tab
- sample/demo buttons
- recent analyses

Results page:
- source summary
- urgency banner
- action cards
- deadline cards
- requirements
- dependency graph
- risks
- confidence
- source evidence
- “What-if” input

## 12. Demo scenarios
Create 3 safe demo documents:
A. Internship offer email: sign and return within 24 hours.
B. University notice: payment deadline + required steps.
C. Small-business compliance/renewal notice: deadline + documents required.

The app must produce visibly different action plans for each.

## 13. API endpoints
Implement:
POST /api/analyze
POST /api/analyze/text
GET /api/analysis/{id}
GET /api/analysis/{id}/tasks
POST /api/tasks/{id}/complete
GET /api/analysis/{id}/calendar.ics
GET /api/analysis/{id}/export/json
GET /api/analysis/{id}/export/markdown
DELETE /api/session/{id}
GET /api/health

## 14. Data model
Analysis:
id, title, source_type, raw_text, created_at, language, status

Action:
id, analysis_id, title, description, priority, status, due_at, confidence, evidence

Requirement:
id, analysis_id, item, required, status, confidence, evidence

Dependency:
id, analysis_id, from_action_id, to_action_id, reason

Risk:
id, analysis_id, description, severity, confidence, evidence

Question:
id, analysis_id, question, reason

## 15. AI output contract
Force the model to return valid JSON matching a Pydantic schema. Do not parse free-form markdown for the core workflow.

Minimum schema:
{
  "title": "...",
  "document_type": "...",
  "summary": "...",
  "actions": [],
  "deadlines": [],
  "requirements": [],
  "dependencies": [],
  "risks": [],
  "questions": [],
  "confidence": "high|medium|low",
  "verification_notes": []
}

Every deadline/action/risk should contain an evidence field whenever source text exists.

## 16. Error handling
The application must:
- show friendly API errors
- handle invalid files
- handle empty input
- handle model timeout
- handle malformed AI JSON with retry + repair
- never expose API keys
- show loading progress by pipeline stage

## 17. 30-hour priority rule
Build in this order:
P0: text input → AI extraction → action plan → results UI
P0: PDF/image input
P0: deadlines + task checklist
P0: evidence/confidence
P1: Action Graph
P1: .ics export
P1: Action Pack
P1: what-if simulator
P2: voice
P2: accounts/cloud persistence
P2: advanced integrations

If a feature threatens the working demo, cut it.

## 18. Definition of Done
A judge can:
1. Open the app.
2. Upload/paste a realistic document.
3. See the agent pipeline execute.
4. Receive a structured action plan.
5. See deadlines and dependencies.
6. Inspect evidence/confidence.
7. Ask a what-if question.
8. Complete a task.
9. Download a calendar event.
10. Export an Action Pack.

No fake buttons. Every visible primary feature must work.

## 19. Coding rules
- Write production-quality but hackathon-speed code.
- Small modules, clear names, no giant files.
- TypeScript types on frontend.
- Pydantic schemas on backend.
- Environment variables for secrets.
- Include .env.example.
- Include README with setup and demo instructions.
- Include seed/demo data.
- Add basic tests for core extraction schema and calendar generation.
- Never hard-code API keys.
- Never claim an unavailable integration works.

## 20. Build behavior
Start by inspecting the repository.
Then create the project structure.
Then implement P0 completely.
Run the app after each major milestone.
Fix runtime errors before adding features.
At the end, provide:
- exact run commands
- environment variables
- test commands
- demo script
- known limitations
- next-step production roadmap.

Do not ask unnecessary questions. Make sensible engineering decisions and keep moving.
