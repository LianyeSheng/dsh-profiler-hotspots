## Agent GitHub identity

For this repository, run agent GitHub operations through
[`scripts/gh-app-run.py`](/scripts/gh-app-run.py) from the repository root.
The wrapper automatically reads `AGENT_GH_APP_ID` and `AGENT_GH_APP_KEY` from
the repository-root `.env`, independently of the current working directory.
Command-line options override environment variables, which override `.env`.
The PEM file must be stored outside the repository with mode `600`;
relative key paths resolve from the repository root. `.env` supports plain
or quoted values, optional `export`, and comments; values are never evaluated
as shell code or expanded. Never print or commit private keys or tokens.

Never stage or commit `.env` or `.env.*` files anywhere in the repository;
only `.env.example` templates with placeholder values are allowed. The ignore
rules exclude secret environment files; the wrapper, pre-commit hook, CI,
and `pnpm run check` run `scripts/verify-no-env.py` to reject them anywhere in the Git index,
including files added with `git add -f`. Never bypass this check with
`--no-verify`, disabled hooks, or alternate commit mechanisms. If it fails,
remove the named paths from the index while retaining the local files.

Use the wrapper for every `gh` command, Git network operation (fetch, pull,
push, or remote inspection over the network), and Git command that creates
commits (including commit, merge, cherry-pick, rebase, and revert). It supplies
the App installation token and default bot author/committer identity, and temporarily
maps this repository's SSH URL to HTTPS without changing persistent Git config.
Local reads and staging, such as `git status`, `git diff`, `git log`, and
`git add`, may run directly.

For new commits authored with agent assistance in this repository, use
`LianyeSheng <wishrem@outlook.com>` as the primary author, keep
`se-tools-agent[bot] <351535718+se-tools-agent[bot]@users.noreply.github.com>`
as the committer, and include that bot in a `Co-authored-by:` commit-message
trailer. The primary author, co-author trailer, and committer are distinct;
bot authentication must remain in use for GitHub operations.

The wrapper currently defaults both author and committer to the bot, so
explicitly override the author with `git commit --author` as shown below.
For other commands that create a new commit and lack `--author`, set
`GIT_AUTHOR_NAME=LianyeSheng` and `GIT_AUTHOR_EMAIL=wishrem@outlook.com`
using `env` **inside** the wrapped command; setting them before invoking the
wrapper is insufficient because it overrides them. Include the co-author
trailer in the new commit message. Preserve original authors and existing
trailers when replaying others' commits; do not rewrite published history
solely to apply this convention.

```bash
python3 scripts/gh-app-run.py
python3 scripts/gh-app-run.py -- gh pr list
python3 scripts/gh-app-run.py -- git commit \
  --author='LianyeSheng <wishrem@outlook.com>' \
  -m 'impl: describe the change' \
  --trailer 'Co-authored-by: se-tools-agent[bot] <351535718+se-tools-agent[bot]@users.noreply.github.com>'
python3 scripts/gh-app-run.py -- git push -u origin HEAD
```

Before pushing a new commit, check `git show -s --format=fuller HEAD` and
`git log -1 --format=%B` to verify the author, committer, and co-author trailer.

The first command checks authentication and reports the bot, repository,
permissions, and token expiry without printing the token. Each invocation
requests a fresh token scoped to `LianyeSheng/dsh-profiler` and attempts to revoke
it when the command exits. Commit author metadata follows Git's semantics:
rebase and cherry-pick may preserve an existing commit's author.

If configuration is missing or App authentication fails, report the blocker;
do not fall back to the user's credentials, personal SSH identity, or a
connector authenticated as the user. For sandbox failures, follow the host
escalation rule above. This entry point configures identity only; existing
requirements for authorization to publish, comment, or merge still apply.

<!-- se-tools:begin component=kit -->
## Installed kit tree

The installed `.agents/se/` tree and the AGENTS.md blocks are rendered from the kit's `components/` sources. Edit the sources and regenerate; never edit an installed copy, because the next installation overwrites it. The install manifest at `.agents/se/install-manifest.json` records the kit revision, the selected components, the tracked or untracked installation mode and every installed digest; it is installation state, never decision evidence, an approval record or a substitute for Git history.

The installer lives at `.agents/se/scripts/kit/install.py` and is also run from the kit checkout as `python3 install.py`. Every subcommand is a dry run without `--apply`, prints each selected component's consequence and prerequisites, and refuses a selection whose prerequisites are unmet:

```bash
python3 .agents/se/scripts/kit/install.py install --target . --components workflow --apply
python3 .agents/se/scripts/kit/install.py uninstall --target . --components bilingual-docs
```

Installation writes a file only when it is absent or byte-identical and stops on a different existing file or block. Removal is per component and all-or-nothing: a missing file, a missing or duplicated block or a digest mismatch stops it before anything is deleted. Upgrades validate the removal dry run first and only then reinstall the selected components.
<!-- se-tools:end component=kit -->

<!-- se-tools:begin component=workflow -->
## Decision-driven workflow

**Read the decisions in play first.** Decisions live in the decision tree under `.agents/notes/`: implemented decisions in `.agents/notes/implemented/`, open proposals in `.agents/notes/proposed/`. A decision outranks tests, types and comments; when they disagree, follow the decision and **report the conflict** instead of smoothing it over. A decision path in a code comment is the decision for that code — read it before changing that code.

**Distinguish records from evidence.** In a request folder only `proposal.md` / `proposal.zh.md` state constraints. `discuss-*` and `reply-*` are non-binding evidence, including inside `implemented/`. Human approval happens directly between the proposal author and the reviewer; neither evidence nor green checks establish approval.

**Preserve request history.** Use one `<type>/<slug>` branch from `main`, record `Base-SHA` in the first request commit body, and use the workflow's event subjects (`proposal`, `discuss`, `reply`, `reply & revise`, optional `decision`, `impl`, `review`, `fix`). Once shared or referenced, append corrections; integrate by merge or fast-forward.

**Classify the task before you do anything else.** *Pure implementation* — the constraints hold and only the approach changes: do it. *Decision change or new decision*: write a proposal before any code, check it against the decisions in play, then stop and wait for a human ruling on any violation or uncertainty. *Unclear*: trace what the change touches, then classify.

**Bypass only on request.** When the user explicitly says to skip the process for this change, do it and record `Decision process: bypassed (reason: …)` in the commit message.

**Write a decision record only when a decision changed** — a constraint added, relaxed or overturned. A pure implementation swap, a mechanical edit or a local change does not qualify; keep the record tree the size of the decisions, not of the commits.

The operative procedure is [the workflow contract](/.agents/se/contracts/workflow.md); record shape is [the note format](/.agents/se/contracts/note-format.md), references are [the anchor convention](/.agents/se/contracts/anchor-convention.md), and the judgments no machine makes are in [the review checklist](/.agents/se/contracts/review-checklist.md). Record templates are installed under `.agents/se/templates/`.

## Apply the workflow with the decision skills

The `decision-*` skills apply [the workflow contract](/.agents/se/contracts/workflow.md) on demand. They are not an indispensable runtime: the procedure stays operable without them, and a skill never replaces a rule the contracts state. Use `decision-intake` to turn a fuzzy request into candidate constraints, `decision-check` before landing a change, `decision-revise` as the only write path into the decision tree, `decision-audit` for periodic drift inspection, and `design-discipline` for structure review before coding. Each skill's trigger and steps are in its `SKILL.md` under `.agents/skills/`.

## Run the gates before committing

The shipped validators check what machines can check. Run them in order and never let one invoke another. With the bilingual-docs component installed, the pairing gate runs first; then the document gate, then the link gate:

```bash
python3 .agents/se/scripts/decisions/verify.py --staged
python3 .agents/se/scripts/decisions/verify_links.py --staged
```

CI requires an explicit comparison base instead of `--staged`; the local hook may check the index with `--staged`. Every gate run ends by declaring what it did not check — read that list and review those items. Green checks prove neither human approval nor reviewer agreement. The judgments left to review are in [the review checklist](/.agents/se/contracts/review-checklist.md).
<!-- se-tools:end component=workflow -->

<!-- se-tools:begin component=bilingual-docs -->
## Bilingual documents

When this repository keeps bilingual documents, every in-scope document is three sibling files: `foo.md` (English), `foo.zh.md` (Chinese) and `foo.i18n.yaml` (the consistency record). Update both sides in the same change and re-record the pair; apply one update as a minimal patch to the counterpart, never as a full re-translation. For understanding or reviewing a document, the English side is enough — do not read the Chinese counterpart alongside it.

Scope, exclusions and the record format are defined by [the bilingual contract](/.agents/se/contracts/i18n/README.md); translation rules are in [translation-rules.md](/.agents/se/contracts/i18n/translation-rules.md) and terms in [terminology.md](/.agents/se/contracts/i18n/terminology.md). Re-record and check a pair with:

```bash
node .agents/se/scripts/docs/verify-translation-pairing.ts --write <pair>
node .agents/se/scripts/docs/verify-translation-pairing.ts
```

The pairing gate requires Node 24+, and it makes the adopting repository pair its own in-scope documents; without it the rest of the workflow and the other gates still run. The extended [update-bilingual-docs](/.agents/skills/update-bilingual-docs/SKILL.md) workflow runs only when the user explicitly asks for it.
<!-- se-tools:end component=bilingual-docs -->
