# SOCIALSPACE — COMPLETE STEP BY STEP GUIDE
# Read this once from top to bottom before touching anything.
# Last updated: April 3, 2026
#
# This guide assumes:
# - You are on the Claude free plan
# - You are on Windows
# - You are using PowerShell
# - You have git installed (if not: https://git-scm.com/download/win)

---

## WHAT YOU HAVE — 8 FILES EXPLAINED

| File | What it is | Where it lives |
|---|---|---|
| HOW_TO_USE_EVERYTHING.md | This guide | docs\ |
| SOCIALSPACE_CONTINUITY_SYSTEM_FINAL.md | Full system reference | docs\ |
| SOCIALSPACE_BRUTAL_REALITY_CHECK.md | Honest project audit | docs\ |
| HANDOFF_CURRENT.md | Full 18-section project state | docs\ |
| HANDOFF_QUICK.md | 40-line version for new chats | docs\ |
| run_verify.ps1 | Runs health checks, saves output | docs\ |
| update_handoff.ps1 | Reads clipboard, updates handoff | docs\ |
| create_gitignore.ps1 | Creates .gitignore safely | docs\ |

---

---
# PART A — ONE-TIME SETUP
# Do this once. Takes about 10 minutes.
# Never repeat it unless starting a completely fresh machine.
---

## A1. Create the docs folder

Open File Explorer. Go to:
```
C:\Users\dheer\Downloads\socialspace-workspace\socialspace
```

Right-click inside the folder. New > Folder. Name it `docs`.

---

## A2. Save all 8 files into the docs folder

Move or copy all 8 downloaded files into:
```
C:\Users\dheer\Downloads\socialspace-workspace\socialspace\docs\
```

Your folder should now look like this:
```
socialspace\
  docs\
    HOW_TO_USE_EVERYTHING.md
    SOCIALSPACE_CONTINUITY_SYSTEM_FINAL.md
    SOCIALSPACE_BRUTAL_REALITY_CHECK.md
    HANDOFF_CURRENT.md
    HANDOFF_QUICK.md
    run_verify.ps1
    update_handoff.ps1
    create_gitignore.ps1
  backend\
  frontend\
  venv\
```

---

## A3. Unlock PowerShell scripts — CRITICAL, do this before anything else

Windows blocks .ps1 scripts by default.
If you skip this, every script will refuse to run with a red error.

Do this ONCE:

1. Press the Windows key
2. Type: PowerShell
3. RIGHT-CLICK on "Windows PowerShell"
4. Click "Run as administrator"
5. Click Yes on the security popup

In the admin PowerShell window, type this exactly and press Enter:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

When it asks "Do you want to change the execution policy?" — type Y and press Enter.

Close the admin PowerShell window. Never need to do this again.

---

## A4. Open a normal PowerShell window for the rest of setup

Press Windows key. Type PowerShell. Click the normal one (not admin).

Navigate to your repo root by pasting this and pressing Enter:
```powershell
cd C:\Users\dheer\Downloads\socialspace-workspace\socialspace
```

You should see the path change to end in `\socialspace`.
Keep this PowerShell window open for all the steps below.

---

## A5. Create the .gitignore

In your PowerShell window run:
```powershell
.\docs\create_gitignore.ps1
```

You will see: ".gitignore created at: ..."

This creates the file that stops git from trying to commit node_modules
and venv (which contain 100,000+ files and would hang git forever).

---

## A6. Make your first git commit — creates your safety net

Run these commands one at a time in PowerShell:
```powershell
git add .gitignore
git commit -m "add gitignore"
git add -A
git commit -m "initial project snapshot"
```

If git asks for your name and email for the first time:
```powershell
git config --global user.email "youremail@example.com"
git config --global user.name "Dheeraj"
```
Then run the two commit commands again.

You now have a recovery point. Nothing can be permanently lost from here.

---

## A7. Run the verification script

In PowerShell:
```powershell
.\docs\run_verify.ps1
```

This takes 1-3 minutes. It runs your backend tests, tries the frontend build,
checks git, and lists your real files. It saves everything to:
```
socialspace\docs\VERIFICATION_OUTPUT.txt
```

When it finishes it will say something like:
```
Done. Saved to: ...VERIFICATION_OUTPUT.txt
Size: 52 KB
Safe to paste the entire file into Claude.
```

If size is over 200KB it will tell you which sections to paste first.

---

## A8. Fill in the HANDOFF_CURRENT.md UNVERIFIED tags
## FREE PLAN WARNING: Split this into TWO separate chat messages, not one.

The HANDOFF_CURRENT.md has UNVERIFIED tags wherever real data is needed.
The verification output has the real data. You need Claude to merge them.
But on the free plan, pasting both at once will overload the context window.

Do it in two messages instead:

### Message 1 — paste the handoff first:

Open claude.ai. Start a NEW chat (not the old SocialSpace Agent one).

Paste this:
```
Read this project handoff document. It has UNVERIFIED tags.
Do not respond yet. Just confirm you have read it by saying READY.

[paste entire HANDOFF_CURRENT.md content here]
```

Wait for Claude to say READY.

### Message 2 — paste the verification output second:

```
Now here is the real verification output from running my scripts.
Replace every UNVERIFIED tag in the handoff you just read with
the real data from this output.

Output only the sections that had UNVERIFIED tags.
Use this EXACT format for each section:

--- SECTION N UPDATED ---
[full updated content of that section]
--- END SECTION N ---

Then output:

--- HANDOFF_QUICK UPDATED ---
[updated 40-line version]
--- END HANDOFF_QUICK ---

[paste entire VERIFICATION_OUTPUT.txt content here]
```

### If Claude's response gets cut off mid-output:

This happens on the free plan. Fix it by saying:
```
Your response was cut off after Section N.
Continue from Section N+1. Use the same format.
```

Keep saying this until all sections are output.
Then copy ALL of Claude's responses together (scroll up and get everything).

---

## A9. Run update_handoff.ps1 to save Claude's output

1. Select ALL of Claude's output from the chat (scroll to top, Ctrl+A or manually select)
2. Press Ctrl+C to copy
3. In PowerShell run:
```powershell
.\docs\update_handoff.ps1
```

The script reads from your clipboard and automatically:
- Creates a backup at HANDOFF_BACKUP.md first
- Replaces each UNVERIFIED section with the real data
- Updates HANDOFF_QUICK.md
- Reports what it changed

If it says "Clipboard is empty" — see Emergency section below.

---

## A10. Commit the verified handoff to git

```powershell
git add docs\HANDOFF_CURRENT.md docs\HANDOFF_QUICK.md
git commit -m "handoff: initial verified snapshot"
```

---

## A11. Delete create_gitignore.ps1 — it has done its job

```powershell
Remove-Item docs\create_gitignore.ps1
```

---

# SETUP IS COMPLETE.
# The old SocialSpace Agent chat is permanently retired.
# Every future session uses a fresh chat with HANDOFF_QUICK.md.

---

---
# PART B — EVERY WORKING SESSION
# This is your daily workflow from now on.
---

## B1. Starting a session

**Open a BRAND NEW Claude chat.**
Go to claude.ai. Click the pencil/new chat icon. Never reuse an old slow chat.

**Paste HANDOFF_QUICK.md as your opener.**

Open `socialspace\docs\HANDOFF_QUICK.md` in Notepad.
Select all text (Ctrl+A). Copy (Ctrl+C).

Paste it into the new chat using this wrapper:

```
Read this before doing anything else. Do not write code yet.

I am continuing SocialSpace development.
Below is my project quick handoff — use this as your full context.
Do not rely on any memory from previous conversations.

[PASTE HANDOFF_QUICK.md CONTENT HERE]

Before we start, answer these 3 questions:
1. What is the current status of the frontend build?
2. What is the next task?
3. What is the single most dangerous unresolved issue?

Do not proceed until you have answered all 3.
Only then I will tell you today's task.
```

**Wait for Claude to answer the 3 questions.**

Check the answers against your HANDOFF_QUICK.md.
If any answer is wrong, say: "That answer is wrong — re-read the handoff."
Do not start working until all 3 are correct.

**Tell Claude the one task for today.**

One specific thing only. Not "fix everything." One file, one feature, one bug.

---

## B2. During a session — rules

ONE FILE AT A TIME.
Never say "fix all the TypeScript errors." Say "fix only AnalyticsPage.tsx."

PASTE ONLY THE BROKEN PART.
If a file is 300 lines and the bug is on line 47, paste lines 30-70.
Not the whole file. The whole file eats context and causes lag.

IF CLAUDE STARTS GOING SLOW OR GIVING WEIRD ANSWERS:
Stop immediately. Do not push through.
Copy the last fix Claude gave you.
Open a NEW chat.
Paste HANDOFF_QUICK.md again.
Tell Claude what you were doing and paste the code you need to continue.
This takes 2 minutes and saves 20 minutes of frustration.

IF CLAUDE SAYS SOMETHING THAT CONTRADICTS HANDOFF_QUICK.MD:
Trust the handoff. Say: "That contradicts my handoff which says X. 
The handoff is the source of truth. Proceed based on the handoff."

IF CLAUDE'S RESPONSE GETS CUT OFF:
Say: "Your response was cut off. Continue from where you stopped."
Do not start a new chat mid-task unless Claude becomes genuinely broken.

---

## B3. Ending a session — exact steps every time

**Step 1: Paste the session end template into the chat**

Copy and paste this exactly:

```
Session is ending. Check what changed today and output only the sections
that actually changed. Skip any section that did not change.

Use this EXACT format for each changed section:

--- SECTION N UPDATED ---
[full content of the updated section]
--- END SECTION N ---

Sections to check:
- Section 3: did git status change?
- Section 4: did any system status change?
- Section 6: were new bugs found or existing ones fixed?
- Section 10: ALWAYS replace with today's exact session record
- Section 11: what is the next task now?
- Section 14: did anything move from mock to real?
- Section 16: add one line for today's session
- Section 17: any new warnings?

Then output this regardless of whether anything else changed:

--- HANDOFF_QUICK UPDATED ---
[fresh 40-line compressed version reflecting today's current state]
--- END HANDOFF_QUICK ---
```

Wait for Claude to finish. If it gets cut off, say "continue" until done.

**Step 2: Copy ALL of Claude's response**

Scroll to the top of Claude's session end response.
Select everything from the first `--- SECTION` to the last `--- END HANDOFF_QUICK ---`.
Ctrl+C.

**Step 3: Run the update script**

In PowerShell:
```powershell
cd C:\Users\dheer\Downloads\socialspace-workspace\socialspace
.\docs\update_handoff.ps1
```

Watch the output. It should say something like:
```
Read 87 lines from clipboard.
Backup saved: HANDOFF_BACKUP.md
Sections updated: 6, 10, 11, 16
HANDOFF_QUICK.md updated.
```

If it says a section was NOT found, that section's header may have changed.
Open HANDOFF_CURRENT.md in VS Code, find the section manually, paste the update.

**Step 4: Commit to git**

```powershell
git add docs\HANDOFF_CURRENT.md docs\HANDOFF_QUICK.md
git commit -m "handoff: [today's date] session update"
```

**Step 5: Close the chat.**

Total time for steps 1-5: 3-5 minutes.
This is what keeps the project alive across sessions.
Never skip it.

---

---
# PART C — WEEKLY MAINTENANCE
# Once a week or after any big milestone.
---

```powershell
cd C:\Users\dheer\Downloads\socialspace-workspace\socialspace
.\docs\run_verify.ps1
git add -A
git commit -m "checkpoint: [describe what you built]"
```

This saves a full snapshot of all code. If anything goes badly wrong you can
restore to this exact state. Think of it like a game save point.

---

---
# PART D — EMERGENCY PROCEDURES
---

## Emergency 1 — Chat crashed or got too slow mid-session

1. Open a new chat
2. Paste HANDOFF_QUICK.md with the opener template
3. Say: "My last chat crashed. I was in the middle of [describe task].
   Here is the code I was working on: [paste the relevant section]
   What is the current state and how do I continue?"
4. Continue from where you left off

## Emergency 2 — HANDOFF_CURRENT.md got corrupted or overwritten

The update script saves a backup automatically before every run.
Restore it:
```powershell
cd C:\Users\dheer\Downloads\socialspace-workspace\socialspace
Copy-Item docs\HANDOFF_BACKUP.md docs\HANDOFF_CURRENT.md -Force
```

If HANDOFF_BACKUP.md is also bad, restore from git:
```powershell
git checkout docs\HANDOFF_CURRENT.md
```

## Emergency 3 — update_handoff.ps1 says clipboard is empty

Your system has clipboard access issues. Manual workaround:
1. Paste Claude's session end output into a new file:
   `socialspace\docs\SESSION_END_OUTPUT.txt`
2. Open `update_handoff.ps1` in Notepad
3. Find this line near the top:
   `try { $claudeOutput = (Get-Clipboard) -join`
4. Replace the entire clipboard block (lines 32-49) with:
   `$claudeOutput = Get-Content "$root\docs\SESSION_END_OUTPUT.txt" -Raw`
5. Save and run the script

## Emergency 4 — Scripts refuse to run with red error about policy

You skipped Step A3. Open PowerShell as administrator and run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Emergency 5 — git commit hangs and never finishes

.gitignore is missing. Press Ctrl+C to stop the hang. Then:
```powershell
cd C:\Users\dheer\Downloads\socialspace-workspace\socialspace
# Check if .gitignore exists:
Test-Path .gitignore
# If it says False, create it:
.\docs\create_gitignore.ps1
git add .gitignore
git commit -m "add gitignore"
# Now try your original commit again
```

## Emergency 6 — update_handoff.ps1 says sections were NOT FOUND

The section headers in HANDOFF_CURRENT.md no longer match the expected format.
Open HANDOFF_CURRENT.md in VS Code (or Notepad).
Find the section Claude updated.
Manually replace the old content with Claude's new content.
Save the file. Then commit.

## Emergency 7 — Lost everything, no git history, files deleted

Open a fresh Claude chat and paste this:

```
I need to rebuild my SocialSpace project handoff document from scratch.
Here is my honest project audit:

[paste SOCIALSPACE_BRUTAL_REALITY_CHECK.md]

Generate a new HANDOFF_CURRENT.md using an 18-section format covering:
project identity, environment, git status, system status, file structure,
bugs, architectural conflicts, locked decisions, platform status table,
last session record, next task, things never to do, frontend page status,
demo mode tracker, dependency warnings, session history, warnings for
next Claude, confidence ratings.

Mark anything you cannot verify as UNVERIFIED.
Output in chunks of 80 lines. Say CHUNK N OF N before each.
Wait for me to say NEXT between chunks.
```

---

---
# PART E — QUICK REFERENCE CARD
# Screenshot this section. Keep it visible while working.
---

ONE-TIME SETUP (already done after following Part A):
[x] 8 files saved to socialspace\docs\
[x] PowerShell execution policy unlocked (admin)
[x] create_gitignore.ps1 run
[x] First git commits made
[x] run_verify.ps1 run
[x] HANDOFF_CURRENT.md UNVERIFIED tags filled (2-message method)
[x] update_handoff.ps1 run
[x] Handoff files committed to git

STARTING EVERY SESSION:
[ ] New chat — never reuse old slow one
[ ] Open HANDOFF_QUICK.md in Notepad, copy contents
[ ] Paste into new chat using opener template
[ ] Claude answers 3 questions correctly
[ ] State one specific task only — then work

DURING EVERY SESSION:
[ ] One file at a time
[ ] Paste only the broken section, not full file
[ ] Chat going slow = save work, open new chat, continue
[ ] Claude contradicts handoff = correct Claude, trust handoff

ENDING EVERY SESSION (non-negotiable):
[ ] Paste session end template
[ ] Wait for full output (say "continue" if cut off)
[ ] Select ALL of Claude's session end response, Ctrl+C
[ ] Run: .\docs\update_handoff.ps1
[ ] Run: git add docs\HANDOFF_CURRENT.md docs\HANDOFF_QUICK.md
[ ] Run: git commit -m "handoff: [date] session update"
[ ] Close chat

WEEKLY:
[ ] .\docs\run_verify.ps1
[ ] git add -A && git commit -m "checkpoint: [what you built]"

---

## KEY PATHS — MEMORISE THESE

| What | Full Path |
|---|---|
| Repo root | C:\Users\dheer\Downloads\socialspace-workspace\socialspace |
| Docs folder | ...\socialspace\docs\ |
| Full handoff | ...\docs\HANDOFF_CURRENT.md |
| Quick handoff | ...\docs\HANDOFF_QUICK.md |
| Auto backup | ...\docs\HANDOFF_BACKUP.md |
| Verify output | ...\docs\VERIFICATION_OUTPUT.txt |
| Backend | ...\socialspace\backend\ |
| Frontend | ...\socialspace\frontend\ |
| Run tests | From backend\: ..\venv\Scripts\pytest.exe tests -q |
| Build check | From frontend\: npm run build |

---

*Written April 3, 2026.
This guide covers every realistic failure a solo developer on the free plan hits.
Follow Part A once. Follow Parts B and C every session.
Part D is only for when things go wrong.*
