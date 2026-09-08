# URO Research Monitoring System — UI Design Specification

**Version:** 1.0  
**Purpose:** Source-of-truth UI/UX specification for implementation by the coding agent.  
**Reference mockups:** Dashboard, Research Projects, Evaluators screens generated for this project.

---

## 1. Design Direction

The application should feel like a **modern institutional research-management system**, not a public marketing website.

The visual language combines:
- Holy Angel University identity
- Deep maroon institutional branding
- Clean white workspace surfaces
- Warm cream/off-white backgrounds
- Refined serif headings paired with modern sans-serif body text
- Rounded cards with subtle borders and shadows
- Dense but readable dashboard information architecture

The experience should communicate:
- Professionalism
- Academic credibility
- Administrative clarity
- Ease of monitoring research workflows
- Strong visual hierarchy

---

## 2. Brand Assets

### Primary logo
Use the supplied circular Holy Angel University seal:

`logo-circle(1).png`

Preferred placement:
- Left sidebar, top center
- Approximately 96–112 px diameter on desktop
- Never stretch or distort
- Maintain clear space of at least 16 px around logo

### Brand name block
Below logo:

**URO**  
Research Monitoring System  
Holy Angel University

Alignment: centered in sidebar.

---

## 3. Color System

### Primary colors

| Token | Value | Usage |
|---|---:|---|
| `--uro-maroon-900` | `#5A0E16` | Sidebar base, dark headers |
| `--uro-maroon-800` | `#6E101C` | Sidebar gradients |
| `--uro-maroon-700` | `#7E1320` | Primary action backgrounds |
| `--uro-maroon-600` | `#941A29` | Hover / active |
| `--uro-maroon-500` | `#A92A38` | Accents, active menu highlight |
| `--uro-rose-100` | `#F8EAEC` | Soft accent backgrounds |
| `--uro-cream-50` | `#FCFAF7` | App canvas |
| `--uro-white` | `#FFFFFF` | Cards / panels |
| `--uro-charcoal` | `#1E1E24` | Main text |
| `--uro-gray-700` | `#525866` | Secondary text |
| `--uro-gray-500` | `#8B919E` | Muted text |
| `--uro-gray-300` | `#D9DDE4` | Borders |
| `--uro-gray-100` | `#F2F4F7` | Soft panel backgrounds |

### Semantic colors

| Token | Value | Meaning |
|---|---:|---|
| `--status-success` | `#1F8F5F` | Completed / approved / available |
| `--status-warning` | `#D99A22` | Pending / due soon |
| `--status-danger` | `#C1434D` | Revision / overdue / failed |
| `--status-info` | `#3E7CC4` | Under evaluation / submitted |
| `--status-purple` | `#7D57B8` | IRB review / special stage |
| `--status-neutral` | `#8C96A3` | Draft / inactive |

### Background gradient for sidebar

```css
background: linear-gradient(180deg, #6E101C 0%, #5A0E16 55%, #3E0B10 100%);
```

---

## 4. Typography

### Heading font
Use a refined serif font:
- `Playfair Display`
- fallback: `Georgia, serif`

Used for:
- Large screen titles
- Section titles
- Hero text
- Major card titles

### UI font
Use a modern sans-serif:
- `Inter`
- fallback: `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`

Used for:
- Navigation
- Forms
- Tables
- Buttons
- Metrics
- Labels

### Suggested sizes

| Style | Size | Weight | Line height |
|---|---:|---:|---:|
| Hero title | 42–52 px | 700 | 1.05 |
| Page title | 36–44 px | 700 | 1.1 |
| Section title | 20–24 px | 700 | 1.25 |
| Card title | 16–18 px | 650 | 1.3 |
| Body | 14–15 px | 400 | 1.5 |
| Small label | 12–13 px | 500 | 1.4 |
| Metric number | 30–36 px | 700 | 1.1 |

---

## 5. App Shell

### Desktop layout

- Fixed left sidebar: **240–260 px**
- Main content area: flexible width
- Max content width: ~1600 px
- Top utility bar: **64 px**
- Page padding: **20–24 px**
- Vertical spacing between sections: **16–20 px**

```text
┌───────────────┬──────────────────────────────────────────────────────────┐
│               │ Top Utility Bar                                          │
│   Sidebar     ├──────────────────────────────────────────────────────────┤
│               │ Hero / Page Header                                       │
│               ├──────────────────────────────────────────────────────────┤
│               │ Quick Actions                                             │
│               ├──────────────────────────────────────────────────────────┤
│               │ Metrics / Filters / Tables / Analytics                    │
└───────────────┴──────────────────────────────────────────────────────────┘
```

### Sidebar

Contains:
1. Logo
2. URO name block
3. Navigation menu
4. Decorative campus image/texture toward bottom
5. Motto block: `VIRTUS · SCIENTIA · CARITAS`

#### Navigation items

Recommended order:
- Dashboard
- Research
- Submissions
- Researchers
- Evaluators
- IRB
- Turnitin
- Monitoring
- Reports
- Resources
- Settings

#### Active state

```css
background: rgba(189, 52, 67, 0.55);
border-radius: 10px;
color: #fff;
```

Icon + label aligned horizontally, 14–16 px gap.

---

## 6. Top Utility Bar

Height: 56–64 px.

### Left
Global search:
- Placeholder contextual to screen
- Rounded 10–12 px
- 1 px neutral border
- Search icon left
- Optional shortcut hint `Ctrl + K`

### Right
- Notification icon with badge
- User avatar/initials
- User name
- User role
- Dropdown chevron

Use white background and no heavy shadow.

---

## 7. Hero / Page Header

Each primary module may use a short visual banner.

### Style
- Height: 150–175 px
- Background: HAU campus imagery with dark maroon overlay on left, warm fade to right
- Border radius: 12 px
- Large serif page title
- Supporting sentence below
- Optional quote or institution statement aligned right

### Examples

Dashboard:
- `Welcome, Dr. Tayag!`
- `Monitor. Support. Advance Research.`

Research:
- `Research Projects`
- `Manage. Monitor. Support. Advance Research.`

Evaluators:
- `Evaluators`
- `Manage research evaluators and evaluation assignments.`

---

## 8. Card System

### Base card

```css
background: #fff;
border: 1px solid #E5E7EB;
border-radius: 12px;
box-shadow: 0 2px 8px rgba(24, 24, 27, 0.04);
```

### Hoverable card

```css
transition: 160ms ease;
```

Hover:
- translateY(-1px)
- subtle shadow increase
- maroon border tint for clickable cards

---

## 9. Quick Action Cards

Horizontal row directly under hero.

Each action:
- 150–210 px wide depending viewport
- 86–100 px height
- Icon above or left
- Short title
- Optional description

Primary action uses solid maroon background and white text.
Secondary actions use pale neutral/rose surfaces.

Example Dashboard actions:
- New Submission
- Assign Evaluator
- Check Turnitin
- IRB Review
- Blind Evaluation
- Generate Reports

---

## 10. KPI / Metric Cards

Structure:
- Small icon badge
- Large numeric value
- Label
- Supporting change percentage or ratio

Examples:
- Total Projects
- Ongoing
- For Evaluation
- For Revision
- Completed
- Total Evaluators
- Active Evaluators
- Pending Assignments
- Completed Reviews

Use semantic color wash backgrounds, not saturated fills.

---

## 11. Tables

### Visual style

- White card container
- Compact header row
- Header text 12–13 px semibold
- Row height ~42–46 px
- Light separators
- Hover row: `#FAF7F5`
- Sticky header for long tables
- Rightmost actions menu using ellipsis

### Typical columns — Research
- #
- Research Code
- Title
- Researcher(s)
- College
- Type
- Status
- Date Submitted
- Evaluator
- Actions

### Typical columns — Evaluators
- #
- Name
- Expertise
- College / Department
- Email
- Active Assignments
- Avg. Rating
- Availability
- Actions

---

## 12. Status Chips

Use compact pills with a colored dot or soft-fill background.

Examples:

```text
● Ongoing
● Under Evaluation
● For Revision
● IRB Review
● Turnitin Checked
● Completed
● Pending
● Overdue
```

Pill style:

```css
font-size: 12px;
padding: 4px 8px;
border-radius: 999px;
font-weight: 500;
```

---

## 13. Filters

Filters should appear as a horizontal bar above list/table views.

Recommended controls:
- Academic Year
- College
- Research Type
- Status
- Search input

Each select/input:
- height 40–42 px
- radius 8–10 px
- white background
- subtle border

On smaller screens, wrap filters into multiple rows.

---

## 14. Dashboard Screen Specification

### Sections

1. Top utility bar
2. Welcome hero
3. Quick actions
4. Research Projects Overview KPI block
5. Upcoming Deadlines panel
6. Research Status donut chart
7. Research by College bar chart
8. Recent Activities
9. Recent Submissions table

### Main desktop grid

```text
[ Overview / KPIs -------------------------- ] [ Deadlines ]
[ Research Status ] [ Research by College ]   [ Activity  ]
[ Recent Submissions ------------------------------------- ]
```

### Recommended breakpoints
- ≥1440: 12-column layout
- 1024–1439: 8-column layout
- 768–1023: collapse sidebar to icons/drawer
- <768: single column

---

## 15. Research Screen Specification

### Goal
Primary operational view for managing all research projects.

### Sections
1. Research hero
2. Action toolbar
   - New Submission
   - Import
   - Filter
   - Export
3. KPI cards
4. Filter bar
5. Research Projects table
6. Right-side contextual panel
   - Project Pipeline donut
   - Recent Submissions
   - Selected Project Preview

### Selected project preview
Should display:
- Research code
- Title
- Researcher
- College
- Type
- Evaluator
- Current status chip
- Timeline / progress stages
- Buttons: View Full Details, Add Note

### Project workflow stages
Use a horizontal timeline:

```text
Submitted → Turnitin → Evaluation → IRB Review → Final Decision
```

Support additional stages in actual system:

```text
Initial Submission
→ Screening
→ Turnitin
→ Evaluation
→ Revision if needed
→ IRB (if applicable)
→ Research Implementation
→ Final Paper
→ Turnitin
→ Blind Final Evaluation
→ Completed
→ Presentation / Publication Ready
```

---

## 16. Evaluator Screen Specification

### Goal
Manage evaluator registry, availability, workload, and assignments.

### Sections
1. Evaluators hero
2. Action toolbar
   - Add Evaluator
   - Assign Evaluation
   - Bulk Invite
   - Export List
3. KPI cards
4. Evaluator Directory table
5. Right-side Evaluator Profile panel
6. Evaluation Assignments table
7. Workload by Expertise chart
8. Recent Evaluator Activity

### Evaluator profile panel
Should show:
- Photo/avatar
- Name
- Academic rank/title
- College/department
- Email
- Active status
- Active assignments
- Average rating
- Completed reviews
- Research interests as chips
- Qualifications

### Assignment states
- Pending
- Accepted
- Ongoing
- Submitted
- Overdue
- Completed
- Declined

---

## 17. Evaluation UX Rules

1. Evaluator identity must remain hidden from researchers during blind evaluation.
2. URO administrators can see assignment identities.
3. Selective re-evaluation is supported when only one evaluator fails a final paper.
4. Re-evaluation should be assigned only to the evaluator who issued the failing decision, unless overridden by an authorized admin.
5. Final completion occurs only after the final blind evaluation passes.

---

## 18. IRB Screen Direction

Follow the same application shell.

Suggested widgets:
- Total applications
- Pending review
- Revisions required
- Approved
- Upcoming meetings
- Protocol list
- Reviewer assignment
- Decision history

Main table columns:
- IRB Code
- Research Title
- Principal Researcher
- Submission Date
- Review Type
- Assigned Reviewers
- Status
- Meeting Date
- Actions

---

## 19. Turnitin Screen Direction

Suggested screen sections:
- Pending similarity checks
- Checked today
- Requires revision
- Cleared
- Similarity threshold settings
- Recent reports

Each record should show:
- Research code
- Title
- Researcher
- Submission version
- Similarity score
- Date checked
- Result
- Report action

Color behavior:
- Green = acceptable
- Amber = attention
- Red = exceeds threshold

---

## 20. Monitoring Screen Direction

Focus on research implementation progress.

Suggested metrics:
- Active studies
- On schedule
- Delayed
- Deliverables due
- Completed milestones

Main views:
- Project progress cards
- Timeline
- Milestone checklist
- Compliance status
- Document submission history
- Remarks / notes

---

## 21. Forms & Modals

Use modals for:
- Add evaluator
- Assign evaluator
- Create research project
- Confirm destructive actions
- Set status
- Add note / comment

### Modal style
- Width 520–720 px
- Rounded 14 px
- Large title
- Short helper text
- Clear form grouping
- Footer actions aligned right

Primary button: maroon
Secondary: white with neutral border
Destructive: red

---

## 22. Buttons

### Primary

```css
background: #7E1320;
color: white;
border-radius: 9px;
height: 40px;
padding: 0 16px;
font-weight: 600;
```

Hover: `#941A29`

### Secondary
White background, gray border, dark text.

### Ghost
No fill, maroon text.

### Icon buttons
36–40 px square, rounded 8 px.

---

## 23. Icons

Recommended icon library:
- Lucide React
- Heroicons

Do not mix icon families in the same interface.

Use 18–20 px for navigation and buttons.
Use 22–28 px for action cards and KPI badges.

---

## 24. Spacing Scale

Use 4 px base rhythm:

```text
4, 8, 12, 16, 20, 24, 32, 40, 48, 64
```

Common application values:
- Sidebar menu gap: 6–8 px
- Card padding: 16–20 px
- Section gap: 16–20 px
- Page padding: 20–24 px

---

## 25. Border Radius

```text
Inputs/buttons: 8–10 px
Cards: 12 px
Hero: 12 px
Modal: 14 px
Pills: 999 px
```

Avoid overly rounded “consumer app” styling.

---

## 26. Shadows

Keep shadows subtle.

```css
--shadow-card: 0 2px 8px rgba(24, 24, 27, 0.04);
--shadow-hover: 0 6px 20px rgba(24, 24, 27, 0.08);
--shadow-modal: 0 24px 64px rgba(0,0,0,0.18);
```

---

## 27. Responsive Behavior

### Desktop
Full fixed sidebar and multi-column dashboards.

### Tablet
- Sidebar collapses to icon rail or drawer
- Right-side contextual panels move below tables
- KPI cards wrap into 2 columns

### Mobile
- Single-column layout
- Top app bar with menu button
- Hide decorative hero quote
- Tables become cards or horizontally scroll
- Filters collapse behind Filter button
- Quick actions use 2-column grid

---

## 28. Accessibility

Implementation must include:
- WCAG AA contrast where practical
- Visible keyboard focus rings
- Accessible labels for inputs/icons
- Do not communicate status only by color
- Minimum 40 px interaction target
- Logical tab order
- Semantic headings
- ARIA labels for icon-only controls

---

## 29. Suggested Frontend Stack

Preferred implementation pattern:
- React or Next.js
- Tailwind CSS
- shadcn/ui for form primitives, dialogs, dropdowns, tables
- Lucide React icons
- Recharts for analytics

The design should be implemented as reusable components rather than page-specific hardcoded blocks.

---

## 30. Reusable Component Inventory

Coding agent should create at minimum:

```text
AppShell
Sidebar
TopBar
PageHero
QuickActionCard
MetricCard
StatusBadge
DataTable
FilterBar
SectionCard
DonutChartCard
BarChartCard
ActivityList
DeadlineList
ProjectPreviewPanel
EvaluatorProfilePanel
ProgressTimeline
ModalForm
EmptyState
LoadingSkeleton
ConfirmDialog
```

---

## 31. Suggested Token File

```css
:root {
  --uro-maroon-900: #5A0E16;
  --uro-maroon-800: #6E101C;
  --uro-maroon-700: #7E1320;
  --uro-maroon-600: #941A29;
  --uro-maroon-500: #A92A38;
  --uro-rose-100: #F8EAEC;
  --uro-cream-50: #FCFAF7;
  --uro-white: #FFFFFF;
  --uro-charcoal: #1E1E24;
  --uro-gray-700: #525866;
  --uro-gray-500: #8B919E;
  --uro-gray-300: #D9DDE4;
  --uro-gray-100: #F2F4F7;

  --status-success: #1F8F5F;
  --status-warning: #D99A22;
  --status-danger: #C1434D;
  --status-info: #3E7CC4;
  --status-purple: #7D57B8;
  --status-neutral: #8C96A3;

  --radius-control: 9px;
  --radius-card: 12px;
  --radius-modal: 14px;

  --shadow-card: 0 2px 8px rgba(24, 24, 27, 0.04);
  --shadow-hover: 0 6px 20px rgba(24, 24, 27, 0.08);
}
```

---

## 32. Coding Agent Guardrails

The coding agent must follow these rules:

1. **Do not redesign the visual identity.** Follow this specification and the supplied mockups.
2. Keep the left maroon sidebar as the primary navigation pattern.
3. Use the supplied circular HAU logo.
4. Keep pages application-oriented, not public-website-oriented.
5. Preserve serif headings + sans-serif UI text.
6. Do not introduce bright gradients, neon colors, glassmorphism, or excessive animation.
7. Keep cards compact and information-dense.
8. Reuse components across modules.
9. Ensure all tables, filters, modals, and forms follow the same design system.
10. Maintain consistent semantic status colors across the entire app.
11. Every new module should inherit the same shell, spacing, tokens, typography, and card system.
12. Desktop implementation should closely match the reference mockups before responsive adaptations are added.

---

## 33. Reference Screens

Use these images as visual references during implementation:

- `university_research_monitoring_dashboard.png`
- `research_projects_dashboard.png`
- `holy_angel_university_evaluators_dashboard.png`
- `logo-circle(1).png`

The mockups are visual direction; this specification defines the reusable implementation rules.

---

## 34. Definition of Done for UI Implementation

A screen is considered visually complete when:
- It uses the standard app shell
- Sidebar, top bar, hero, cards, tables, and controls match the design system
- Responsive layout works at desktop/tablet/mobile breakpoints
- Empty/loading/error states are styled consistently
- Statuses use approved semantic colors
- Typography and spacing are consistent
- No public-site navigation pattern is introduced
- The screen visually belongs to the same product as the Dashboard, Research, and Evaluator reference screens

