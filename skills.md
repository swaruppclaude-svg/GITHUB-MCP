# Project Skills & Conventions

## 1. Branch Naming

### Allowed Branch Types

| Type | Purpose |
|---|---|
| `feature/` | New feature development |
| `dev/` | General development or experimental work |
| `bug/` | Bug fixes |
| `release/` | Release preparation |

### Format

```
<type>/<JIRA-NUMBER>-<short-description>
```

### Rules

- JIRA number must come immediately after the slash, before the description
- Short description uses **hyphens only** to separate words
- **No spaces, no underscores, no dots, no special characters** (only `a-z`, `0-9`, `-`)
- Description should be lowercase and concise (3–5 words max)

### Examples

```
feature/KAN-361-github-mcp-server
bug/KAN-204-fix-token-auth
dev/KAN-450-refactor-octokit-client
release/KAN-500-v1-0-0
```

### Invalid Examples

```
feature/KAN_361_github_mcp        ✗  underscores not allowed
feature/KAN-361 github mcp        ✗  spaces not allowed
Feature/KAN-361-Github-MCP        ✗  uppercase not allowed
feature/github-mcp-server         ✗  missing JIRA number
```

---

## 2. Commit Message Format

### Format

```
<JIRA-NUMBER> | <Change done>
```

### Rules

- JIRA number comes first, followed by ` | ` (space-pipe-space)
- Change description starts with a capital letter
- Use present tense, imperative style ("Add", "Fix", "Update", not "Added", "Fixed")
- Keep it under 72 characters total
- No special characters other than the `|` separator

### Examples

```
KAN-361 | Add GitHub MCP server with file read and commit tools
KAN-204 | Fix token authentication error on expired PAT
KAN-450 | Refactor Octokit client into separate module
KAN-500 | Bump version to 1.0.0 for release
```

### Invalid Examples

```
fixed the bug                     ✗  no JIRA number, no pipe
KAN-361: Add server               ✗  colon instead of pipe
KAN-361 | added github server     ✗  past tense, lowercase start
KAN361 | Add server               ✗  missing hyphen in JIRA number
```

---

## 3. Merge Request Description

Every MR must include all four sections below. Do not skip any section.

### Template

```
## What Files Changed
List every file that was added, modified, or deleted and state the type of change.

- `server.py` — Added: main MCP server with GitHub API tools
- `requirements.txt` — Added: project dependencies
- `.gitignore` — Added: excludes .env and __pycache__
- `skills.md` — Added: branch, commit, and MR conventions

---

## What We Are Trying to Accomplish
A clear, non-technical summary of the goal of this MR.

Example:
This MR introduces a Python-based MCP server that allows Claude Code to interact
with GitHub repositories — reading files, creating commits, managing branches,
and opening pull requests — through a set of structured tools.

---

## Impact Analysis
Describe the effect this change has on the system, other teams, or users.

- Does this change break any existing functionality? (Yes / No — explain)
- Does it affect other services or integrations?
- Are there any performance, security, or compatibility considerations?
- Does it require environment variable changes or new secrets?

Example:
- No breaking changes to existing workflows
- Requires GITHUB_TOKEN, GITHUB_OWNER, and GITHUB_REPO in .env
- Token must have repo and read:org scopes

---

## Why Files Changed
Explain the reasoning behind each change — not what changed, but why it was necessary.

- `server.py` — Core deliverable for KAN-361; implements the MCP tool layer over GitHub API
- `requirements.txt` — Dependency manifest needed for reproducible installs
- `.gitignore` — Prevents accidental commit of secrets stored in .env
- `skills.md` — Establishes team conventions so all contributors follow the same standards
```

---

## Quick Reference Card

```
Branch   →  feature/KAN-361-short-description
Commit   →  KAN-361 | Do something specific
MR Body  →  Files Changed | Accomplish | Impact | Why
```
