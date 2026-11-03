# Kit adoption guide

English | [中文](/.agents/se/README.zh.md)

The kit is a reusable development workflow for agent-assisted work on DeepSeek Harness (DSH): development agreements, skills that apply them, and validators for the artifacts they produce. It ships as an installed `.agents/` tree plus one marked block per selected component in the repository's `AGENTS.md`; the kit's own sources are never installed, no shipped file refers to the kit author's decision history, and once installed no path outside `.agents/` is required to apply the workflow.

Adoption is a clone-local copy procedure with a manifest, not a published package. The installer is offline and standard-library Python, every subcommand is a dry run unless applied, every installed file is recorded with a digest, and updates are reviewed diffs from a pinned kit revision.

## What the kit is

The kit delivers three things: the agreements that define conforming delivery and where human authority sits; skills that help an agent apply those agreements; and validators that check what machines can check about the resulting artifacts. The contracts state the operative procedure, the record format, the anchor convention and the review checklist; the skills apply them on demand; the gate validators run in a fixed order and end by declaring what they did not check.

The kit ships methodology, not project content. Consumer business logic, project instructions and the decision record tree stay owned by the adopting repository: the kit installs no decision record and imports no decision history. A repository that keeps its own `AGENTS.md` keeps its text; the installer only adds its marked blocks.

The installed payload depends on the selected components:

| Installed path | Content | Component |
| --- | --- | --- |
| `.agents/se/contracts/` | The workflow contracts: the operative procedure, the record format, the anchor convention and the review checklist. | `workflow` |
| `.agents/se/templates/` | Record templates for proposals, discussions and replies. | `workflow` |
| `.agents/skills/<name>/` | The selected skills. | `workflow` |
| `.agents/se/scripts/decisions/` | The decision, link and anchor validators. | `workflow` |
| `.agents/se/contracts/i18n/` | The bilingual pairing contract, translation rules and terminology. | `bilingual-docs` |
| `.agents/se/scripts/docs/` | The optional bilingual pairing gate. | `bilingual-docs` |
| `.agents/se/scripts/kit/install.py` and `.agents/se/README.md` | The installer copy and this adoption guide. | `kit` |
| `AGENTS.md` blocks | One marked block per selected component. | all selected |

The installed tree is generated. Authors edit the kit sources and regenerate it; a hand edit to an installed copy is overwritten by the next render and caught as drift.

Paths under `.agents/notes/` in instructions, validator roots, examples and template placeholders describe the adopting repository's own record tree. They are allowed; the kit copies no records and must not depend on se-tools' development history. Component source code retains development decision anchors, which rendering removes from installed code. The closure check rejects concrete Markdown links into the record tree and any remaining code anchors into it before writing. Review still checks prose for dependencies on the author's history. Self-installation renders the same component bytes and marked blocks as consumer installation; se-tools developers use the component sources to trace development decisions.

## Required core and optional components

The required core is `workflow`. It owns the contracts, templates, decision skills, validators and their tests as one functional capability. Installing it delivers the complete decision workflow.

`bilingual-docs` and `kit` are optional. The bilingual component adds the pairing contract and makes the adopting repository pair its own in-scope documents; its gate needs Node 24+, and without it the rest of the workflow runs unchanged. The kit component installs the installer copy and this guide into the target, so the target keeps the installer and this guide; removal works from the target, while an update still runs from a kit checkout. Neither optional component changes the workflow's guarantees.

## Components

Each functional component owns its `components/<id>/registry.json`, declaring consequences, prerequisites, fragments and source-to-installed mappings relative to its directory. These local registries are the only selection source; there is no central registry. The installer discovers components and orders them by dependencies, using component id to break ties among ready components. The kit revision is declared only in `components/kit/registry.json`. The installer prints each selected component's consequence and prerequisites before writing and refuses a selection whose prerequisites are unmet.

| Component | Status | Consequence | Prerequisites |
| --- | --- | --- | --- |
| `workflow` | required core | The complete decision-driven workflow: contracts, templates, decision skills, validators and evidence-chain tooling. | none |
| `bilingual-docs` | optional | The bilingual pairing contract, translation rules, terminology and the optional pairing gate with its Node requirement. | `workflow` |
| `kit` | optional | The installer, the install manifest protocol and this adoption guide for the installed tree. | none |

## Prerequisites

| Prerequisite | Needed for |
| --- | --- |
| Python 3 | The installer and the decision, link and anchor validators. The installer uses only the standard library and makes no network call. |
| Git | Recording the installed tree and its manifest in the repository's history; adoption and updates are reviewed diffs. |
| DSH and its base profile | Running the workflow's agents. The contracts, skills and gates work through ordinary repository tools, and the kit needs no plugin. |
| Node 24+ | Only the optional bilingual pairing gate. Without `bilingual-docs`, the workflow's other parts do not use Node. |

The plugin adds one more prerequisite: `dsh plugin` forwards to pnpm, so pnpm must be on `PATH` where the plugin is installed and removed. It is not needed to install, update or remove the kit.

## Installing from the kit checkout

Run [the installer](/.agents/se/scripts/kit/install.py) from a pinned kit checkout against the target repository. The checkout's root `install.py` is a symlink to the installer source and resolves to it; the installed copy under `.agents/se/scripts/kit/` is the same code. The installer refuses symlinked destination paths and paths that resolve outside the target, and it leaves no state outside the target.

Every subcommand is a dry run unless `--apply` is given. A dry run performs the same validation as the applied run, prints the selected components' consequences and prerequisites and the planned changes, and exits non-zero on a conflict. Installation writes a file only when it is absent or byte-identical; a different existing file stops the run with a non-zero exit and writes nothing.

```bash
# dry run: prints consequences, prerequisites and planned changes only
python3 install.py install --target ../svc

# install the required core
python3 install.py install --target ../svc --components workflow --apply

# install every component, tracked mode by default
python3 install.py install --target ../svc --apply
```

`--components` takes a comma-separated list of component ids; the installer normalizes their order by dependencies. Omitting it selects every component on `install`, and every component recorded in the manifest on `uninstall` and `upgrade`. A selected component's prerequisites must already be installed or be selected in the same run. Only selected components contribute files and one `AGENTS.md` block; an unselected component contributes nothing, so no resident guidance refers to a contract or a gate the repository does not have.

### AGENTS.md blocks

The installer composes `AGENTS.md` from one marked block per selected component, in deterministic dependency order, and leaves every byte outside the blocks untouched:

```
<!-- se-tools:begin component=workflow -->
...
<!-- se-tools:end component=workflow -->
```

Each block is single-language English guidance and links only to installed paths that its component or a declared prerequisite installs. The installer runs that link-closure check for the selected set before writing and fails with a non-zero exit and no writes when a reference points at an unselected component. A different existing block, a duplicate marker or an unregistered block is a conflict that exits non-zero and writes nothing.

### Skill-name collisions

Before writing, the installer reports a skill collision when a selected component's skill would shadow a different existing file at `.agents/skills/<name>/`, and it refuses to overwrite it. Resolve the collision on the repository's own side: prefix the repository's skill with the project's short name (for example `svc-decision-check`, in the directory and in the skill's frontmatter `name`) then re-run. Never rename or edit an installed kit skill: the manifest records its path and digest, and upgrade or removal refuses a changed file.

## Walkthrough: a new repository

A new repository starts empty, so one installation creates the tracked tree, the `AGENTS.md` blocks and the manifest in a single reviewed change. From the kit checkout:

```bash
# create the repository, then install the required core from the kit checkout
mkdir ../svc && git -C ../svc init
python3 install.py install --target ../svc --components workflow --apply

# commit the adoption change in the new repository
git -C ../svc add .agents AGENTS.md
git -C ../svc commit -m "chore: adopt the development workflow kit"
```

1. Read the dry-run output: the required core's consequences and prerequisites, the planned files and the `AGENTS.md` blocks.
2. Apply the installation; the installer writes the payload and `.agents/se/install-manifest.json`, and creates `AGENTS.md` because the repository has none.
3. Commit the installed tree, the `AGENTS.md` blocks and the manifest together, so adoption is one reviewable change.
4. Create the repository's own decision tree with the installed templates, starting from the proposed lifecycle; the kit imports no decision history.
5. Wire the installed validators into the repository's hook or CI in the gate order the `workflow` block states, and commit the wiring.
6. Add optional components in later installation runs and the optional plugin in the DSH profile, not in the repository.

## Walkthrough: an existing repository

An existing repository keeps its instructions. The installer appends its marked blocks and never rewrites text outside them; it refuses a conflicting block or a different existing file instead of overwriting it. Where existing guidance duplicates or contradicts the kit's, the repository's owners decide: keep the repository's rule and adjust or omit the kit block, or adopt the kit rule and retire the duplicate. Expose the conflict rather than merging it silently.

1. Run the installation dry run against the existing repository and read the planned block additions, consequences and prerequisites.
2. Reconcile conflicts by editing the repository's own instructions or by selecting fewer components; the installer does not choose between two conflicting instructions.
3. Apply the installation; the manifest records the files and blocks the installer added, so later upgrade and removal touch only those.
4. Create the repository's own empty decision tree; the kit installs no record and imports no history.
5. Run the installed validators on the adoption change in gate order and fix findings before merging; green checks prove neither human approval nor reviewer agreement.
6. Keep the plugin optional: install it in the DSH profile when inline cards are wanted, and remove it without changing any installed repository file.

## The install manifest

The manifest at `.agents/se/install-manifest.json` records the installation exactly: `kit_revision` from the kit component registry, `components` in deterministic dependency order, `mode` as `tracked` or `untracked`, `agents_md_created` (whether the installer created `AGENTS.md`), every installed file as `{path, sha256, component}` ordered by dependency order and then path, and `blocks`, mapping each component id to the SHA-256 of its block's bytes from the begin marker through the end marker excluding the final newline.

```json
{
  "kit_revision": "2026-11-03.1",
  "components": ["workflow"],
  "mode": "tracked",
  "agents_md_created": true,
  "files": [
    {"path": ".agents/se/contracts/workflow.md", "sha256": "…", "component": "workflow"}
  ],
  "blocks": {"workflow": "…"}
}
```

The manifest is consumer-owned installation state. It is never decision evidence, an approval record or a substitute for the repository's Git history; upgrade and removal read it, and a missing or corrupt manifest is an error with no deletion.

### Installation modes

Installation is tracked by default. The repository commits the installed tree, the `AGENTS.md` blocks and the manifest, so a fresh clone lets agents read the methodology without running the installer, and the drift gate renders a fresh install and compares it with the tracked tree.

Untracked mode keeps generated files out of history. Add `.agents/se/` and `.agents/skills/` to the repository's `.gitignore` — the installer checks that list but does not edit it — and install with `--mode untracked`. The manifest records the mode; a dry-run install from the pinned revision compares the fresh render with the working tree and exits non-zero on any difference. A repository in this mode must run the installer before its agents read the methodology: until then, the `AGENTS.md` blocks point at files that are not on disk.

## Updating

The kit has no released package and no stable interface; an update moves to a new pinned kit revision and re-runs the installer from that checkout. Read the revision diff first, dry-run the upgrade against the repository, and review the planned removal and reinstallation before applying.

```bash
# dry run first, then apply
python3 install.py upgrade --target ../svc
python3 install.py upgrade --target ../svc --apply
```

Old installations with separate `skills` and `gate` owners must upgrade all components without `--components`. The installer derives their replacement owners from the installed file paths declared by the current registries, validates every old file and block digest, and preflights the new installation before removing anything. No permanent selection aliases remain. An owner without a replacement requires explicit removal first; uninstall can still select owners recorded by an old manifest.

`upgrade` validates a removal dry run for the selected components first. Only a conflict-free removal and reinstall preflight proceed, and only then are those components reinstalled from the new revision; unselected components are untouched. In tracked mode the installed tree and manifest diff is the reviewable change; in untracked mode review the working tree before applying. Every prerequisite is checked again.

## Removing

Removal is per selected component and all-or-nothing. A missing file, a missing or duplicated block or a digest mismatch is a prompt: the installer reports it, exits non-zero and deletes nothing. A clean run deletes exactly the recorded files and blocks; the other components' files and blocks, and all content outside the blocks, are untouched. `AGENTS.md` itself is deleted only when the installer created it and only whitespace remains. A missing or corrupt manifest is an error with no deletion.

```bash
# dry run first, then apply
python3 install.py uninstall --target ../svc --components bilingual-docs
python3 install.py uninstall --target ../svc --components bilingual-docs --apply
```

Omitting `--components` removes every component recorded in the manifest. Removing the optional kit component removes the installer copy and this guide from the target, so a later update runs from a kit checkout again; a final removal can still run from the installed copy before it is deleted. A removed component's files and block are gone; the other components are untouched.

## Self-install and the drift gate

se-tools installs its own kit into itself, so the repository that ships the kit exercises the same path a consumer takes. Its tracked `.agents/` tree and `AGENTS.md` blocks are rendered from its sources, and an installed copy is never edited by hand: the next render overwrites it and the drift gate fails. After editing a source, regenerate from the checkout with an upgrade, because `install` refuses differing files by design.

```bash
python3 install.py upgrade --target . --self --confirm-self --apply
```

`--self` is internal to se-tools, requires `--confirm-self`, and is refused on any other target. The drift gate renders a fresh install into a temporary directory and compares the files, the manifest and the `AGENTS.md` blocks with the tracked tree; it fails on any difference and runs as part of the full check (`pnpm run check`, or `pnpm run verify:install` for the gate alone).

## Optional DSH plugin: dsh-se-cards

`dsh-se-cards` is the kit's optional DSH bundle: it renders inline static HTML cards and mermaid diagrams from a `dsh-card` fence at the point in the reply where the fence is written. The plugin is outside the installer and the manifest. It is a user-scoped step in a DSH profile, it changes no repository file, and removing it leaves the installed tree unchanged and every shipped validator green. A consuming repository's continuous integration runs the installed gates; it installs neither the kit components nor the plugin.

### Validated range and degradation

The validated DSH range is the single release DSH `0.2.2-alpha.2`, tested at commit `ce7073d51254c26cd63b22a60835b8f948deb447`; any other release is outside it until the DOM hooks are re-tested. The renderer is DOM decoration, not a supported render hook: it observes the rendered conversation and replaces a settled `dsh-card` code block in place, so it depends on DOM hooks that DSH does not promise as a plugin API.

When a hook changes, the fence silently stays an ordinary code block: the reply text and session data are unchanged, replay and export keep the fence, and clients without the bundle always show a code block. Removing the plugin restores plain code blocks on reload and leaves every installed repository file and validator result unchanged.

### Installing and removing the plugin

Pin the source to the kit revision recorded as `kit_revision` in the install manifest. Build and pack the bundle tarball from that checkout; the tarball carries the built `dist/` artifacts the package declares, so the profile installs prebuilt code and needs no build script. The package declares `dsh.bundle.patch` at `./cordis.patch.yml`, so `dsh plugin add` also appends its layer to the profile's `dsh.profile.bundles`.

```bash
# from the pinned kit checkout: build and pack the bundle
pnpm install
pnpm --filter dsh-se-cards run build
pnpm --filter dsh-se-cards pack --pack-destination ./.tmp

# install into a DSH profile, then verify the layer
dsh plugin --profile <name> add ./.tmp/dsh-se-cards-0.2.0.tgz
dsh --profile <name> --dump-config

# remove it again
dsh plugin --profile <name> remove dsh-se-cards
```

The packed tarball is the pinned source: do not install from a moving directory link or an unpinned git reference, because either can change what runs in the profile without a reviewed kit revision. `--dump-config` should show the `dsh-se-cards` layer before you rely on the plugin. Removing the dependency removes the layer as well; restart or reload the client to return to plain code blocks.
