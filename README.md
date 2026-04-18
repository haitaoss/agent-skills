# agent-skills

Personal skill repository for terminal-based AI agents.

Current layout:

```text
agent-skills/
  codex/
    skills/
      commit-api-doc/
      lrc-mp3-lyrics/
```

Notes:

- `codex/skills/` contains skills in the Codex skill format.
- Skill logic and scripts may be reusable across agents, but metadata and trigger format can differ by host tool.
- Add future agent-specific ports under separate top-level folders such as `claude/` or `generic/`.
