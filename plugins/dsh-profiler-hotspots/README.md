# dsh-profiler-hotspots

English | [中文](/plugins/dsh-profiler-hotspots/README.zh.md)

`dsh-profiler-hotspots` is a DSH Web UI plugin package that contributes an Execution hotspots page to the Web client: a searchable workspace and session browser. The Host half registers nothing; all behavior lives in the client half. The repository's goal and responsibility boundary are defined in [the project charter](/docs/agent-profiler.md).

## What the plugin contributes

The client half adds one entry to the left sidebar's panel list: a bar-chart icon and the label Execution hotspots. Selecting the entry opens the page in the main column. The page has no heading; a full-width search box is its first element.

## Search

Typing in the search box filters the grouped workspace and session list in real time, with no Enter key and no Host round trip. The filter matches metadata case-insensitively: the session title, the workspace title, and a substring of the session id. Matches stay grouped under their owning workspace: under the Search results label and its result count, each matching workspace appears as a header row with an open folder icon and the workspace name, and its matching sessions follow below. A workspace title match keeps every session in that workspace. Matches within a workspace are listed newest first, and there is no result cap. The provisional blank session has no durable title and never matches. The client half filters metadata it already holds.

## Workspace and session list

With an empty query, the page shows the same grouped workspace and session list as the sidebar's Workspaces region, under the Workspaces section label. Each workspace row is a button that expands or collapses its sessions; it shows the host's open folder glyph while expanded and the host's closed folder glyph while collapsed, and on devices with hover the glyph becomes a disclosure triangle. The workspace containing the current session tints its folder with the brand color, and the current session row is highlighted. Ordinary session rows show a status dot, the session title, and the relative update time; the provisional blank session appears as New Session with only its title. Archived sessions and subagent-origin sessions are hidden, and sessions outside a workspace appear in the Ungrouped group. Selecting a session opens it in the conversation.

## Package layout

| Path | Role |
|---|---|
| `package.json` | Package metadata, exports, and the `dsh.bundle` and `dsh.client` declarations |
| `cordis.patch.yml` | Bundle patch row that inserts the plugin |
| `index.js` | Host half; exports a no-op `apply()` |
| `client.js` | Client half; adds the sidebar entry and renders the page |
| `icon.svg` | Bar-chart package icon |
| `locale/en.json` | English plugin metadata: `meta.title` and `meta.description` |
| `locale/zh.json` | Chinese plugin metadata: `meta.title` and `meta.description` |

`package.json` exports the Host half as the package entry (`./index.js`), the client half as `./client` (`./client.js`), the language resources as `./locale/*.json`, and the icon as `./icon` (`icon.svg`).

## Identifiers

| Identifier | Value | Role |
|---|---|---|
| Package name | `dsh-profiler-hotspots` | Names the package and its bundle patch row |
| Bundle patch row id | `dsh-profiler-hotspots` | The row `cordis.patch.yml` inserts, with an empty `config` |
| Main panel id | `hotspots` | The id under which the client half registers the sidebar entry and the page |
| Locale namespace | `dsh-profiler-hotspots` | The namespace under which the client half registers its UI strings |

## Configuration

The package takes no configuration; the bundle patch row inserts it with `config: {}`. The `dsh.client` block declares `platform: "web"` and `immediately: true`, and lists the packages the client half injects: `@deepseek-ai/dsh-client-locale`, `@deepseek-ai/dsh-client-ui-layout`, `@deepseek-ai/dsh-client-ui-session`, `@deepseek-ai/dsh-client-ui-sidebar`, and `@deepseek-ai/dsh-client-ui-workspace`.

## Limitations

- **Metadata search only** — the search covers session titles, workspace titles, and session id substrings, not session content.
- **No workspace or session management** — the page offers no add, rename, or delete action for workspaces and no pin or archive action for sessions.
- **No archive filter** — archived sessions stay hidden; the page has no control to show them.
