# agent-skills

Personal skill repository for terminal-based AI agents.

Chinese version: [README.zh-CN.md](README.zh-CN.md)

## Overview

This repository stores reusable skills, scripts, and workflow packaging for AI coding agents.

The current repository is organized around the Codex skill format, but the repository name is intentionally agent-neutral. The long-term goal is to keep the reusable logic portable while isolating host-specific metadata and triggering rules by agent.

## Current Scope

Right now this repository contains Codex-format skills only:

```text
agent-skills/
  codex/
    skills/
      lrc-mp3-lyrics/
```

Included skills:

- `lrc-mp3-lyrics`: Shift `.lrc` timestamps, trim MP3 intros when needed, remove stale `awlrc` blocks, and sync embedded lyrics.

## Repository Layout

Recommended top-level layout:

```text
agent-skills/
  codex/
    skills/
      <skill-name>/
  claude/
    skills/
      <skill-name>/
  shared/
    scripts/
    docs/
```

Current conventions:

- `codex/skills/` contains Codex-compatible skills.
- Each skill lives in its own folder.
- Host-specific metadata stays with the host-specific skill.
- Reusable logic can later be extracted into shared folders if multiple agent ecosystems need the same implementation.

## How To Use These Skills In Codex

Copy a skill folder from this repository into your local Codex skills directory.

Typical destination:

- `$CODEX_HOME/skills/<skill-name>`
- or `~/.codex/skills/<skill-name>` when `CODEX_HOME` is unset

Example:

```text
agent-skills/
  codex/
    skills/
      lrc-mp3-lyrics/
```

Copy `lrc-mp3-lyrics/` to:

```text
~/.codex/skills/lrc-mp3-lyrics/
```

After copying or updating a skill, restart Codex so it reloads the skill list.

## Updating A Skill

When this repository changes:

1. Pull the latest repository changes.
2. Re-copy the updated skill folder into your local Codex skills directory, or sync it in place if that directory is your working copy.
3. Restart Codex.

## Adding A New Codex Skill To This Repository

Put each new Codex skill under:

```text
codex/skills/<skill-name>/
```

Minimum expected structure:

```text
<skill-name>/
  SKILL.md
  agents/
    openai.yaml
```

Optional folders:

```text
scripts/
references/
assets/
```

Repository-level guidance:

- Keep the skill folder self-contained.
- Keep reusable scripts inside the skill until they are clearly shared by multiple skills.
- Prefer adding bilingual references only when they help real usage, not as filler.
- Do not assume another host tool can read Codex metadata directly.

## Cross-Agent Compatibility

The reusable parts of a skill are often portable:

- scripts
- reference material
- workflow logic
- domain heuristics

The packaging is usually not portable as-is:

- trigger metadata
- installation path
- host-specific UI metadata
- loading conventions

That is why this repository is agent-neutral in name but host-specific in layout.

## Notes

- This repository currently targets Codex first.
- A public repository without a dedicated `LICENSE` file should be treated as having no open-source license granted yet.
- If the repository later adds other agent formats, they should live beside `codex/`, not inside it.
