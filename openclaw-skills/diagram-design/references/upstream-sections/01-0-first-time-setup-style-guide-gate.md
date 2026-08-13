<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `0. First-time setup — style guide gate`

## 0. First-time setup — style guide gate

**Before generating your first diagram in a new project, verify the style guide has been customized.**

Don't silently ship default-skinned diagrams into a branded project.

Open [`references/style-guide.md`](../../upstream/references/style-guide.md) and check the default tokens. If they're still the shipped defaults (paper `#f5f5f5`, ink `#2d3142`, accent `#eb6c36` atomic-tangerine), **pause and ask the user**:

> *"This is your first Schematic in this project. The style guide is still at the default (neutral white-smoke + atomic-tangerine). Do you want to customize it to match your brand first? Options: (a) pull from your website URL, (b) extract from an installed skill, (c) extract from a local folder / design-system directory, (d) paste tokens manually, (e) proceed with the default for now."*

Then branch:

- **(a)** → follow [`references/onboarding.md § URL`](../../upstream/references/onboarding.md) to fetch the site, extract palette + fonts, propose a diff, and write `style-guide.md`.
- **(b)** → follow [`references/onboarding.md § Skill`](../../upstream/references/onboarding.md) — ask which skill, read its SKILL.md / CSS / token files, map to semantic roles, propose diff.
- **(c)** → follow [`references/onboarding.md § Folder`](../../upstream/references/onboarding.md) — ask for the path, glob for CSS/JSON/MD token files, map to semantic roles, propose diff.
- **(d)** → accept the user's tokens and write them into `style-guide.md` under a new "Custom tokens" section.
- **(e)** → proceed; optionally remind the user they can run onboarding later.

**Once the style guide has been customized** (or the user explicitly opted for default), skip this gate on subsequent runs. A simple way to detect customization: if the `accent` value in `style-guide.md` differs from `#eb6c36`, assume custom.

---
