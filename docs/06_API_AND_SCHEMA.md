# LifeOps AI — API & Schema Checklist

## Endpoints
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

## AI rules
- JSON only for core extraction
- Pydantic validation
- retry malformed output once
- evidence for extracted claims
- confidence for uncertain claims
- never invent missing facts

## Acceptance tests
1. Empty input returns 400.
2. Unsupported file type returns 415.
3. Valid text creates an analysis.
4. At least one action can be stored.
5. Deadline is preserved correctly.
6. Task completion persists.
7. Calendar file is valid .ics.
8. Export JSON is valid.
9. Delete session removes its data.
10. Missing API key produces a clear setup error, not a stack trace.
