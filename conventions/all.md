# General conventions

Applies to every repo, independent of language or framework.

- **Branches**
  - **Naming**: Name work branches `<type>/<slug>`, where `<type>` is a Conventional Commits type — `feat`, `fix`, `chore`, `refactor`, `ci`, `docs`, `style`, `test`, `perf`, or `build` — and `<slug>` is a short kebab-case description of the change. Never use a `claude/` prefix or a random session suffix.
  - **Renaming an assigned branch**: The naming rule above overrides the branch name a session is assigned by default — if you were given one, rename it before the first push.
- **PR review threads**: Always reply on the thread with what changed (or why it wasn't changed), then mark the thread resolved. Do this for every thread you act on, not just the ones that needed discussion.
- **Formatting**: Run the repo's `format` script after making edits and before every commit, using whichever package manager the repo uses (`npm run format`, `pnpm run format`, ...).
- **Dependency ranges**: Unless instructed otherwise, write the caret range down to the axis that semver treats as breaking, and no further — `^8` for a 1.0+ package, `^0.45` for a 0.x one, where the minor is that axis, unless it has been explicitly found that a minimum minor or patch version is needed. Installers write the full `^8.23.1` by default; trim it. The lockfile is what pins the build, so the extra precision only claims a floor that was never actually established.
- **Markdown**: Don't hard-wrap prose. Keep each paragraph, list item, and table row on one line and let the editor wrap it. Manual line breaks mean a one-word edit reflows the whole block, so the diff shows a rewritten paragraph instead of the words that actually changed.
