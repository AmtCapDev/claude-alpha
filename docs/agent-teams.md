# Agent Teams — Master Reference Guide

Source: https://code.claude.com/docs/en/agent-teams (fetched 2026-04-23)

Purpose: this is the reference I (Claude) consult when building or coordinating agent teams in this project. It captures what works, what doesn't, and the concrete mechanics behind the feature so I can make good decisions under time pressure.

---

## 1. What an agent team is (and isn't)

An agent team is **multiple Claude Code instances running in parallel**, coordinating through a shared task list and a messaging mailbox. One session is the **lead** (the session that creates the team). The rest are **teammates** — independent Claude Code sessions, each with its own context window, that can message each other directly.

Key distinction from subagents:

|                   | Subagents                                        | Agent teams                                         |
| :---------------- | :----------------------------------------------- | :-------------------------------------------------- |
| **Context**       | Own context window; result returns to caller    | Own context window; fully independent               |
| **Communication** | Report back to the main agent only              | Teammates message each other directly               |
| **Coordination**  | Main agent manages all work                     | Shared task list with self-coordination             |
| **Best for**      | Focused tasks where only the result matters     | Work requiring discussion and collaboration         |
| **Token cost**    | Lower (results summarized)                      | Higher (each teammate is a full Claude instance)    |

**Requirements:** Claude Code v2.1.32+. Check with `claude --version`.

**Status:** Experimental, off by default. Known gaps in session resumption, task status reliability, and shutdown.

---

## 2. Decision matrix: team, subagents, or single session?

### Use an agent team when
- Work genuinely parallelizes into independent streams
- Teammates need to **challenge each other** (competing hypotheses, adversarial review)
- Parallel exploration adds signal (multiple lenses on the same problem)
- Cross-layer changes where frontend / backend / tests are each self-contained
- New modules or features where each teammate owns a distinct file set

### Use subagents when
- Work parallelizes but workers don't need to talk to each other
- You only care about the synthesized result, not the process
- Token budget is a concern

### Stay in a single session when
- Tasks are sequential or share state heavily
- Multiple workers would edit the same files
- The task is routine — coordination overhead would dwarf the gain

**Rule of thumb:** "Would these workers need to compare notes to do the job right?" Yes → team. No → subagents or one session.

---

## 3. Enabling the feature

Set the env var to `1`, either in the shell or in `settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

Already done in this project in [.claude/settings.local.json](../.claude/settings.local.json). Takes effect on the **next** Claude Code session (restart required).

---

## 4. Starting a team

Ask Claude in natural language. Describe the task *and* the team structure. Claude creates the team, spawns teammates, and coordinates.

**Example prompts that work (verbatim from docs):**

Exploratory / multi-perspective:
```text
I'm designing a CLI tool that helps developers track TODO comments across
their codebase. Create an agent team to explore this from different angles: one
teammate on UX, one on technical architecture, one playing devil's advocate.
```

Size and model control:
```text
Create a team with 4 teammates to refactor these modules in parallel.
Use Sonnet for each teammate.
```

Plan-gated work:
```text
Spawn an architect teammate to refactor the authentication module.
Require plan approval before they make any changes.
```

Adversarial debugging:
```text
Users report the app exits after one message instead of staying connected.
Spawn 5 agent teammates to investigate different hypotheses. Have them talk to
each other to try to disprove each other's theories, like a scientific
debate. Update the findings doc with whatever consensus emerges.
```

Parallel PR review:
```text
Create an agent team to review PR #142. Spawn three reviewers:
- One focused on security implications
- One checking performance impact
- One validating test coverage
Have them each review and report findings.
```

Spawn with a spawn-prompt containing all task context the teammate needs:
```text
Spawn a security reviewer teammate with the prompt: "Review the authentication module
at src/auth/ for security vulnerabilities. Focus on token handling, session
management, and input validation. The app uses JWT tokens stored in
httpOnly cookies. Report any issues with severity ratings."
```

**Two ways a team gets created:**
1. You ask for one explicitly.
2. Claude proposes one if the task benefits from parallel work — user confirms before it proceeds.

---

## 5. Architecture

| Component     | Role                                                                        |
| :------------ | :-------------------------------------------------------------------------- |
| **Team lead** | Main session — creates the team, spawns teammates, coordinates work         |
| **Teammates** | Independent Claude Code instances, each working on assigned tasks           |
| **Task list** | Shared list of work items; teammates claim and complete them                |
| **Mailbox**   | Messaging system — direct teammate-to-teammate communication                |

**Local storage:**
- Team config: `~/.claude/teams/{team-name}/config.json` (contains `members` array — name, agent ID, agent type; teammates can read this to discover peers)
- Task list: `~/.claude/tasks/{team-name}/`

**Do not hand-edit** these files — they hold runtime state (session IDs, tmux pane IDs) and are rewritten on every state update. There is **no project-level config**; a file like `.claude/teams/teams.json` is ignored.

**Tool surface (team-coordination tools always available to teammates, even with restricted `tools` allowlists):**
- `TeamCreate` / `TeamDelete` — lifecycle
- `SendMessage` — direct teammate messaging by name
- Task management tools — create / claim / update / complete tasks

---

## 6. Controlling teammates

### Display modes
- **In-process** (default in plain terminals) — all teammates run inside the main terminal; `Shift+Down` cycles through them, type to message; `Enter` to view a session, `Escape` to interrupt; `Ctrl+T` toggles the task list.
- **Split panes** — one pane per teammate; click to interact. Requires **tmux** or **iTerm2 + `it2` CLI**. Not supported in VS Code integrated terminal, Windows Terminal, or Ghostty.

Default `"auto"` → split panes if already inside tmux, otherwise in-process. Override globally in `~/.claude.json`:

```json
{ "teammateMode": "in-process" }
```

Per-session override:
```bash
claude --teammate-mode in-process
```

### Assign and claim tasks
Three states: **pending → in progress → completed**. Tasks can depend on other tasks; a pending task with unresolved dependencies can't be claimed. Task claiming uses **file locking** to prevent races.

- **Lead assigns**: tell the lead which task goes to which teammate
- **Self-claim**: after finishing, a teammate picks the next unassigned, unblocked task

### Plan approval for teammates
Teammate works in read-only plan mode until the lead approves. On rejection, teammate stays in plan mode and revises. Influence the lead's judgment via criteria in the spawn prompt, e.g., "only approve plans that include test coverage."

### Shutdown
```text
Ask the researcher teammate to shut down
```
Lead sends a shutdown request; teammate can approve (graceful exit) or reject with explanation.

### Cleanup (always via the lead, never a teammate)
```text
Clean up the team
```
Fails if any teammate is still running — shut them down first.

### Direct teammate messaging
Every teammate gets a lead-assigned name on spawn. Any teammate can message any other by name. To reach everyone, send N messages. **For predictable names, tell the lead what to call each teammate at spawn time.**

---

## 7. Subagent definitions as teammate roles

Reference a subagent definition (project / user / plugin / CLI scope) when spawning:

```text
Spawn a teammate using the security-reviewer agent type to audit the auth module.
```

The teammate honors the subagent definition's `tools` allowlist and `model`. The definition's body is **appended** to the teammate's system prompt (not a replacement).

**Caveat:** `skills` and `mcpServers` frontmatter fields in the subagent definition are **not applied** when running as a teammate. Skills and MCP servers are loaded from project/user settings instead.

Team-coordination tools (`SendMessage`, task tools) remain available regardless of `tools` restrictions.

---

## 8. Context, permissions, and tokens

### Context inherited by a teammate on spawn
- CLAUDE.md from its working directory (use it for project-wide teammate guidance)
- MCP servers from project/user settings
- Skills from project/user settings
- Spawn prompt from the lead

**Not inherited:** the lead's conversation history. Put everything the teammate needs into the spawn prompt.

### Communication primitives
- **Automatic delivery**: messages arrive at recipients without polling
- **Idle notifications**: teammate finishing → lead notified
- **Shared task list**: all agents see statuses and can claim work
- **Named messaging**: one-to-one by name; no broadcast

### Permissions
Teammates inherit the lead's permission mode at spawn. `--dangerously-skip-permissions` on the lead → same on all teammates. You can change an individual teammate's mode **after** spawn, but **not at spawn time per-teammate**.

Teammate permission prompts **bubble up to the lead** — pre-approve common operations in permission settings to reduce interruption.

### Tokens
Token usage scales roughly linearly with teammate count (each has its own context). Worth it for research / review / new features; overkill for routine work. Start with **3–5 teammates**; **5–6 tasks per teammate** is the docs' sweet spot.

---

## 9. Quality gates via hooks

| Hook            | Fires when                                    | Block behavior (exit code 2)                      |
| :-------------- | :-------------------------------------------- | :------------------------------------------------ |
| `TeammateIdle`  | A teammate is about to go idle                | Send feedback and keep them working               |
| `TaskCreated`   | A task is being created                       | Prevent creation; send feedback                   |
| `TaskCompleted` | A task is being marked complete               | Prevent completion; send feedback                 |

Configure in `settings.json` under `hooks` (same structure as other hook events).

---

## 10. Best practices (condensed)

- **Start with research / review tasks** — clear boundaries, no merge conflicts; best way to learn the feature.
- **3–5 teammates** for most workflows; scale up only when work genuinely parallelizes. Three focused teammates often beat five scattered ones.
- **Partition files** — two teammates editing the same file → overwrites. Assign file ownership explicitly.
- **Task sizing**: self-contained units producing a clear deliverable (one function, one test file, one review scope). Too small → coordination overhead wins; too large → long stretches without check-ins.
- **Give teammates full spawn-prompt context** — they don't see the lead's history.
- **If the lead starts implementing instead of delegating**, say: `Wait for your teammates to complete their tasks before proceeding`.
- **Monitor and steer**: check in, redirect bad approaches, synthesize findings as they arrive. Don't let a team run unattended for long.
- **Name teammates deterministically** at spawn if you want to message them by name later.
- **Pre-approve common tool operations** in permissions before spawning to minimize the lead drowning in permission prompts from teammates.

---

## 11. Limitations (things that will bite me)

- **No session resumption for in-process teammates**: `/resume` and `/rewind` don't restore them; lead may message ghosts. Fix: spawn replacements.
- **Task status can lag**: teammates sometimes don't mark complete → dependents stay blocked. Manually update or nudge via the lead.
- **Shutdown is slow**: teammates finish current request / tool call before exiting.
- **One team per session** — clean up before starting a new one.
- **No nested teams** — only the lead can manage; teammates can't spawn teams.
- **Lead is fixed** — can't promote a teammate or transfer leadership.
- **Per-teammate permission modes only settable post-spawn**.
- **Split panes**: tmux or iTerm2 only; not in VS Code integrated terminal, Windows Terminal, or Ghostty.

---

## 12. Troubleshooting quick-hits

| Symptom                                         | Check                                                                                          |
| :---------------------------------------------- | :--------------------------------------------------------------------------------------------- |
| Teammates don't appear                          | In-process? `Shift+Down` to cycle. Split-pane? `which tmux`. iTerm2? `it2` CLI + Python API.   |
| Too many permission prompts                     | Pre-approve in permission settings before spawning                                             |
| Teammate stopped on an error                    | `Shift+Down` to view; give instructions directly or spawn a replacement                        |
| Lead shuts down before work is done             | Tell it to keep going; also instruct it to wait for teammates instead of doing work itself     |
| Orphaned tmux session                           | `tmux ls` → `tmux kill-session -t <session-name>`                                              |
| Task appears stuck (not moving to complete)     | Check if work is actually done; manually update status or have lead nudge teammate             |

---

## 13. Working examples (prompt templates I can reuse)

### A. Parallel PR review
```text
Create an agent team to review PR #<N>. Spawn three reviewers:
- SecurityReviewer: auth, input handling, secret management
- PerfReviewer: hot paths, allocations, N+1 patterns
- TestReviewer: coverage of new branches, edge cases
Have each post findings with severity. Then synthesize.
```

### A hypothesis tournament for a flaky bug
```text
Users report <symptom>. Spawn 4 teammates, each with a different hypothesis.
Have them talk to each other and try to disprove each other's theories.
Update <findings-doc> with the surviving theory and the evidence for it.
```

### C. Cross-layer feature work
```text
Build <feature>. Spawn three teammates:
- Backend (owns src/server/**)
- Frontend (owns src/client/**)
- Tests (owns tests/**)
Each teammate only edits its own path. Coordinate through the task list.
Require plan approval for backend and frontend; tests can proceed directly.
```

### D. Refactor on a risky module
```text
Refactor <module>. Spawn one architect teammate with plan approval required.
Only approve plans that (a) preserve public API, (b) include a migration note,
(c) keep existing tests green.
```

---

## 14. Open questions / things to check on next use

- How do I assign deterministic teammate names via the spawn prompt? (Docs say to tell the lead what to call them — confirm the phrasing the lead respects.)
- Does `TaskCreated` fire for tasks the lead creates for itself, or only for teammates? (Exit-code-2 blocking would be useful for both cases.)
- Confirm the exact `TeamCreate` / `TeamDelete` / `SendMessage` tool schemas when used in a real session — the docs describe behavior but I don't have schemas documented here.
