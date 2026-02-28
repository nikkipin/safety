---
name: capture-skills
description: Session-end skill review. Run at the end of every Claude session to capture learnings as new or updated skills, AGENTS.md entries, or templates. Use when ending a session, wrapping up work, or when the user says "capture skills".
---

# Capture Skills — Session Learning Extraction

## Purpose

Review the current chat session and extract anything worth preserving as reusable knowledge. The goal is to prevent the team from re-learning the same lessons, burning tokens on the same confusion, or re-asking the same clarifying questions.

## When to Run

- **Always** at the end of a session, before the final commit/push (referenced in AGENTS.md session close protocol)
- On demand when the user says `/capture-skills`

## What to Look For

Scan the session for any of these signals:

| Signal | Why It Matters |
|---|---|
| **Confusing patterns** | If Claude or the user was confused, future sessions will be too |
| **Novel solutions** | First-time patterns that worked well should be templated |
| **High token cost** | Long explorations or retries suggest missing guidance |
| **User corrections** | The user had to step in — the skill/docs were insufficient |
| **Repeated clarifications** | Back-and-forth means ambiguity in existing instructions |
| **Workarounds discovered** | Tooling quirks, library gotchas, or env-specific fixes |
| **New architectural decisions** | Choices that affect future work need to be documented |
| **Multi-step recipes** | Complex workflows that could be a slash command or template |

## Decision Tree

For each learning identified, choose the **best** destination:

```
Is this learning specific to an existing skill domain?
├── YES → Update the existing skill's SKILL.md
│         (add a new section, pattern, pitfall, or example)
│
├── PARTIALLY → Update the skill AND add context to AGENTS.md
│               (skill gets the recipe, AGENTS.md gets the rule)
│
└── NO
    ├── Is it a reusable multi-step workflow or template?
    │   └── YES → Create a new skill: .claude/skills/{name}/SKILL.md
    │             (follow the existing YAML frontmatter + markdown body format)
    │
    ├── Is it a one-liner rule or convention?
    │   └── YES → Add to the relevant section of AGENTS.md
    │
    └── Is it a personal preference or env-specific?
        └── YES → Add to ~/.claude/CLAUDE.md or auto-memory MEMORY.md
```

## How to Capture

### Step 1: Summarize Candidates

List each candidate learning in this format:

```
### Learning: {short title}
- **Signal**: {which signal from the table above}
- **Context**: {1-2 sentences on what happened}
- **Destination**: {existing skill | new skill | AGENTS.md | CLAUDE.md | MEMORY.md}
- **Content**: {the actual text/code to add}
```

### Step 2: Ask the User

Present the candidates to the user and ask:
1. "Do any of these seem wrong or not worth capturing?"
2. "Should any of these go to a different destination?"
3. "Is there anything else from this session I should capture?"

Do NOT silently write to skills or AGENTS.md — always get confirmation first.

### Step 3: Apply Changes

For each approved learning:

- **Existing skill update**: Read the current SKILL.md, find the right section, add the new content. Keep the style consistent with what's already there.
- **New skill creation**: Follow this template:

```markdown
---
name: {kebab-case-name}
description: {One sentence. Use when ... triggers.}
---

# {Human Title} for {Project Name}

## {Section 1}
{Content with code examples}

## {Section 2}
{More content}

## Common Pitfalls
{Gotchas specific to this skill}
```

- **AGENTS.md update**: Add to the most relevant existing section. If no section fits, add under "Agent Workflow Learnings".
- **Template extraction**: If the session produced a reusable artifact (migration script, test fixture, API endpoint, etc.), convert it to a generalized template within the skill, replacing specific names with `{placeholders}`.

### Step 4: Verify

- Read back each modified file to confirm the edit landed correctly
- Ensure no duplicate content was introduced
- Confirm the YAML frontmatter is valid (if a skill was created/modified)

## Anti-Patterns

- **Don't capture everything** — only things that would save future sessions real time or confusion
- **Don't duplicate CLAUDE.md** — if it's already in the user's global instructions, don't repeat it in a skill
- **Don't capture session-specific context** — "we fixed bug X" is not a skill; "when you see error Y, the fix is Z" is
- **Don't create skills for one-off tasks** — skills should be reusable across multiple future sessions
- **Don't skip user confirmation** — the user may disagree with your assessment of what's worth capturing
