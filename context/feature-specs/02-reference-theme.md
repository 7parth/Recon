# Reference Theme — Recon UI Design System

> **Source**: Derived from the sample dashboard image provided by the user (Factory AI aesthetic).
> **Style**: Dark, terminal-inspired, monospaced — minimal, data-dense, professional.

---

## 1. Visual Identity

| Attribute    | Value                                                                      |
| ------------ | -------------------------------------------------------------------------- |
| App Name     | **Recon** (displayed as `RECON` — all-caps wordmark, top-left)            |
| Subtitle     | `AI JOB APPLICATION AGENT` — all-caps, monospaced, wide letter-spacing    |
| Overall Mood | Hacker-tool meets professional dashboard — dark, precise, zero decoration |
| Accent       | Orange-red (`#E8471A`) for interactive/status highlights                  |

---

## 2. Color Palette

### Background Hierarchy

| Role                     | Hex       |
| ------------------------ | --------- |
| App background           | `#0A0A0A` |
| Sidebar                  | `#0D0D0D` |
| Card / Panel surface     | `#141414` |
| Card border              | `#1E1E1E` |
| Elevated element (hover) | `#1A1A1A` |

### Text Colors

| Role              | Hex       |
| ----------------- | --------- |
| Primary text      | `#E8E8E8` |
| Secondary text    | `#888888` |
| Tertiary / labels | `#555555` |
| Section headers   | `#666666` |

### Accent / Semantic Colors

| Role                                    | Hex       |
| --------------------------------------- | --------- |
| Primary accent (CTA, active nav, links) | `#E8471A` |
| Success / Applied                       | `#22C55E` |
| Warning / In Review                     | `#F59E0B` |
| Error / Skipped/Failed                  | `#EF4444` |
| Neutral                                 | `#6B7280` |

### Status Badge Styles

| Tag        | Background  | Border/Text    |
| ---------- | ----------- | -------------- |
| APPLIED    | transparent | `#22C55E`      |
| SKIPPED    | transparent | `#EF4444`      |
| IN REVIEW  | transparent | `#F59E0B`      |
| HIGH MATCH | `#E8471A`   | white text     |
| GOOD MATCH | `#1A1A1A`   | `#E8E8E8` text |

---

## 3. Typography

### Font Stack

| Category   | Font             | Fallback                   |
| ---------- | ---------------- | -------------------------- |
| UI / Sans  | `Inter`          | `system-ui, sans-serif`    |
| Monospaced | `JetBrains Mono` | `'Courier New', monospace` |

> **Rule**: All labels, nav sections, table headers, and stat labels use **ALL CAPS + letter-spacing**
> (`text-transform: uppercase; letter-spacing: 0.08em`). Numbers and data values use monospaced font.

### Type Scale

| Token         | Size | Weight | Use                              |
| ------------- | ---- | ------ | -------------------------------- |
| `--text-xs`   | 10px | 400    | Sub-labels, timestamps, run IDs  |
| `--text-sm`   | 11px | 400    | Table data, secondary text       |
| `--text-base` | 13px | 400    | Body, sidebar nav items          |
| `--text-md`   | 14px | 500    | Card body, pipeline step labels  |
| `--text-lg`   | 16px | 600    | Job title, section headers       |
| `--text-xl`   | 20px | 700    | Stat values (e.g., "28", "86")   |
| `--text-2xl`  | 28px | 700    | Page title ("DASHBOARD")         |
| `--text-hero` | 36px | 800    | Match score circle center value  |

---

## 4. Layout & Grid

### Overall Structure

```
+-------------------------------------------------------+
|  TOP NAV BAR  (~52px tall, full width)                |
+----------+--------------------------------------------+
| SIDEBAR  |  MAIN CONTENT AREA                         |
| (220px)  |  (fluid, padding 24-32px)                  |
|          |                                            |
|          |  [ STAT CARDS ROW — 5 equal cards ]        |
|          |                                            |
|          |  [ PIPELINE PANEL (60%) ]  [ RIGHT (40%) ] |
|          |                                            |
|          |  [ RECENT APPLICATIONS TABLE (full width)] |
+----------+--------------------------------------------+
```

### Spacing Scale

| Token       | Value |
| ----------- | ----- |
| `--space-1` | 4px   |
| `--space-2` | 8px   |
| `--space-3` | 12px  |
| `--space-4` | 16px  |
| `--space-5` | 20px  |
| `--space-6` | 24px  |
| `--space-8` | 32px  |

### Border Radius

| Use          | Radius |
| ------------ | ------ |
| Cards/panels | 6px    |
| Badges/tags  | 4px    |
| Buttons      | 4px    |
| Score ring   | 50%    |
| Avatar       | 50%    |

---

## 5. Components

### 5.1 Top Navigation Bar

- Full-width, ~52px tall, `background: #0D0D0D`, bottom border `1px solid #1E1E1E`
- **Left**: Wordmark `RECON` (`Inter 700`, `#E8E8E8`) + subtitle `AI JOB APPLICATION AGENT` (`JetBrains Mono`, 11px, `#555555`, `letter-spacing: 0.12em`)
- **Right**: Bell icon (orange dot badge) + `> RUN NEW PIPELINE` ghost button (monospace, uppercase) + `LOG IN` outlined button

### 5.2 Sidebar

- `220px` wide, `background: #0D0D0D`, right border `1px solid #1E1E1E`
- **Section labels**: 10px, all-caps, `#555555`, `letter-spacing: 0.1em`
- **Nav items**: 13px, `#888888`, `padding: 8px 16px`, `border-radius: 4px`
- **Active item**: `background: #1A1A1A`, left accent border `3px solid #E8471A`, text `#E8E8E8`
- **Hover**: `background: #141414`, text `#C0C0C0`
- **Queue badge**: `background: #E8471A`, white text, `border-radius: 10px`, 10px font, `padding: 2px 6px`
- **Sections**: OVERVIEW / APPLICATIONS / RESUME & PROFILE / JOB DISCOVERY / AUTOMATION / SETTINGS
- **Footer**: Avatar circle (`#E8471A` bg, white initials) + name + email + `...` menu

### 5.3 Stat Cards (5-card row)

- `background: #141414`, `border: 1px solid #1E1E1E`, `border-radius: 6px`, `padding: 16px 20px`
- **Label**: 10px all-caps, `#666666`, `letter-spacing: 0.08em`
- **Value**: 28–32px, `Inter 700`, `#E8E8E8`
- **Sub-label**: 11px, `#555555`
- **Icon**: semantic color, 24px, top-right position
- Cards: Applications / Applied / In Review / Skipped+Failed / Avg. Match Score

### 5.4 Pipeline Progress Stepper

- Horizontal step indicator with connecting lines
- **Completed step**: Green circle + checkmark (`#22C55E`), green connecting line
- **Active step**: Orange circle + icon (`#E8471A`)
- **Pending step**: Gray filled circle (`#333333`), gray connecting line
- **Step label**: 10px, all-caps, `#666666`, centered below node
- Steps: RESUME PARSED → JOB PARSED → COMPANY RESEARCHED → MATCH SCORED → TAILORED RESUME → COVER LETTER → REVIEW → APPLIED → TRACKING

### 5.5 Match Score Ring

- SVG donut, 80–96px diameter, `stroke-width: 6–8px`
- **Track**: `#1E1E1E`
- **Fill**: `#22C55E` (≥90, "Excellent") / `#F59E0B` (70–89, "Good") / `#EF4444` (<70, "Poor")
- **Center**: Score number (`Inter 800`, 28px, `#E8E8E8`) + quality label (10px, `#888888`)

### 5.6 Skill Tags

- `background: #1A1A1A`, `border: 1px solid #2A2A2A`, `border-radius: 4px`
- `font: 11px JetBrains Mono`, `color: #C0C0C0`, `padding: 4px 10px`
- Overflow rendered as `+N more` in identical style

### 5.7 Buttons

| Type       | Style                                                               |
| ---------- | ------------------------------------------------------------------- |
| Primary    | `bg: #E8471A`, white text, `border-radius: 4px`, `Inter 600 13px`  |
| Secondary  | transparent bg, `border: 1px solid #333333`, `color: #E8E8E8`      |
| Ghost/Link | no border/bg, `color: #E8471A`, arrow suffix `→`                   |
| Icon       | 24×24px circle, `bg: #1A1A1A`, icon in `#888888`                   |

### 5.8 Review Queue Cards

- `padding: 12px 16px`, row divider `1px solid #1E1E1E`
- **Logo**: 36px square, `border-radius: 4px` (real brand logo or colored initial avatar)
- **Job title**: `Inter 600`, 13px, `#E8E8E8`
- **Company + location**: 11px, `#888888`
- **Match %**: `Inter 700`, right-aligned, `#E8E8E8`
- **Time ago**: 10px, `#555555`
- **Match badge**: `HIGH MATCH` (orange solid) or `GOOD MATCH` (dark fill)

### 5.9 Data Table (Recent Applications)

- No outer border — horizontal row dividers `1px solid #1E1E1E`
- **Header row**: 10px all-caps, `#555555`, `letter-spacing: 0.08em`, `padding: 8px 0`
- **Data rows**: 13px, `#E8E8E8`, `padding: 12px 0`
- **Status badges**: Outlined — APPLIED=green border+text, SKIPPED=red border+text
- **Row actions**: `...` three-dot menu, right-aligned, `#555555`
- Columns: POSITION / COMPANY / MATCH SCORE / STATUS / APPLIED ON

### 5.10 Activity Timeline

- Vertical timeline, connector line `2px solid #1E1E1E`
- **Node**: 24px circle — green filled (done), orange (active/user action), gray (pending)
- **Title**: `Inter 600`, 13px, `#E8E8E8`
- **Description**: 11px, `#888888`
- **Time ago**: 10px, `#555555`, right-aligned

### 5.11 Inline Status Badge

- `border: 1px solid <semantic-color>`, transparent bg, text matches border color
- `font: 10px JetBrains Mono`, `padding: 3px 8px`, `border-radius: 4px`
- Prepend icon when relevant (clock for IN REVIEW, check for APPLIED, X for SKIPPED)

---

## 6. Iconography

- Library: **Lucide React** (preferred) or Heroicons (stroke-based)
- Sizes: 16px inline / 20px sidebar / 24px stat cards
- Style: `stroke-width: 1.5`, never filled icons
- Color: inherits semantic context or defaults to muted `#888888`

---

## 7. Motion & Interaction

| Interaction        | Behavior                                             |
| ------------------ | ---------------------------------------------------- |
| Nav item hover     | `background` fade-in `100ms ease`                   |
| Button hover       | `opacity: 0.85`, `translateY(-1px)`, `150ms ease`   |
| Card hover         | Border lightens to `#2A2A2A`, `150ms ease`          |
| Score ring         | SVG `stroke-dashoffset` animate on load `600ms ease-out` |
| Pipeline active    | Pulse `box-shadow` animation on active step node    |
| Stat card values   | Count-up number animation on initial page load      |
| Table row hover    | `background: #141414`, `100ms ease`                 |

---

## 8. CSS Design Tokens

```css
:root {
  /* Backgrounds */
  --color-bg-app:      #0A0A0A;
  --color-bg-sidebar:  #0D0D0D;
  --color-bg-card:     #141414;
  --color-bg-elevated: #1A1A1A;

  /* Borders */
  --color-border:       #1E1E1E;
  --color-border-hover: #2A2A2A;

  /* Text */
  --color-text-primary:   #E8E8E8;
  --color-text-secondary: #888888;
  --color-text-tertiary:  #555555;
  --color-text-section:   #666666;

  /* Accents */
  --color-accent:  #E8471A;
  --color-success: #22C55E;
  --color-warning: #F59E0B;
  --color-danger:  #EF4444;

  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Courier New', monospace;

  /* Spacing */
  --space-1: 4px;  --space-2: 8px;   --space-3: 12px;
  --space-4: 16px; --space-5: 20px;  --space-6: 24px;
  --space-8: 32px;

  /* Radius */
  --radius-sm:   4px;
  --radius-md:   6px;
  --radius-full: 9999px;

  /* Layout */
  --sidebar-width: 220px;
  --navbar-height: 52px;

  /* Transitions */
  --transition-fast: 100ms ease;
  --transition-base: 150ms ease;
  --transition-slow: 300ms ease;
}
```

---

## 9. Page Inventory

| Route              | Sidebar Section  | Description                                    |
| ------------------ | ---------------- | ---------------------------------------------- |
| `/`                | Overview         | **Dashboard** — stats, pipeline, review queue  |
| `/activity`        | Overview         | Activity timeline / event log                  |
| `/applications`    | Applications     | All Applications table (full history)          |
| `/review`          | Applications     | Review Queue — approve/reject tailored docs    |
| `/history`         | Applications     | Past applications with status                  |
| `/resumes`         | Resume & Profile | Resume upload and management                   |
| `/profile`         | Resume & Profile | Candidate profile (structured data)            |
| `/keywords`        | Resume & Profile | Skills & Keywords editor                       |
| `/jobs/search`     | Job Discovery    | Job search with criteria                       |
| `/jobs/saved`      | Job Discovery    | Saved / bookmarked listings                    |
| `/automation/ats`  | Automation       | ATS platform configs (Greenhouse, Lever, etc.) |
| `/automation/logs` | Automation       | Playwright run logs                            |
| `/settings`        | Settings         | Preferences (threshold, LLM model, etc.)       |
| `/integrations`    | Settings         | API keys, Supabase config, NVIDIA API key      |

---

## 10. Key UI Rules

1. **No gradients on backgrounds** — pure flat darks only. Gradients only for score ring SVG fill or CTA button hover states.
2. **All-caps + tracking for all labels** — every section header, stat label, table column header uses `text-transform: uppercase; letter-spacing: 0.08em`.
3. **Monospace for IDs, timestamps, and run metadata** — Run IDs, dates, and match percentages always in `JetBrains Mono`.
4. **Orange-red is the only "alive" color** — `#E8471A` reserved for active nav state, CTA buttons, high-match badges, pipeline active node, notification dots. Never use decoratively.
5. **Cards are barely visible** — surfaces are `#141414` against `#0A0A0A`. No drop shadows. Borders `#1E1E1E` carry all visual structure.
6. **Density over whitespace** — information-dense layout. Card padding 12–16px. No empty breathing room.
7. **Status is always a badge** — every item has a visible status badge. Never rely on color alone; always pair with text.
8. **Company logos matter** — use real brand logos (favicons / Clearbit API) where available; fall back to a colored initial-based circle avatar.
