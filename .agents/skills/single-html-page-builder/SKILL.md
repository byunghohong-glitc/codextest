---
name: single-html-page-builder
description: "Workflow for a single-file HTML page, generating or editing index.html with the html-builder agent."
---

# Single HTML Page Builder

Use this skill when the user asks for a single-file HTML page, usually by requesting an `index.html` for a topic, landing page, demo, or small site.

## Workflow

1. Confirm the page requirements from the user request.
2. If information is missing, ask up to 3 short questions.
3. If the user does not answer, continue with sensible defaults and report the assumptions you made.
4. Use the confirmed `html-builder` agent name from `.codex/agents/html-builder.toml` to create or edit only `index.html`.
5. Put all HTML, CSS, and JavaScript inside `index.html`.
6. Do not use React, Vue, npm, package installs, or external CDN imports.
7. Apply semantic HTML and a mobile-friendly viewport meta tag.
8. After implementation, perform a short code review before finishing.

## Code Review Checks

- `<html`, `<head`, and `<body` are present.
- `<style>` is present.
- The viewport meta tag is present.
- There are no external CDN links or script imports.
- No unnecessary extra files were created.
- No file other than `index.html` was modified.

## Stop Hook Coordination

- Do not run the Stop hook directly from this skill.
- At the end of the turn, the existing Stop hook should handle any test or auto-commit behavior based on whether `index.html` changed.
- Do not perform the hook action here, and do not run `git push`.

## Output Expectations

- Report any assumptions clearly when default values were used.
- Keep the result focused on the single `index.html` file unless the user explicitly asks for something else.
