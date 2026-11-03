/**
 * Browser half of dsh-profiler-hotspots.
 *
 * Contributes two things to the Harness Web page:
 *
 *  1. a `sidebar.panellist` entry — the analysis glyph plus the label
 *     "执行热点分析" that the sidebar shell turns into a panel row; and
 *  2. the `main` panel registered under the matching panel id, which the
 *     sidebar opens when that row is clicked.
 *
 * The panel is a search surface over the workspace/session index the left
 * sidebar already shows. With an empty query it renders that same grouped
 * browser (workspace rows with open/closed folders, session rows with status
 * dot and relative time); a non-blank query filters the index in place,
 * synchronously on every keystroke, and keeps each match under its workspace
 * row so the owning workspace stays visible. Everything is read from the
 * framework's standard slot hooks, so the page never folds session events or
 * issues a Host request of its own.
 */

window.__ModuleLoader__.load({
  id: 'dsh-profiler-hotspots',
  factory(require) {
    const React = require('react')
    const h = React.createElement

    /** Locale namespace owned by this plugin. */
    const NS = 'dsh-profiler-hotspots'
    /** Panel id shared by the sidebar entry and the main panel it opens. */
    const PANEL_ID = 'hotspots'

    const ZH = {
      'panel.label': '执行热点分析',
      'search.aria': '搜索工作区或会话',
      'search.placeholder': '搜索会话名称、工作区或 Session ID',
      'search.clear': '清除搜索',
      'search.results': '搜索结果',
      'search.resultCount': '{n} 条结果',
      'search.noMatches': '无匹配会话',
      'search.empty': '暂无会话',
      'section.workspaces': '工作区',
      'group.ungrouped': '未分组',
      'group.expand': '展开工作区',
      'group.collapse': '收起工作区',
      'session.new': '新会话',
      'session.untitled': '未命名',
      'row.pinned': '已置顶',
      'status.running': '运行中',
      'status.warning': '等待处理',
      'status.done': '已完成',
      'status.idle': '空闲',
      'time.now': '刚刚',
      'time.minutes': '{n}分钟',
      'time.hours': '{n}小时',
      'time.days': '{n}天',
      'time.months': '{n}个月',
      'time.years': '{n}年',
    }

    const EN = {
      'panel.label': 'Execution hotspots',
      'search.aria': 'Search workspaces or sessions',
      'search.placeholder': 'Search sessions, workspaces, or Session IDs',
      'search.clear': 'Clear search',
      'search.results': 'Search results',
      'search.resultCount': '{n} results',
      'search.noMatches': 'No matching sessions',
      'search.empty': 'No sessions yet',
      'section.workspaces': 'Workspaces',
      'group.ungrouped': 'Ungrouped',
      'group.expand': 'Expand workspace',
      'group.collapse': 'Collapse workspace',
      'session.new': 'New Session',
      'session.untitled': 'Untitled',
      'row.pinned': 'Pinned',
      'status.running': 'Running',
      'status.warning': 'Waiting for you',
      'status.done': 'Completed',
      'status.idle': 'Idle',
      'time.now': 'now',
      'time.minutes': '{n}min',
      'time.hours': '{n}h',
      'time.days': '{n}d',
      'time.months': '{n}mo',
      'time.years': '{n}y',
    }

    /* Copied from the host's own chrome so the page reads as one application:
       the row geometry follows ui-workspace's Session rows, the search field
       follows ui-schedule's task search, and every color is a theme token. */
    const CSS = `
.dshp-page {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  box-sizing: border-box;
  color: var(--dsw-alias-label-primary);
  background: var(--dsw-alias-bg-base);
  /* Pin the page's type to the host's own text stack and regular weight: the
     panel must render exactly like the sidebar rows even if a surrounding
     context carries a different inherited family or weight. */
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 14px;
  font-weight: 400;
  font-style: normal;
  font-synthesis: none;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  line-height: 1.6;
}
/* The page carries no bold text: force the regular weight on every descendant
   so no inherited or surrounding rule can render the list heavier than the
   sidebar's own rows. */
.dshp-page,
.dshp-page * { font-weight: 400 !important; }
.dshp-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  scrollbar-gutter: stable;
  --dsh-scrollbar-width: 9px;
  --dsh-scrollbar-thumb-border: 2px;
}
.dshp-content {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 clamp(24px, 4vw, 48px) 48px;
}
@media (max-width: 767px) {
  .dshp-content { padding-inline: 20px; }
}
.dshp-toolbar { padding-top: 20px; margin-bottom: 20px; }
.dshp-search {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  box-sizing: border-box;
  padding: 0 10px;
  border: 0.5px solid var(--dsw-alias-border-l3);
  border-radius: 12px;
  color: var(--dsw-alias-label-tertiary);
  transition: border-color 150ms ease;
}
@media (hover: hover) {
  .dshp-search:hover { border-color: var(--dsw-alias-border-l2); }
}
.dshp-search:focus-within { border-color: var(--dsw-alias-state-business-primary); }
.dshp-search-icon {
  flex: none;
  display: inline-flex;
  width: 16px;
  height: 16px;
  align-items: center;
  justify-content: center;
}
.dshp-search-icon svg { width: 14px; height: 14px; }
.dshp-search-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-family: inherit;
  font-size: 14px;
  line-height: 22px;
  color: var(--dsw-alias-label-primary);
}
.dshp-search-input::placeholder { color: var(--dsw-alias-label-caption); }
.dshp-search-input::-webkit-search-cancel-button { display: none; }
.dshp-search-clear {
  flex: none;
  display: inline-flex;
  width: 28px;
  height: 28px;
  margin-right: -6px;
  padding: 0;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  color: var(--dsw-alias-label-tertiary);
}
@media (hover: hover) {
  .dshp-search-clear:hover {
    background: var(--dsw-alias-interactive-bg-hover);
    color: var(--dsw-alias-label-secondary);
  }
}
.dshp-search-clear svg { width: 14px; height: 14px; }
.dshp-section { display: flex; flex-direction: column; }
.dshp-section-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  height: 28px;
  margin-bottom: 4px;
  color: var(--dsw-alias-label-tertiary);
}
.dshp-section-title { font-size: 14px; line-height: 20px; font-weight: 400; }
.dshp-section-count {
  font-size: 12px;
  line-height: 17px;
  color: var(--dsw-alias-label-caption);
}
.dshp-group-block { display: flex; flex-direction: column; }
.dshp-result-group { display: flex; flex-direction: column; margin-top: 12px; }
.dshp-group,
.dshp-result-group-head {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  height: 34px;
  box-sizing: border-box;
  padding: 0 8px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: var(--dsw-alias-label-primary);
  font-family: inherit;
  font-size: 14px;
  line-height: 20px;
  text-align: left;
}
.dshp-group { cursor: pointer; }
@media (hover: hover) {
  .dshp-group:hover { background: var(--dsw-alias-interactive-bg-hover); }
}
.dshp-glyph {
  flex: none;
  display: inline-flex;
  width: 16px;
  height: 20px;
  align-items: center;
  justify-content: center;
  color: var(--dsw-alias-label-tertiary);
}
.dshp-glyph svg { width: 16px; height: 16px; }
.dshp-folder.is-current { color: var(--dsw-alias-state-business-primary); }
.dshp-chevron { display: none; color: var(--dsw-alias-label-secondary); }
.dshp-chevron svg { width: 12px; height: 12px; transform: rotate(90deg); transition: transform 150ms ease; }
.dshp-group.is-collapsed .dshp-chevron svg { transform: rotate(0deg); }
@media (hover: hover) {
  .dshp-group:hover .dshp-folder { display: none; }
  .dshp-group:hover .dshp-chevron { display: inline-flex; }
}
.dshp-group-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dshp-group-rows { display: flex; flex-direction: column; }
.dshp-row {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  height: 32px;
  box-sizing: border-box;
  padding: 0 8px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: var(--dsw-alias-label-primary);
  font-family: inherit;
  text-align: left;
  cursor: pointer;
}
@media (hover: hover) {
  .dshp-row:hover { background: var(--dsw-alias-interactive-bg-hover); }
}
.dshp-row.is-current { background: var(--dsw-alias-interactive-bg-hover); }
.dshp-row-glyph {
  flex: none;
  display: inline-flex;
  width: 16px;
  height: 20px;
  align-items: center;
  justify-content: center;
  color: var(--dsw-alias-label-tertiary);
}
.dshp-row-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  line-height: 20px;
}
.dshp-row-time {
  flex: none;
  margin-left: 8px;
  font-size: 10px;
  line-height: 16px;
  color: var(--dsw-alias-label-tertiary);
}
.dshp-pin {
  flex: none;
  display: inline-flex;
  width: 16px;
  height: 20px;
  align-items: center;
  justify-content: center;
  margin-left: 6px;
  color: var(--dsw-alias-label-caption);
}
.dshp-pin svg { width: 14px; height: 14px; }
.dshp-dot {
  position: relative;
  display: inline-block;
  flex: none;
  width: 10px;
  height: 10px;
}
.dshp-dot::after {
  content: '';
  position: absolute;
  inset: 20%;
  border-radius: 50%;
  background: currentColor;
}
.dshp-dot[data-state='done'] { color: var(--dsw-alias-state-success-primary); }
.dshp-dot[data-state='warning'] { color: var(--dsw-alias-state-warn-primary); }
.dshp-dot[data-state='error'] { color: var(--dsw-alias-state-error-primary); }
.dshp-dot[data-state='idle'] { color: var(--dsw-alias-state-idle-primary); }
.dshp-spinner { flex: none; color: var(--dsw-alias-label-tertiary); }
.dshp-spinner-motion { transform-origin: center; animation: dshp-spin 1.5s linear infinite; }
.dshp-spinner-track,
.dshp-spinner-arc {
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
}
.dshp-spinner-track { opacity: 0.25; }
.dshp-spinner-arc {
  stroke-dasharray: 12 150;
  animation: dshp-dash 1.5s ease-in-out infinite;
}
@keyframes dshp-spin { to { transform: rotate(360deg); } }
@keyframes dshp-dash {
  0% { stroke-dasharray: 12 150; stroke-dashoffset: 0; }
  50% { stroke-dasharray: 24 150; stroke-dashoffset: -6; }
  100% { stroke-dasharray: 12 150; stroke-dashoffset: 0; }
}
@media (prefers-reduced-motion: reduce) {
  .dshp-spinner-motion,
  .dshp-spinner-arc { animation: none; }
  .dshp-spinner-arc { stroke-dasharray: 18 150; stroke-dashoffset: -3; }
}
.dshp-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 160px;
  padding: 32px 0;
  font-size: 14px;
  line-height: 20px;
  color: var(--dsw-alias-label-tertiary);
}
`

    const MINUTE = 60_000
    const HOUR = 3_600_000
    const DAY = 86_400_000

    /* Host artwork: the 16px folder outlines the sidebar swaps between a
       closed and an open folder, and the search/close outlines of its fields. */
    const FOLDER_CLOSE_PATH = 'M1.50439 3.11059C1.50439 2.55831 1.95211 2.1106 2.50439 2.1106H5.43389C5.67773 2.1106 5.91318 2.19969 6.09593 2.36113L7.71649 3.79265C7.89924 3.95409 8.1347 4.04319 8.3785 4.04319H13.4958C14.0481 4.04319 14.4958 4.4909 14.4958 5.04319V12.8894C14.4958 13.4417 14.0481 13.8894 13.4958 13.8894H2.50439C1.95211 13.8894 1.50439 13.4417 1.50439 12.8894V4.04319V3.11059Z'
    const FOLDER_CLOSE_LINE_PATH = 'M3.63501 7.66614H12.3647'
    const FOLDER_OPEN_BACK_PATH = 'M4.7666 1.90137C5.13227 1.90144 5.48571 2.03525 5.75977 2.27734L7.27246 3.61328C7.36379 3.69382 7.48174 3.73828 7.60352 3.73828H12.3994C13.2276 3.73841 13.8993 4.41005 13.8994 5.23828V6.7168C13.8183 6.70327 13.735 6.69436 13.6494 6.69434H12.8994V5.23828C12.8993 4.96233 12.6754 4.73841 12.3994 4.73828H7.60352C7.23781 4.73828 6.88446 4.60438 6.61035 4.3623L5.09766 3.02637C5.00636 2.94576 4.88838 2.90144 4.7666 2.90137H2.0498C1.77366 2.90137 1.5498 3.12523 1.5498 3.40137V9.78223L0.902344 12.2119C0.648452 13.1642 1.36604 14.0986 2.35156 14.0986H2.0498C1.2214 14.0986 0.549838 13.427 0.549805 12.5986V3.40137C0.549805 2.57294 1.22138 1.90137 2.0498 1.90137H4.7666Z'
    const FOLDER_OPEN_FILL_PATH = 'M2.55912 7.93683C2.67584 7.49906 3.0723 7.19446 3.52536 7.19446H13.6491C14.3061 7.19446 14.7846 7.81725 14.6153 8.45209L13.4411 12.856C13.3244 13.2938 12.9279 13.5984 12.4748 13.5984H2.35113C1.69411 13.5984 1.21562 12.9756 1.38489 12.3407L2.55912 7.93683Z'
    const FOLDER_OPEN_OUTLINE_PATH = 'M13.6491 6.69446C14.6346 6.69453 15.3522 7.62895 15.0983 8.58118L13.9245 12.9845C13.7494 13.6412 13.1539 14.0988 12.4743 14.0988H2.35126C1.36574 14.0988 0.648153 13.1643 0.902044 12.212L2.07587 7.80774C2.25102 7.15128 2.84567 6.69455 3.52509 6.69446H13.6491ZM3.52509 7.69446C3.29865 7.69455 3.10004 7.84674 3.04169 8.06555L1.86786 12.4698C1.78345 12.7872 2.02285 13.0988 2.35126 13.0988H12.4743C12.7007 13.0988 12.8992 12.9463 12.9577 12.7277L14.1325 8.32336C14.2171 8.00598 13.9776 7.69453 13.6491 7.69446H3.52509Z'
    const SEARCH_CIRCLE_PATH = 'M6.58727 11.8586C9.55061 11.8586 11.9529 9.45637 11.9529 6.49304C11.9529 3.5297 9.55061 1.12744 6.58727 1.12744C3.62394 1.12744 1.22168 3.5297 1.22168 6.49304C1.22168 9.45637 3.62394 11.8586 6.58727 11.8586Z'
    const SEARCH_HANDLE_PATH = 'M10.2991 10.3933L14.7783 14.8725'
    const PIN_PATH = 'M9.96976 1.70572L13.1554 3.93629L10.9019 8.12317L11.5158 11.605L10.7192 12.7427L2.52767 7.00693L3.3243 5.86922L6.80612 5.25528L9.96976 1.70572Z'
    const PIN_NEEDLE_PATH = 'M6.05285 9.47511C6.27284 9.16094 6.70586 9.08458 7.02003 9.30457C7.3342 9.52455 7.41055 9.95757 7.19057 10.2717L3.98587 14.4708L3.21223 13.9291L6.05285 9.47511Z'

    /**
     * The plugin's own entry glyph: three ascending bars, the analysis mark
     * the sidebar renders at the size it asks for.
     * @param props.size - square edge in pixels supplied by the sidebar shell.
     * @returns the decorative bar-chart icon.
     */
    function PanelIcon({ size }) {
      const edge = size === undefined ? 16 : size
      return h('svg', {
        width: edge, height: edge, viewBox: '0 0 16 16',
        fill: 'none', 'aria-hidden': 'true', style: { display: 'block' },
      },
      h('rect', { x: 1.75, y: 8.5, width: 2.5, height: 5.75, rx: 1, fill: 'currentColor', opacity: 0.45 }),
      h('rect', { x: 6.75, y: 5.5, width: 2.5, height: 8.75, rx: 1, fill: 'currentColor', opacity: 0.72 }),
      h('rect', { x: 11.75, y: 2.5, width: 2.5, height: 11.75, rx: 1, fill: 'currentColor' }))
    }

    /**
     * Decorative folder outline: the host's closed folder while the workspace
     * is collapsed and its open folder while the workspace is expanded.
     * @param props.open - whether the owning workspace row is expanded.
     */
    function FolderGlyph({ open }) {
      if (open) {
        return h('svg', { viewBox: '0 0 16 16', fill: 'none', 'aria-hidden': 'true', focusable: 'false' },
          h('path', { d: FOLDER_OPEN_FILL_PATH, fill: 'currentColor', opacity: 0.16 }),
          h('path', { d: FOLDER_OPEN_BACK_PATH, fill: 'currentColor' }),
          h('path', { d: FOLDER_OPEN_OUTLINE_PATH, fill: 'currentColor' }))
      }
      return h('svg', { viewBox: '0 0 16 16', fill: 'none', strokeWidth: 1, 'aria-hidden': 'true', focusable: 'false' },
        h('path', { d: FOLDER_CLOSE_PATH, stroke: 'currentColor' }),
        h('path', { d: FOLDER_CLOSE_LINE_PATH, stroke: 'currentColor' }))
    }

    /** Disclosure triangle shown on a hovered workspace row, as in the host. */
    function ChevronGlyph() {
      return h('svg', { viewBox: '0 0 16 16', fill: 'none', 'aria-hidden': 'true', focusable: 'false' },
        h('path', {
          d: 'M5.5 4.5C5.5 4.40714 5.52586 4.31612 5.57467 4.23713C5.62349 4.15815 5.69334 4.09431 5.77639 4.05279C5.85945 4.01126 5.95242 3.99368 6.0449 4.00202C6.13738 4.01036 6.22572 4.04429 6.3 4.1L10.967 7.6C11.0291 7.64657 11.0795 7.70697 11.1142 7.77639C11.1489 7.84582 11.167 7.92238 11.167 8C11.167 8.07762 11.1489 8.15418 11.1142 8.22361C11.0795 8.29303 11.0291 8.35343 10.967 8.4L6.3 11.9C6.22572 11.9557 6.13738 11.9896 6.0449 11.998C5.95242 12.0063 5.85945 11.9887 5.77639 11.9472C5.69334 11.9057 5.62349 11.8419 5.57467 11.7629C5.52586 11.6839 5.5 11.5929 5.5 11.5V4.5Z',
          fill: 'currentColor',
        }))
    }

    /** Decorative pin marker a pinned Session row carries, as in the host. */
    function PinGlyph() {
      return h('svg', { viewBox: '0 0 16 16', fill: 'none', 'aria-hidden': 'true', focusable: 'false' },
        h('path', { d: PIN_PATH, fill: 'currentColor', stroke: 'currentColor', strokeLinejoin: 'round' }),
        h('path', { d: PIN_NEEDLE_PATH, fill: 'currentColor' }))
    }

    /** Decorative search glyph matching the host search fields. */
    function SearchGlyph() {
      return h('svg', { viewBox: '0 0 16 16', fill: 'none', strokeWidth: 1, 'aria-hidden': 'true', focusable: 'false' },
        h('path', { d: SEARCH_CIRCLE_PATH, stroke: 'currentColor' }),
        h('path', { d: SEARCH_HANDLE_PATH, stroke: 'currentColor' }))
    }

    /** Decorative close cross for the search field's clear control. */
    function CloseGlyph() {
      return h('svg', { viewBox: '0 0 16 16', fill: 'none', strokeWidth: 1, 'aria-hidden': 'true', focusable: 'false' },
        h('path', { d: 'M2.5 2.5L13.5 13.5', stroke: 'currentColor' }),
        h('path', { d: 'M13.5 2.5L2.5 13.5', stroke: 'currentColor' }))
    }

    /**
     * Bucket an update instant the way the host sidebar does.
     * @param at - epoch milliseconds of the last update.
     * @param now - epoch milliseconds of the current render.
     * @returns the bucket unit and its count.
     */
    function relativeTime(at, now) {
      const diff = Math.max(0, now - at)
      if (diff < MINUTE) return { unit: 'now', n: 0 }
      if (diff < HOUR) return { unit: 'minutes', n: Math.floor(diff / MINUTE) }
      if (diff < DAY) return { unit: 'hours', n: Math.floor(diff / HOUR) }
      if (diff < 30 * DAY) return { unit: 'days', n: Math.floor(diff / DAY) }
      if (diff < 365 * DAY) return { unit: 'months', n: Math.floor(diff / (30 * DAY)) }
      return { unit: 'years', n: Math.floor(diff / (365 * DAY)) }
    }

    /**
     * Localized compact relative time ("刚刚", "5分钟", "3小时"), as in the sidebar.
     * @param at - epoch milliseconds of the last update.
     * @param now - epoch milliseconds of the current render.
     * @param t - the page's translate function.
     * @returns the display label.
     */
    function timeLabel(at, now, t) {
      const { unit, n } = relativeTime(at, now)
      return unit === 'now' ? t('time.now') : t('time.' + unit, { n })
    }

    /**
     * Row title with the host's blank/unnamed fallbacks.
     * @param summary - Session summary from the list snapshot.
     * @param t - the page's translate function.
     * @returns the display title.
     */
    function sessionTitle(summary, t) {
      if (summary.blank === true) return t('session.new')
      const title = typeof summary.title === 'string' ? summary.title.trim() : ''
      return title === '' ? t('session.untitled') : title
    }

    /**
     * Resolve one row's status presentation from the run-time status snapshot.
     * @param summary - Session summary from the list snapshot.
     * @param status - optional live status for that Session.
     * @returns the state-dot state the host would use.
     */
    function rowState(summary, status) {
      if (status !== undefined && status.running === true) return 'ongoing'
      if (status === undefined && summary.running === true) return 'ongoing'
      if (status !== undefined && status.pendingInteraction !== undefined) return 'warning'
      if (status !== undefined && status.completionUnread === true) return 'done'
      return 'idle'
    }

    /**
     * Render the status mark for one Session row.
     * @param props.state - resolved state-dot state.
     * @returns the mark element.
     */
    function StateMark({ state }) {
      if (state === 'ongoing') {
        return h('svg', {
          className: 'dshp-spinner', width: 14, height: 14, viewBox: '0 0 24 24', 'aria-hidden': 'true',
        }, h('g', { className: 'dshp-spinner-motion' },
          h('circle', { className: 'dshp-spinner-track', cx: 12, cy: 12, r: 9.5 }),
          h('circle', { className: 'dshp-spinner-arc', cx: 12, cy: 12, r: 9.5 })))
      }
      return h('span', { className: 'dshp-dot', 'data-state': state, 'aria-hidden': 'true' })
    }

    /** Directory basename used when a Workspace reports no title. */
    function pathLabel(path) {
      if (typeof path !== 'string' || path === '') return ''
      const parts = path.split(/[\\/]+/u).filter(part => part !== '')
      return parts.length === 0 ? path : parts[parts.length - 1]
    }

    /**
     * Order the rows of one group: the provisional New Session first, then
     * pinned Sessions, then latest update first — the sidebar's own order.
     */
    function orderMembers(members, pinned, archived) {
      return members.slice().sort((left, right) => {
        if (left.blank !== right.blank) return left.blank ? -1 : 1
        const leftPinned = pinned.has(left.id) && !archived.has(left.id) ? 1 : 0
        const rightPinned = pinned.has(right.id) && !archived.has(right.id) ? 1 : 0
        if (leftPinned !== rightPinned) return rightPinned - leftPinned
        if (left.updatedAt !== right.updatedAt) return right.updatedAt - left.updatedAt
        return left.id < right.id ? -1 : left.id > right.id ? 1 : 0
      })
    }

    /**
     * Project the Workspace and Session list snapshots into the grouped
     * browser the page shows for an empty query.
     *
     * Archived and subagent-origin Sessions are hidden exactly as the
     * sidebar hides them by default; only the selected blank Session shows.
     */
    function buildModel(workspaces, sessions, statuses, t) {
      const list = sessions === undefined || sessions === null ? {} : sessions
      const items = workspaces !== undefined && workspaces !== null && Array.isArray(workspaces.items) ? workspaces.items : []
      const archived = new Set(workspaces !== undefined && workspaces !== null ? (workspaces.archivedSessionIds || []) : [])
      const pinned = new Set(workspaces !== undefined && workspaces !== null ? (workspaces.pinnedSessionIds || []) : [])
      const byId = list.byId === undefined ? {} : list.byId
      const ids = Array.isArray(list.ids) ? list.ids : []
      const statusFor = id => (statuses instanceof Map ? statuses.get(id) : undefined)
      const currentBlankId = ids.find((id) => {
        const summary = byId[id]
        return summary !== undefined && summary.blank === true
          && summary.retainedBy !== undefined && (summary.retainedBy.mainView || 0) > 0
      })
      const currentId = ids.find((id) => {
        const summary = byId[id]
        return summary !== undefined
          && summary.retainedBy !== undefined && (summary.retainedBy.mainView || 0) > 0
      })
      const visible = summary => summary !== undefined
        && summary.origin !== 'subagent'
        && !archived.has(summary.id)
        && (summary.blank !== true || summary.id === currentBlankId)
      const toRow = summary => ({
        id: summary.id,
        title: sessionTitle(summary, t),
        blank: summary.blank === true,
        current: summary.id === currentId,
        pinned: pinned.has(summary.id) && !archived.has(summary.id),
        updatedAt: typeof summary.updatedAt === 'number' ? summary.updatedAt : 0,
        state: rowState(summary, statusFor(summary.id)),
      })
      const accounted = new Set()
      const groups = []
      /* The first-use Workspace keeps a language-neutral on-disk name but is
         labeled with the localized default name, exactly as the sidebar does. */
      const defaultWorkspaceTitle = t('workspace.defaultName')
      for (const workspace of items) {
        const members = []
        const sessionIds = Array.isArray(workspace.sessionIds) ? workspace.sessionIds : []
        for (const id of sessionIds) {
          const summary = byId[id]
          if (summary === undefined) continue
          accounted.add(id)
          if (visible(summary)) members.push(summary)
        }
        const rows = orderMembers(members, pinned, archived).map(toRow)
        const rawTitle = (typeof workspace.title === 'string' && workspace.title !== '')
          ? workspace.title
          : pathLabel(workspace.path)
        groups.push({
          key: String(workspace.workspaceId),
          title: rawTitle === 'default-workspace'
            ? defaultWorkspaceTitle
            : (rawTitle || t('group.ungrouped')),
          path: typeof workspace.path === 'string' ? workspace.path : '',
          rows,
          containsCurrent: rows.some(row => row.current),
        })
      }
      const stray = []
      for (const id of ids) {
        const summary = byId[id]
        if (summary === undefined || accounted.has(id) || !visible(summary)) continue
        stray.push(summary)
      }
      if (stray.length > 0) {
        const rows = orderMembers(stray, pinned, archived).map(toRow)
        groups.push({
          key: '',
          title: t('group.ungrouped'),
          path: '',
          rows,
          containsCurrent: rows.some(row => row.current),
        })
      }
      return { groups }
    }

    /**
     * Filter the workspace groups by a lowercased query and keep every match
     * under its own workspace row: session title, workspace title, or Session
     * id substring. Groups without a match disappear.
     * @param groups - the empty-query workspace groups.
     * @param query - lowercased trimmed query.
     * @returns matching groups plus the total number of matched Sessions.
     */
    function searchGroups(groups, query) {
      const matched = []
      let total = 0
      for (const group of groups) {
        const workspaceTitle = group.title.toLowerCase()
        const workspaceMatches = workspaceTitle.includes(query)
        const rows = []
        for (const row of group.rows) {
          /* A blank Session has no durable title, so it never matches a query. */
          if (row.blank) continue
          const title = row.title.toLowerCase()
          const id = String(row.id).toLowerCase()
          if (workspaceMatches || title.includes(query) || id.includes(query)) rows.push(row)
        }
        if (rows.length === 0) continue
        rows.sort((left, right) => right.updatedAt - left.updatedAt)
        total += rows.length
        matched.push({ key: group.key, title: group.title, path: group.path, rows })
      }
      return { groups: matched, total }
    }

    /**
     * Render one workspace row: the host's closed folder while collapsed and
     * its open folder while expanded, or the disclosure triangle on hover.
     */
    function WorkspaceHead({ title, path, open, current, asButton, collapsed, onClick, t }) {
      const content = [
        h('span', {
          className: current ? 'dshp-glyph dshp-folder is-current' : 'dshp-glyph dshp-folder',
          key: 'folder',
        }, h(FolderGlyph, { open })),
        asButton ? h('span', { className: 'dshp-glyph dshp-chevron', key: 'chevron' }, h(ChevronGlyph)) : null,
        h('span', { className: 'dshp-group-title', key: 'title' }, title),
      ]
      if (!asButton) {
        return h('div', { className: 'dshp-result-group-head', title: path === '' ? undefined : path }, content)
      }
      return h('button', {
        type: 'button',
        className: collapsed ? 'dshp-group is-collapsed' : 'dshp-group',
        'aria-expanded': !collapsed,
        'aria-label': t(collapsed ? 'group.expand' : 'group.collapse') + ' ' + title,
        title: path === '' ? undefined : path,
        onClick,
      }, content)
    }

    /** Render one workspace group with its session rows. */
    function WorkspaceGroup({ group, folded, now, t, onToggle, onOpenSession }) {
      const collapsed = folded[group.key] === true
      return h('div', { className: 'dshp-group-block' },
        h(WorkspaceHead, {
          title: group.title,
          path: group.path,
          open: !collapsed,
          current: group.containsCurrent,
          asButton: true,
          collapsed,
          onClick: onToggle,
          t,
        }),
        collapsed ? null : h('div', { className: 'dshp-group-rows' }, group.rows.map(row => h(SessionRow, {
          key: String(row.id), row, now, t, onOpenSession,
        }))))
    }

    /** Render one grouped session row, matching the sidebar's Session row. */
    function SessionRow({ row, now, t, onOpenSession }) {
      return h('button', {
        type: 'button',
        className: row.current ? 'dshp-row is-current' : 'dshp-row',
        'aria-current': row.current ? 'true' : undefined,
        onClick: () => { onOpenSession(row.id) },
      },
      h('span', { className: 'dshp-row-glyph' }, row.blank ? null : h(StateMark, { state: row.state })),
      h('span', { className: 'dshp-row-title' }, row.title),
      /* A blank Session has no first prompt yet, so the sidebar shows neither a
         status cell nor a timestamp for it; only the title row is drawn. */
      row.blank ? null : [
        h('span', { className: 'dshp-row-time', key: 'time' }, timeLabel(row.updatedAt, now, t)),
        row.pinned ? h('span', {
          className: 'dshp-pin', key: 'pin', role: 'img',
          'aria-label': t('row.pinned'), title: t('row.pinned'),
        }, h(PinGlyph)) : null,
      ])
    }

    /**
     * The main panel: the live search field at the top, then the workspace
     * browser (empty query) or the per-workspace search results below it.
     */
    function HotspotsPage(props) {
      const t = props.t
      const workspaces = props.useWorkspaces(snapshot => snapshot)
      const sessions = props.useSessions(snapshot => snapshot)
      const statuses = props.useSessionStatus(snapshot => snapshot)
      const [query, setQuery] = React.useState('')
      const [folded, setFolded] = React.useState({})
      const [now, setNow] = React.useState(() => Date.now())

      React.useEffect(() => {
        const timer = window.setInterval(() => { setNow(Date.now()) }, 60_000)
        return () => { window.clearInterval(timer) }
      }, [])

      const model = React.useMemo(
        () => buildModel(workspaces, sessions, statuses, t),
        [workspaces, sessions, statuses, t],
      )
      const trimmed = query.trim().toLowerCase()
      const results = React.useMemo(
        () => (trimmed === '' ? { groups: [], total: 0 } : searchGroups(model.groups, trimmed)),
        [model, trimmed],
      )
      const toggleGroup = key => {
        setFolded((previous) => {
          const next = { ...previous }
          if (next[key] === true) delete next[key]
          else next[key] = true
          return next
        })
      }
      const onOpenSession = props.onOpenSession

      return h('div', { className: 'dshp-page' },
        h('style', null, CSS),
        h('div', { className: 'dshp-scroll' },
          h('div', { className: 'dshp-content' },
            h('div', { className: 'dshp-toolbar' },
              h('div', { className: 'dshp-search' },
                h('span', { className: 'dshp-search-icon', 'aria-hidden': 'true' }, h(SearchGlyph)),
                h('input', {
                  className: 'dshp-search-input',
                  type: 'search',
                  value: query,
                  placeholder: t('search.placeholder'),
                  'aria-label': t('search.aria'),
                  autoComplete: 'off',
                  spellCheck: false,
                  onChange: (event) => { setQuery(event.currentTarget.value) },
                }),
                query === '' ? null : h('button', {
                  type: 'button',
                  className: 'dshp-search-clear',
                  'aria-label': t('search.clear'),
                  onClick: () => { setQuery('') },
                }, h(CloseGlyph)))),
            trimmed === ''
              ? renderGroups(model, folded, toggleGroup, now, t, onOpenSession)
              : renderResults(results, now, t, onOpenSession))))
    }

    /** Render the empty-query list: workspace groups and their sessions. */
    function renderGroups(model, folded, onToggle, now, t, onOpenSession) {
      if (model.groups.length === 0) return h('div', { className: 'dshp-empty' }, t('search.empty'))
      return h('section', { className: 'dshp-section', 'aria-label': t('section.workspaces') },
        h('div', { className: 'dshp-section-head' },
          h('span', { className: 'dshp-section-title' }, t('section.workspaces'))),
        model.groups.map(group => h(WorkspaceGroup, {
          key: group.key === '' ? 'ungrouped' : group.key,
          group,
          folded,
          now,
          t,
          onToggle: () => { onToggle(group.key) },
          onOpenSession,
        })))
    }

    /**
     * Render the filtered list: each workspace row stays above the matches it
     * owns, so a result always shows which workspace it belongs to.
     */
    function renderResults(results, now, t, onOpenSession) {
      if (results.total === 0) return h('div', { className: 'dshp-empty' }, t('search.noMatches'))
      return h('section', { className: 'dshp-section', 'aria-label': t('search.results') },
        h('div', { className: 'dshp-section-head' },
          h('span', { className: 'dshp-section-title' }, t('search.results')),
          h('span', { className: 'dshp-section-count' }, t('search.resultCount', { n: results.total }))),
        results.groups.map(group => h('div', {
          className: 'dshp-result-group',
          key: group.key === '' ? 'ungrouped' : group.key,
        },
        h(WorkspaceHead, {
          title: group.title,
          path: group.path,
          open: true,
          current: false,
          asButton: false,
          collapsed: false,
          t,
        }),
        h('div', { className: 'dshp-group-rows' }, group.rows.map(row => h(SessionRow, {
          key: String(row.id), row, now, t, onOpenSession,
        }))))))
    }

    return {
      inject: ['slots', 'locale'],
      apply(ctx) {
        ctx.effect(
          () => ctx.locale.register(NS, { zh: ZH, en: EN }),
          'dsh-profiler-hotspots: dictionaries',
        )
        const t = ctx.locale.bind(NS)
        const openSession = (sessionId) => {
          const uiWorkspace = ctx.get('uiWorkspace')
          if (uiWorkspace === undefined || uiWorkspace === null) return
          uiWorkspace.openSession(sessionId)
        }
        ctx.slots.inject('sidebar.panellist', () => ctx.slots.register({
          name: 'sidebar.panellist',
          id: PANEL_ID,
          order: 20,
          locale: NS,
          label: () => t('panel.label'),
        }, PanelIcon))
        ctx.slots.inject('main', () => ctx.slots.register({
          name: 'main',
          key: PANEL_ID,
          locale: NS,
          inject: () => ({ onOpenSession: openSession }),
        }, HotspotsPage))
      },
    }
  },
})
