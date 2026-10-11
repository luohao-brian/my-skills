<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `0. First-time setup — style guide gate`

## 0. First-time setup — style guide gate

**Before generating your first diagram in a new project, verify the style guide has been customized.**

Do not silently ship default-skinned diagrams into a branded project.

First resolve any project `.diagram-design` marker per [`references/profiles.md`](../../upstream/references/profiles.md); a successfully resolved marker selects its profile and bypasses this gate. That reference owns failures, the protected default, and save behavior.

Open [`references/style-guide.md`](../../upstream/references/style-guide.md) and check the default tokens. If they are still the shipped defaults (paper `#f5f5f5`, ink `#2d3142`, accent `#bf4520`), **pause and ask the user**:

> *"This is your first diagram in this project and the style guide is still default. Customize now? Options: (a) website URL, (b) installed skill, (c) local folder/design-system, (d) paste tokens, (e) keep default, (f) load saved profile."*

Then branch per the matching section of [`references/onboarding.md`](../../upstream/references/onboarding.md); for **(f)** follow [`references/profiles.md`](../../upstream/references/profiles.md).

**Once the style guide has been customized** (or the user explicitly chose default), skip this gate on later runs. A leading profile header names the copied-in active profile. Without a header, any semantic-role value or typography family differing from shipped defaults means **custom-unsaved**: skip the gate and offer to save it as a profile. All-default tokens with no marker/header trigger the gate. After onboarding, offer to save as a named client profile per `references/profiles.md`.

---
