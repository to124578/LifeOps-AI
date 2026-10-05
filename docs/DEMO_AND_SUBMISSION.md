# Demo and submission notes

## 90 second demo (use the internship offer sample)

1. (10s) "Important actions are buried in emails and notices. People need to know what to do next, not just a summary."
2. (10s) Analyze page -> click **Internship offer email**
3. (15s) Watch the five steps run. Say: "Verification is plain code. It checks every quote against the email."
4. (15s) Action plan tab: show the checklist, priority, owner and the quote chips. Click one chip to jump to the highlighted text in the source.
5. (15s) Deadline Shield: the 24-hour deadline shows what must happen first (NOC, ID, signature). Point at the AI suggestion, it's labelled as not from the source.
6. (10s) What-if -> "What happens if I miss this?" It answers that the email doesn't say, and won't invent a consequence.
7. (10s) Action graph tab, then Export: download the .ics and the JSON Action Pack.
8. (5s) "LifeOps turns information into an execution plan, with evidence and deadlines."

Backup demos: University fee notice (states a late fee, so the what-if answers with a quote), Business licence renewal.

## Before you present

- Open the deployed site 5 minutes early (free tier cold start)
- Run each sample once. Keep a screen recording as a fallback
- Check /api/health shows `ai_configured: true`
- Try one real PDF and one screenshot with your Gemini key, since mock mode can't do those

## Checklist

- [ ] Deployed URL works on phone and laptop
- [ ] Repo public, no `.env` committed (only `.env.example`)
- [ ] README renders
- [ ] Sample documents loaded
- [ ] Backup video recorded
- [ ] Slides: problem, users, why summaries fail, solution, pipeline, demo, architecture, future scope
