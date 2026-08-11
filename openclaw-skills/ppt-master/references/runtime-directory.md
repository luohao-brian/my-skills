# Directory Contract

The caller owns the workspace; PPT Master owns only files inside the selected
project directory.

## Project root

- Prefer a user-selected output directory. Otherwise create a dedicated
  projects root inside the current runtime workspace.
- `project_manager.py init` must receive `--dir <absolute-projects-root>`; the
  packaged CLI rejects omission.
- Pass the returned absolute project path to every later command.
- Never write projects, previews, backups, exports, or dependency environments
  under `{baseDir}`, the source repository, a relative `projects/`, `$HOME`, or
  another implicit global directory.

```bash
PROJECTS_ROOT="<caller-selected directory or runtime workspace>"
python3 {baseDir}/scripts/project_manager.py init <name> --format ppt169 --dir "$PROJECTS_ROOT"
```

## Path ownership

- `{baseDir}`: immutable Skill resources and executable helpers.
- `<absolute-project>`: all mutable source, analysis, SVG, validation, preview,
  backup, and export artifacts.
- Runtime caches: owned by the calling Agent/runtime, never moved into the Skill
  or project unless the relevant capability explicitly returns a project asset.

Resolve symlinks and normalize paths before destructive or overwrite operations.
Do not move or overwrite a caller-owned source unless the user explicitly asks.
