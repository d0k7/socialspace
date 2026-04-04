# SOCIALSPACE CONTINUITY SYSTEM — FINAL VERSION
# Read once. Follow forever. Last updated: April 3, 2026
#
# WHAT THIS SYSTEM SOLVES:
# - Chat lag and crashes losing all context
# - Claude drifting from reality after many sessions
# - Manual copy-paste errors corrupting the handoff
# - git commits hanging from node_modules being included
# - Context window getting eaten by a giant opening message

---

## SETUP — DO THIS ONCE RIGHT NOW

### 1. Save these files from your downloads into your repo

```
socialspace\docs\CONTINUITY_SYSTEM.md              ← this file
socialspace\docs\SOCIALSPACE_BRUTAL_REALITY_CHECK.md
socialspace\docs\HANDOFF_CURRENT.md               ← pre-generated, has UNVERIFIED tags
socialspace\docs\HANDOFF_QUICK.md                 ← pre-generated 40-line version
socialspace\docs\run_verify.ps1
socialspace\docs\update_handoff.ps1
socialspace\docs\create_gitignore.ps1
```

### 2. Create the .gitignore (run this once in PowerShell from repo root)

Do NOT try to download and save a .gitignore file directly.
Browsers mangle hidden files. Use the script instead:

```powershell
cd C:\Users\dheer\Downloads\socialspace-workspace\socialspace
.\docs\create_gitignore.ps1
```

This creates `.gitignore` in the correct place and tells you the next commands.

### 3. Make your first safe git commit

```powershell
cd C:\Users\dheer\Downloads\socialspace-workspace\socialspace
git add .gitignore
git commit -m "add gitignore"
git add -A
git commit -m "initial project snapshot"
```

You now have a recovery point. If anything breaks, you can always come back here.

---

---
# STEP 1 — FILL IN THE PRE-GENERATED HANDOFF
# HANDOFF_CURRENT.md and HANDOFF_QUICK.md are already downloaded.
# You do NOT need to go back to the SocialSpace Agent chat.
# This step just replaces UNVERIFIED tags with real data from your machine.
---

### 1a. Save the two handoff files alongside the scripts

```
socialspace\docs\HANDOFF_CURRENT.md   ← pre-generated, has UNVERIFIED tags
socialspace\docs\HANDOFF_QUICK.md     ← pre-generated 40-line version
```

### 1b. Run the verification script to get real data

```powershell
cd C:\Users\dheer\Downloads\socialspace-workspace\socialspace
.\docs\run_verify.ps1
```

This saves real command output to `docs\VERIFICATION_OUTPUT.txt`.

### 1c. Open a fresh Claude chat and paste this:

▼▼▼ START PASTE ▼▼▼

Read everything before responding.

I am setting up my SocialSpace project continuity system.
Below is my current handoff document — it has UNVERIFIED tags wherever
real command output is needed to confirm the truth.

[PASTE ENTIRE HANDOFF_CURRENT.md HERE]

Below is the real verification output from running run_verify.ps1 on my machine.
Use it to fill in every UNVERIFIED tag in the handoff above.

[PASTE ENTIRE VERIFICATION_OUTPUT.txt HERE]

Output ONLY the sections that had UNVERIFIED tags, using this exact format:

--- SECTION N UPDATED ---
[full updated content of that section]
--- END SECTION N ---

Also output:

--- HANDOFF_QUICK UPDATED ---
[updated 40-line version reflecting the verified data]
--- END HANDOFF_QUICK ---

▲▲▲ END PASTE ▲▲▲

### 1d. Run update_handoff.ps1

1. Copy ALL of Claude's output from the chat (Ctrl+A, Ctrl+C)
2. Run:
```powershell
cd C:\Users\dheer\Downloads\socialspace-workspace\socialspace
.\docs\update_handoff.ps1
```

The script reads from clipboard, replaces UNVERIFIED sections automatically,
and saves the updated HANDOFF_QUICK.md. Done.

### 1e. Commit both files

```powershell
git add docs\HANDOFF_CURRENT.md docs\HANDOFF_QUICK.md
git commit -m "handoff: initial verified snapshot"
```

The SocialSpace Agent chat is now retired. Every future session uses a fresh chat
with HANDOFF_QUICK.md as the opener. You never need the old laggy chat again.

---

---
# STEP 1 ARCHIVE — Only needed if starting from scratch with no pre-generated handoff
# Skip this entirely if you have HANDOFF_CURRENT.md already
---

If for any reason you need to regenerate the handoff from scratch (e.g. you lost
HANDOFF_CURRENT.md and have no git backup), open a fresh Claude chat and paste
this prompt with your existing project docs attached:

▼▼▼ REGENERATION PASTE ▼▼▼

I need to regenerate my SocialSpace project handoff document from scratch.
Below are my project context documents. Read all of them, then generate
a HANDOFF_CURRENT.md following the 18-section format from my
CONTINUITY_SYSTEM.md. Mark anything you cannot confirm as UNVERIFIED.

[paste SOCIALSPACE_BRUTAL_REALITY_CHECK.md]
[paste any other project docs you have]

Output in chunks of 80 lines. Wait for me to say NEXT between chunks.

▲▲▲ END REGENERATION PASTE ▲▲▲
Output in NUMBERED CHUNKS of maximum 80 lines each.
Label each chunk: CHUNK 1 OF N, CHUNK 2 OF N, etc.
Wait for me to say NEXT before sending each chunk.

---
# SOCIALSPACE MASTER HANDOFF
**Generated:** [exact date and time IST]
**Source:** SocialSpace Agent chat
**Note:** UNVERIFIED sections must be confirmed by running run_verify.ps1

---

### SECTION 1 — PROJECT IDENTITY
- Product name and codenames:
- What it does RIGHT NOW (not the vision):
- The full vision (autonomous agent goal):
- Exact target user:
- Current development phase:
- Default shell: PowerShell for all commands

---

### SECTION 2 — ENVIRONMENT
- OS:
- Workspace root (full path):
- Repo root (full path):
- Backend dir (full path):
- Frontend dir (full path):
- Venv dir (full path):
- Python version:
- Node version:
- Run backend tests (exact command + directory):
- Start frontend dev (exact command + directory):
- Build frontend (exact command + directory):
- .env files needed (location + required keys):

---

### SECTION 3 — GIT STATUS
- Has commit history: YES or NO
- If YES: last commit hash + message
- If NO: "NO COMMITS — data loss risk on any crash"
- Current branch:
- Untracked files: YES or NO

---

### SECTION 4 — SYSTEM STATUS
For each: WORKING / BROKEN / PARTIAL / NOT STARTED / UNVERIFIED + one specific sentence

- Frontend build (npm run build):
- Frontend dev server:
- Backend test suite (include exact pass/fail numbers):
- Backend running as live API:
- Database (type, exists, tables created):
- Auth (real JWT or demo mode):
- Real OAuth for any platform (which ones):
- Real posting to any platform (which ones):
- Groq API wired in:
- OpenAI API wired in:
- Frontend making real backend calls:
- cli.py exists:

---

### SECTION 5 — ACTUAL FILE STRUCTURE
Real files only. Mark uncertain ones UNVERIFIED.

socialspace/
  backend/
    socialspace_agent/
      [list every subfolder + key files]
    tests/ [count or list]
    requirements.txt: EXISTS / UNVERIFIED
    setup.py: EXISTS / UNVERIFIED
    verify_models.py: EXISTS / UNVERIFIED
  frontend/
    src/
      pages/ [list every .tsx file]
      components/ [list folders + key files]
      contexts/ [list files]
      hooks/ [list files]
      routes/ [list files]
      lib/ [list files]
      App.tsx: EXISTS / UNVERIFIED
      main.tsx: EXISTS / UNVERIFIED
    package.json: EXISTS / UNVERIFIED
    vite.config.ts: EXISTS / UNVERIFIED
    tsconfig.json: EXISTS / UNVERIFIED
  docs/ [list files]
  venv/ EXISTS

---

### SECTION 6 — EVERY KNOWN BUG (one per item, no grouping)
For each:
- File + line number if known
- Exact error or symptom
- Fix attempted: YES/NO + what happened
- Status: OPEN / PARTIALLY FIXED / WORKAROUND APPLIED

---

### SECTION 7 — UNRESOLVED ARCHITECTURAL CONFLICTS
For each: what it is (name specific files) / why unresolved / fix / risk: HIGH/MEDIUM/LOW

Must cover: auth duplication, theme duplication, API client duplication,
composer duplication, layout overlap, platform count 12 vs 13,
WeChat status, config coverage gaps.

---

### SECTION 8 — LOCKED DECISIONS (never revisit)
For each: Decision / Reason / What was rejected / FINAL or REVISABLE

Cover: frontend framework, backend structure, state management,
canonical auth file, canonical theme file, canonical API client,
canonical composer file, database choice, AI provider order,
final platform list, shell convention.

---

### SECTION 9 — PLATFORM STATUS TABLE

| Platform | Adapter Exists | In Config | Real API Tested | Frontend Wired | Notes |
|---|---|---|---|---|---|
| WhatsApp | | | | | |
| Telegram | | | | | |
| Instagram | | | | | |
| Discord | | | | | |
| Reddit | | | | | |
| Twitter/X | | | | | |
| YouTube | | | | | |
| Facebook | | | | | |
| LinkedIn | | | | | |
| TikTok | | | | | |
| Snapchat | | | | | |
| Pinterest | | | | | |
| WeChat | | | | | REMOVE? YES/NO |

---

### SECTION 10 — THIS SESSION RECORD
- Goal:
- Files CREATED (full paths):
- Files MODIFIED (full paths + what changed):
- Files DELETED:
- Completed:
- Failed:
- Left half-done (file + what is incomplete):
- Files currently in broken state:

---

### SECTION 11 — NEXT TASK (specific enough to start immediately)
- Task:
- First file to open:
- First command to run + directory:
- What success looks like:
- How to verify it worked:

---

### SECTION 12 — NEVER DO THESE THINGS
- What not to do + why it broke

---

### SECTION 13 — FRONTEND PAGE STATUS

| Page | File Path | Build Error | Works in Dev | Data: Real/Mock | Notes |
|---|---|---|---|---|---|
| Login | | | | | |
| Register | | | | | |
| Dashboard | | | | | |
| Analytics | | | | | |
| Messages | | | | | |
| Platforms | | | | | |
| Settings | | | | | |
| Composer | | | | | |

---

### SECTION 14 — DEMO MODE TRACKER

| File/Component | What it fakes | Real implementation needed | Priority H/M/L |
|---|---|---|---|

---

### SECTION 15 — DEPENDENCY WARNINGS
- Frontend packages with issues:
- Backend version conflicts:
- Pydantic version + deprecation status:
- Missing from requirements.txt or package.json:

---

### SECTION 16 — SESSION HISTORY
One line per session: Session N — [what was done]

---

### SECTION 17 — WARNINGS FOR NEXT CLAUDE
Each line starts with DO NOT or BE AWARE.

---

### SECTION 18 — CONFIDENCE RATINGS
Rate each section: HIGH / MEDIUM (may have drifted) / LOW (UNVERIFIED)

Single most dangerous unresolved issue: [one sentence]

▲▲▲ END PASTE ▲▲▲

Receive all chunks. Say NEXT after each one. Paste all chunks together in order into Notepad and continue to Step 2.

---

---
# STEP 2 — VERIFY AND FINALIZE THE HANDOFF
---

### 2a. Run the verification script

```powershell
cd C:\Users\dheer\Downloads\socialspace-workspace\socialspace
.\docs\run_verify.ps1
```

Opens `docs\VERIFICATION_OUTPUT.txt` automatically with all real command outputs.

### 2b. Send the verification to Claude

Go back to the chat. Paste this:

"Here is the real output from run_verify.ps1. Replace every UNVERIFIED
section with the real data. Output the updated sections ONLY, one at a time,
using this exact format for each:

--- SECTION N UPDATED ---
[full updated content]
--- END SECTION N ---

Say READY before starting, then output one section per message.
Wait for me to say NEXT between sections."

[paste VERIFICATION_OUTPUT.txt content]

### 2c. Save Claude's updates automatically

1. Copy ALL of Claude's section output into a new file:
   `socialspace\docs\SESSION_END_OUTPUT.txt`

2. Run the update script:
```powershell
cd C:\Users\dheer\Downloads\socialspace-workspace\socialspace
.\docs\update_handoff.ps1
```

This automatically finds and replaces each updated section.
It creates a backup first, so if anything goes wrong just restore `HANDOFF_BACKUP.md`.

### 2d. Build the final verified handoff

Take the chunks from Step 1, paste them all together into:
```
socialspace\docs\HANDOFF_CURRENT.md
```

Then run the update script from 2c to inject the verified data.

### 2e. Commit the handoff to git

```powershell
git add docs\HANDOFF_CURRENT.md
git commit -m "handoff: initial verified snapshot"
```

Now even if the file is overwritten badly, git has the last good version.

---

---
# STEP 3 — CREATE THE QUICK HANDOFF (one-time setup)
# This is what you paste at the start of every chat — NOT the full handoff
# Keeps context window free for actual work
---

After HANDOFF_CURRENT.md is ready, ask Claude this in a new chat:

"Read my full handoff document below. Then generate a HANDOFF_QUICK.md —
a compressed version of maximum 40 lines that contains only:
- Current system status (one word per item)
- Next task (3 lines)
- Top 5 warnings
- 3 most dangerous open bugs
- File locations for key files
- Shell convention reminder

[paste HANDOFF_CURRENT.md]"

Save Claude's output to:
```
socialspace\docs\HANDOFF_QUICK.md
```

Update HANDOFF_QUICK.md at session end alongside HANDOFF_CURRENT.md.

---

---
# STEP 4 — HOW TO START EVERY NEW CHAT
---

▼▼▼ NEW CHAT OPENING — PASTE THIS ▼▼▼

Read everything before writing any code.

I am continuing SocialSpace development. Below is my quick project summary.
Use this as your starting context. Do not rely on any prior memory.

[PASTE HANDOFF_QUICK.md HERE — 40 lines, fast to paste]

Full detailed handoff available at: socialspace\docs\HANDOFF_CURRENT.md
Ask me to paste specific sections if you need more detail on anything.

Before starting, confirm current state by answering these three questions.
Wrong answers = re-read the handoff. Do not proceed until answers are correct.

1. What is the exact current status of the frontend build?
2. What is the next task from the handoff?
3. What is the single most dangerous unresolved issue?

Today's one task only: [YOUR SPECIFIC TASK]

▲▲▲ END NEW CHAT OPENING ▲▲▲

WHY QUICK NOT FULL: The full handoff can be 300+ lines. Pasting it every
time eats your context window on the free plan before you write a line of code.
The quick version is 40 lines. Paste it fast, get to work.
If Claude needs more detail on a specific section, paste just that section.

---

---
# STEP 5 — HOW TO END EVERY SESSION
# Non-negotiable. 5 minutes. Skipping this is how projects die.
---

### 5a. Paste this into the chat before closing:

▼▼▼ SESSION END TEMPLATE ▼▼▼

Session ending. Output only the sections that changed today.
Use this EXACT format — the update script depends on it:

--- SECTION N UPDATED ---
[full updated content of that section]
--- END SECTION N ---

Sections to check (only output ones that actually changed):
- Section 3: git status
- Section 4: any system statuses that changed
- Section 6: new bugs found, fixed bugs marked resolved
- Section 10: replace completely with today's session record
- Section 11: update next task to what comes next now
- Section 14: anything moved from fake to real
- Section 16: add one line for today
- Section 17: any new warnings

Then at the very end output this regardless of whether anything changed:

--- HANDOFF_QUICK UPDATED ---
[compressed 40-line version with: system status, next task, top 5 warnings,
3 most dangerous bugs, key file locations, shell convention]
--- END HANDOFF_QUICK ---

▲▲▲ END SESSION END TEMPLATE ▲▲▲

### 5b. Two steps only — no file creation needed

1. Select all of Claude's output in the chat. Copy it (Ctrl+A, Ctrl+C).

2. Run the update script — it reads from clipboard automatically:
```powershell
cd C:\Users\dheer\Downloads\socialspace-workspace\socialspace
.\docs\update_handoff.ps1
```

The script:
- Reads Claude's output from your clipboard
- Backs up HANDOFF_CURRENT.md automatically before touching it
- Replaces each updated section in place
- Extracts and saves HANDOFF_QUICK.md automatically
- Reports exactly what it updated and what it skipped

### 5c. Commit to git

```powershell
git add docs\HANDOFF_CURRENT.md docs\HANDOFF_QUICK.md
git commit -m "handoff: $(Get-Date -Format 'yyyy-MM-dd') session update"
```

Done. Clipboard cleared. Git has the backup. Close the chat.

RECOVERY: If update_handoff.ps1 corrupts anything, HANDOFF_BACKUP.md
was saved automatically before any changes were made. Restore with:
```powershell
Copy-Item docs\HANDOFF_BACKUP.md docs\HANDOFF_CURRENT.md -Force
```

---

---
# QUICK REFERENCE CARD — SCREENSHOT THIS
---

STARTING A SESSION:
[ ] New chat always
[ ] Paste HANDOFF_QUICK.md in opening template
[ ] Claude answers 3 questions correctly
[ ] One task only

DURING A SESSION:
[ ] One file at a time
[ ] Paste only the broken section, not the full file
[ ] Chat slowing down = save fix, new chat, continue
[ ] Claude contradicts handoff = trust handoff

ENDING A SESSION (every time):
[ ] Paste session end template into chat
[ ] Copy ALL of Claude's output (Ctrl+A Ctrl+C)
[ ] Run: .\docs\update_handoff.ps1   (reads clipboard, updates everything)
[ ] git commit both handoff files
[ ] Close chat

WEEKLY:
[ ] Run run_verify.ps1
[ ] git add -A && git commit -m "checkpoint: [what you built]"

EMERGENCY (chat crashed):
[ ] New chat
[ ] Paste HANDOFF_QUICK.md
[ ] Run run_verify.ps1
[ ] Paste VERIFICATION_OUTPUT.txt
[ ] Ask Claude to assess state before touching anything

---

## ALL FILES AND THEIR ROLES

| File | Location | Updated by |
|---|---|---|
| CONTINUITY_SYSTEM.md | docs/ | Rarely |
| HANDOFF_CURRENT.md | docs/ | update_handoff.ps1 every session |
| HANDOFF_QUICK.md | docs/ | Manual paste, every session, 40 lines |
| HANDOFF_BACKUP.md | docs/ | Auto-created by update_handoff.ps1 |
| SESSION_END_OUTPUT.txt | docs/ | You paste Claude's output here |
| SOCIALSPACE_BRUTAL_REALITY_CHECK.md | docs/ | After major changes |
| run_verify.ps1 | docs/ | Never change |
| update_handoff.ps1 | docs/ | Never change |
| create_gitignore.ps1 | docs/ | Run once then delete |
| VERIFICATION_OUTPUT.txt | docs/ | Auto-generated, gitignored |
| .gitignore | repo root | Set once |

---

*Built April 3, 2026. Designed to keep a solo AI-assisted project alive
indefinitely on the free plan, across unlimited new chats, with zero manual
copy-paste errors and full git backup after every session.*
