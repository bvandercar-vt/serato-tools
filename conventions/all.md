# General conventions

Applies to every repo, independent of language or framework.

- **Branches**
  - **Naming**: Name work branches `<type>/<slug>`, where `<type>` is a Conventional Commits type — `feat`, `fix`, `chore`, `refactor`, `ci`, `docs`, `style`, `test`, `perf`, or `build` — and `<slug>` is a short kebab-case description of the change. Never use a `claude/` prefix or a random session suffix.
  - **Renaming an assigned branch**: The naming rule above overrides the branch name a session is assigned by default — if you were given one, rename it before the first push.
- **PR review threads**: Always reply on the thread with what changed (or why it wasn't changed), then mark the thread resolved. Do this for every thread you act on, not just the ones that needed discussion.
- **Formatting**: Run the repo's `format` script after making edits and before every commit, using whichever package manager the repo uses (`npm run format`, `pnpm run format`, ...).
- **Markdown**: Don't hard-wrap prose. Keep each paragraph, list item, and table row on one line and let the editor wrap it. Manual line breaks mean a one-word edit reflows the whole block, so the diff shows a rewritten paragraph instead of the words that actually changed.
