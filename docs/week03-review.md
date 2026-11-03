# Week 3 — AI Code Review

**Reviewed by:** Claude (Opus 5.5, in Claude Code)  
**Date:** 2026-11-03

## Findings

| # | File:line | What it says is wrong | Is it real? | Action |
|---|---|---|---|---|
| 1 | app.py:75 | `SECRET_KEY` is hardcoded as a fallback (`"development-only-change-me"`), so session cookies could be forged | Yes — line 75 uses it whenever `SECRET_KEY` is not set, and the README never tells you to set it | Leaving for now (deployment is Phase 5) |
| 2 | app.py:484 | `debug=True`; README.md:34 also runs with `--debug` | Yes — both lines are there | Leaving for now (lab only, Phase 5) |
| 3 | app.py:209-212, 237-239, 273-274, 386 | No input length checks on customer name, email, company name, document request title or original uploaded filename | Yes — SQLite does not enforce the declared column lengths | Fixed — commit `9923786` |
| 4 | app.py:301 | Customers can mark their own requests complete or reopen them, but the spec says this route is admin-only | Yes — the original route also allowed the owning customer through | Fixed — commit `aa9bb68` |
| 5 | app.py:220, 225, 404-414 | Newly created customer accounts do not have a proper MFA enrolment process, so they cannot independently configure MFA | Yes — the MFA page only shows the logged-in user's own secret | Leaving for now (the three demo accounts work) |
| 6 | app.py:404-414 | The MFA page shows the secret and current code to anyone with a session | Yes — no password re-check on that page | Leaving for now (demo feature) |
| 7 | app.py:157-188 | No rate limiting on login or MFA attempts | Yes — no attempt counting anywhere | Leaving for now (out of scope for the proof of concept) |
| 8 | app.py:130-131 | Uploads are checked by extension only | Yes — the file contents are never inspected | Leaving for now |

## What I fixed, and why

- **#4 Request status is admin-only** (commit: `aa9bb68`). The specification says only the accountant can complete or reopen a request, but the server originally allowed customers to do it too. Hiding the button is not enough, so I added a server-side permission check to allow administrators only.

- **#3 Input length checks** (commit: `9923786`). Nothing stopped a user from saving excessively long names, email addresses, company names or request titles because SQLite does not enforce the declared column lengths. This could cause database errors when moving to PostgreSQL in Phase 5. The server now rejects inputs that exceed the defined limits. Original uploaded filenames are also checked before files are saved.

The browser tests confirmed that the application rejects:
- Customer names longer than 120 characters.
- Company names longer than 160 characters.
- Document request titles longer than 160 characters.

## What I am knowingly leaving, and why

- **#1 and #2 — Secret key and debug mode.** These are development settings for the local lab project. Before deployment, I will configure a proper secret key and disable debug mode. Deployment and HTTPS are planned for Phase 5.

- **#5, #6 and #7 — MFA enrolment, MFA page security and rate limiting.** MFA works for the three demo accounts, but proper enrolment for newly created customers, protecting the MFA secret after setup, and limiting login attempts remain areas for improvement. These are recorded as known security weaknesses and will be considered in the STRIDE table.

- **#8 — Extension-only upload checks.** Files are restricted by extension and stored under generated filenames. However, their actual contents are not inspected or scanned for malware. This remains a known security limitation of the proof of concept.

## What the reviewer got wrong

- **It missed an obvious problem at first.** Its first review did not mention input length checks. It only identified this issue when I asked about the lab checklist.

- **It assumed a production setting.** Several findings, particularly the secret key and debug mode, were assessed as if the application were already deployed publicly. This is currently a local lab project, although those issues must be addressed before production deployment.
