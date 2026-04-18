---
name: commit-api-doc
description: Generate compact Chinese API/interface documentation from git commits or diffs, especially in Java Spring Boot repositories. Use when Codex needs to inspect recent commits, changed controllers, DTO/VO/entity/service/mapper files, and summarize endpoint additions or request/response contract changes into a fixed text template. Trigger this skill for requests like "根据最近两次提交写接口文档", "按这种风格给我接口文档", "只列新增字段", or when the user provides a sample block and expects the same output style.
---

# Commit API Doc

Inspect commit diffs and turn actual API changes into short Chinese interface docs. Reuse the user's sample style exactly when one is provided; otherwise, default to a compact line-based format instead of tables.

## Workflow

1. Determine scope from the request.

- Use the commits, commit range, or "recent N commits" the user asked for.
- If commit messages are meaningless, rely on `git show`, not commit titles.

2. Locate interface entry points.

- Start from changed controller files.
- Combine class-level `@RequestMapping` with method-level mappings such as `@PostMapping`, `@GetMapping`, `@RequestMapping`.
- Use the actual controller method name or comment to infer the Chinese feature name.

3. Trace request and response contracts.

- For request bodies, inspect changed DTO/VO/entity classes and service code that consumes fields.
- For query parameters, inspect controller method parameters directly.
- For response fields, inspect VO/entity changes, mapper XML aliases, and service post-processing.
- For list/detail APIs, include only fields that are actually returned by the modified query or assembly logic.

4. Classify each affected API.

- New interface: document the interface and its effective request shape.
- Existing interface with new request fields: only list added request fields.
- Existing interface with new response fields: only list added response fields.
- Logic-only change without contract change: omit it unless the user explicitly wants behavioral notes.

5. Write the final text in the user's format.

- If the user provides a sample block, mirror its labels, punctuation, and line breaks.
- If the user says "新增参数就只需要列新增字段", use `入参新增字段` and `出参新增字段` instead of repeating unchanged fields.

## Output Rules

Use plain Chinese blocks like this unless the user asks for another format:

```text
业务名-功能名
接口：/xxx/yyy
入参：{"id":"记录ID"}
```

Or, for existing APIs with incremental changes:

```text
业务名-功能名
接口：/xxx/yyy
入参新增字段：{"newField":"说明"}
出参新增字段：{"newRespField":"说明"}
备注：补充说明
```

Keep these rules:

- One API block per feature.
- Do not use tables unless the user asks for tables.
- Do not repeat unchanged historical fields for old interfaces.
- For brand-new endpoints, show the current request shape needed to call the new endpoint.
- For array bodies, use compact JSON-like examples such as `[{"id":"记录ID"}]`.
- For query parameters, still write them as a compact JSON-like object for readability.
- Prefer field descriptions from `@ApiModelProperty`, comments, names, and validation logic.

## Extraction Heuristics

- If both controller and service changed, trust the service for which fields are truly used.
- If mapper XML changed aliases or selected columns, treat those as response field changes.
- If only enum/status values were added, mention them in `备注` when they affect API understanding.
- If a helper method builds derived fields, document the derived field only if it becomes observable in the response.
- If a validation rule changed but fields did not, mention it in `备注` rather than pretending the schema changed.

## Quality Bar

- Base every documented field on an observed code change.
- Do not invent endpoint paths, fields, or remarks.
- If you cannot confirm an interface contract change, leave it out or clearly mark the uncertainty.
- Keep the result concise. The goal is something the user can paste directly into a ticket, doc, or chat.

## Example Prompts

Use $commit-api-doc to write interface docs for the latest two commits in this repository.

Use $commit-api-doc and follow this sample style exactly: `异常登记-是否可修改责任人 / 接口：... / 入参：...`.
