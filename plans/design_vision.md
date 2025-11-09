# Note-Taking App - Design Vision

## Core Philosophy
**Focus-first, keyboard-driven, distraction-free note capture** with intelligent organization happening in the background.

---

## Layout Architecture

### Three-Column Layout (Responsive & Collapsible)

```
┌────────────┬─────────────────────────────┬────────────────┐
│  Projects  │      Focus Mode (Default)   │    Context     │
│  & Tags    │                             │   (Smart AI)   │
│            │  ┌─────────────────────┐    │                │
│  240px     │  │   NEW NOTE FORM     │    │    420px       │
│ (toggle    │  │                     │    │  (toggle ⌘/)   │
│  with ⌘B)  │  │   [Always visible]  │    │                │
│            │  │                     │    │  - Related     │
│  • Work    │  └─────────────────────┘    │    notes       │
│  • Personal│                             │  - Wiki-links  │
│  • Ref...  │  Recent Notes (scroll)      │  - AI tags     │
│            │  ─────────────────────      │  - Suggestions │
│            │  [Note 1]                   │                │
│  #tags     │  [Note 2]                   │                │
│  #python   │  [Note 3]                   │                │
│  #meeting  │  ...                        │                │
└────────────┴─────────────────────────────┴────────────────┘
```

---

## Left Sidebar (240px)

### Projects Section
- **Color-coded dots** for visual distinction
- **Note count** next to each project (e.g., "Work • 48")
- **"All Notes"** as default/home view
- Clicking filters the main view without hiding the form
- Recently used projects float to top

**Example:**
```
PROJECTS
─────────
● All Notes          142
● Work               48
● Personal           67  
● Reference          27
+ New Project
```

### Tags Section (Bottom)
- **Popular tags as pills** (most-used tags)
- Clicking filters notes by tag
- Tag cloud style: larger = more used
- Can click multiple tags (AND/OR toggle)

**Example:**
```
POPULAR TAGS
────────────
[python] [meeting] [idea]
[design] [api] [research]
[book] [draft]
```

### Behavior
- **Collapsible** with `⌘B`
- Remembers state (local storage)
- Smooth slide animation (200ms)
- On mobile: overlay that slides from left

---

## Center Panel - Focus Mode (680px)

### New Note Form (Always First)

**Header:**
```
New Note                                    ⌘N
```

**Metadata Row (Inline):**
```
[Work ▼]  [Note ▼]  [Add tags...]
  140px     120px       356px
```

**Content Area:**
```
┌──────────────────────────────────────────┐
│ Start writing...                         │
│                                          │
│                                          │
│ [Large textarea - 520px height]         │
│                                          │
│                                          │
│                                          │
│                                0 words   │
└──────────────────────────────────────────┘
```

**Action Bar:**
```
Markdown supported: **bold** *italic* [[wiki-link]] #tag

○ [[Link to note    ○ Attach file    ○ AI classify

                              [Cancel] [Save Note]
```

**Recent Notes Hint:**
```
─────────────────────────────────────────────────
↓ Recent notes below (scroll or Tab+S to browse)
```

### Form Behavior

**Auto-expand on focus:**
- Form compact when empty (300px height)
- Expands to 520px when typing
- Smooth transition

**Smart defaults:**
- Project: Last used or "All Notes"
- Type: "Note" default
- Tags: Auto-suggest from existing
- Timestamp: Auto-generated on save

**Keyboard shortcuts:**
- `⌘N` - Focus form from anywhere
- `⌘Enter` - Save note
- `Esc` - Clear/reset form
- `Tab + S` - Switch to search/browse mode

**Auto-save:**
- LocalStorage every 30 seconds
- Recovery on crash/reload
- Visual indicator: "Unsaved changes •"

### Recent Notes List (Below Form)

**Infinite scroll display:**
```
─────────────────────────────────────────────────
[Note Title]                    2 hours ago • Work
First line of content appears here as preview...
#python #api #meeting

[Another Note]                  Yesterday • Personal  
Preview text of this note appears here...
#idea #draft

[Older Note]                    3 days ago • Work
Yet another preview...
#reference

[Load more...]
```

**Each note card shows:**
- Title (first line or explicit)
- Time ago + Project
- Preview (2 lines max)
- Tags
- Hover: Edit/Delete buttons appear

**Click behavior:**
- **Click card** → Form morphs to show that note for editing
- **⌘Click** → Open in new window/tab
- **Swipe left** (mobile) → Delete

---

## Right Sidebar - Context Panel (420px)

### Related Notes (Dynamic)
Auto-updates as you type based on:
- **Wiki-links** you've added `[[like this]]`
- **Semantic similarity** (if embeddings enabled)
- **Same tags** mentioned
- **Same project** context

**Display:**
```
CONTEXT
───────
Related notes will appear here

[○ Meeting notes from...]
   Similar topics discussed
   2 days ago

[○ API design thoughts]
   Linked via [[project-name]]
   Last week

[○ Python reference]
   Shares tags: #python #api
   3 weeks ago
```

### AI Suggestions

**Suggested Tags:**
```
SUGGESTED TAGS
──────────────
[api +] [backend +] [fastapi +]
```
- Click `+` to add to note
- Based on content analysis
- Updates as you type

**Related Concepts:**
```
You might also want to note:
• Error handling patterns
• Authentication flow
• Database schema
```

### Behavior
- **Collapsible** with `⌘/`
- Appears automatically when:
  - You type a wiki-link
  - Similar notes found
  - AI has suggestions
- Otherwise hidden by default (clean focus)

---

## View Modes (Subtle Toggle)

### Focus Mode (Default)
- Large form prominent
- Recent notes scrollable below
- Both sidebars visible (or last state)
- **This is where you land every time**

### Browse Mode (`Tab + S`)
- Form shrinks to compact top bar
- Notes list expands to fill space
- Grid or list view toggle
- Search bar prominent

### Project View (Click project)
- Form stays visible at top
- Notes filtered to project
- Breadcrumb: `Project > All Notes`
- Can still create notes in this project

### Tag View (Click tag)
- Form stays visible at top
- Notes filtered by tag(s)
- Multi-select tags with AND/OR
- Tag combination breadcrumb

**Key principle:** Form never disappears completely. It just scales based on context.

---

## Keyboard Navigation

### Global Shortcuts
```
⌘N        Focus new note form
⌘B        Toggle left sidebar
⌘/        Toggle right sidebar
⌘K        Quick search (command palette)
Esc       Clear form / Exit mode
Tab+S     Switch to browse mode
⌘Enter    Save current note
```

### Navigation
```
↑↓        Navigate note list
Enter     Edit selected note
Delete    Delete selected note (confirm)
⌘↑        Jump to top
⌘↓        Jump to bottom
```

### Form
```
Tab       Next field
⌘1-9      Quick project select
#tag      Auto-complete tags
[[        Auto-complete note links
```

---

## Progressive Disclosure

### Basic Form (Default)
```
[Project ▼] [Type ▼] [Tags...]
─────────────────────────────
Content here...
─────────────────────────────
           [Cancel] [Save]
```

### Advanced Form (Click "+" or `⌘Shift+A`)
```
[Project ▼] [Type ▼] [Tags...]

Custom Fields:
├─ Due Date: [____]
├─ Priority: [Low ▼]
├─ Assigned: [____]
└─ URL: [____]
─────────────────────────────
Content here...
─────────────────────────────
           [Cancel] [Save]
```

Only show complexity when needed.

---

## Smart Form Behavior

### Auto-completion

**Project dropdown:**
- Recently used first
- Color coding maintained
- Type to filter
- Create new inline: "+ Create 'ProjectName'"

**Tags input:**
- Autocomplete from existing tags
- Shows tag frequency
- Comma/space separated
- Create new tags on-the-fly

**Wiki-links `[[...]]`:**
- Fuzzy search existing notes
- Show previews on hover
- Create new note if not found

### Title Generation
- **No explicit title field** (less friction)
- First line becomes title
- Or extracted from `# Heading` in markdown
- Or "Untitled note" with timestamp

### Timestamp Intelligence
- Created: Auto on save
- Modified: Auto on edit
- Displayed as "2 hours ago" (human readable)
- Hover shows exact timestamp

---

## Visual Design Principles

### Typography
```
Headings:   16px, semibold, #111827
Body text:  14px, regular, #374151
Meta text:  12px, regular, #6b7280
Code:       'SF Mono', 13px, #1f2937
```

### Color System
```
Projects:
  Work       → #3b82f6 (blue)
  Personal   → #8b5cf6 (purple)
  Reference  → #f59e0b (amber)
  
States:
  Focus      → #10b981 (green accent)
  Unsaved    → #ef4444 (red dot)
  Saved      → #6b7280 (gray check)
  
Backgrounds:
  Primary    → #ffffff (white)
  Secondary  → #f9fafb (gray-50)
  Hover      → #f3f4f6 (gray-100)
```

### Spacing
- Base unit: 4px
- Form padding: 20px
- Element spacing: 12px
- Section spacing: 24px

### Animations
```
Sidebar toggle:     200ms ease-in-out
Form expand:        300ms ease
Dropdown open:      150ms ease-out
Note card hover:    100ms ease
Save success:       Subtle fade + check (500ms)
```

---

## Additional UI Elements

### Top Bar (Optional)
```
[≡ Menu]  Notes          [Search...]  [⚙️ Settings]  [👤 User]
```
- Minimal, unobtrusive
- Search always accessible
- User menu: Logout, preferences

### Status Indicators
```
● Unsaved changes
✓ Saved 2 seconds ago
↻ Syncing...
⚠ Sync failed (retry)
```

### Empty States
```
No notes yet in this project.

[+ Create your first note]
```

### Loading States
```
[○○○ Loading notes...]
[Skeleton cards appear]
```

---

## Mobile Adaptations

### Responsive Breakpoints
```
Desktop:  > 1024px  → Three columns
Tablet:   768-1024  → Center + one sidebar (toggle)
Mobile:   < 768px   → Center only (sidebars overlay)
```

### Mobile-Specific
- Swipe gestures (left = delete, right = star)
- Bottom nav bar (New | Browse | Search | More)
- Floating action button (+ for new note)
- Pull-to-refresh

---

## Advanced Features (Phase 2)

### Search Bar
```
⌘K → [Search notes, tags, projects...]

Fuzzy search with:
  - Content search
  - Tag search (#python)
  - Project search (@work)
  - Date search (>2024-01-01)
  - Combined queries
```

### Quick Actions
```
⌘K → Type action:
  - "new note in work"
  - "find python notes"
  - "show recent"
  - "export to pdf"
```

### Batch Operations
- Select multiple notes
- Bulk tag
- Bulk move to project
- Bulk export

### Note Linking Graph
- Visualize connections
- Click to navigate
- Zoom in/out
- Filter by project

---

## Accessibility

### Screen Readers
- Proper ARIA labels
- Semantic HTML
- Keyboard navigation
- Focus indicators

### Contrast
- WCAG AA minimum
- High contrast mode option
- Color blind friendly

### Keyboard Only
- All features accessible
- Visible focus states
- Skip navigation links

---

## The Experience

**Opening the app:**
1. You see: Large form, clean, inviting
2. Cursor auto-focuses in content area
3. Context sidebar hidden until relevant
4. You just start typing

**Creating a note:**
1. Type content (form expands smoothly)
2. Add tags inline with `#`
3. Change project if needed (dropdown)
4. Hit `⌘Enter` or click Save
5. Form clears, new note appears at top of list
6. Continue without interruption

**Finding a note:**
1. Scroll recent list, or
2. Click project filter, or
3. Click tag, or
4. Use `⌘K` quick search
5. Form always visible for new thoughts

**Editing a note:**
1. Click note card
2. Form morphs to show that note
3. Edit inline
4. Save with `⌘Enter`
5. Back to fresh form automatically

**No mode switches. No dialogs. No friction.**

---

## Implementation Notes

### HTMX Patterns Used
- Form submissions (hx-post)
- Infinite scroll (hx-trigger="revealed")
- Search (hx-get with debounce)
- Delete (hx-delete with confirm)
- Partial updates (hx-swap strategies)

### Alpine.js Components
- Dropdown state
- Tag autocomplete
- Form validation
- Loading indicators
- Modal dialogs (if needed)

### Tailwind Classes
- Utility-first styling
- Responsive modifiers
- Dark mode variants
- Transition classes

---

## Design Mantras

1. **Note creation is primary** - Form never hides
2. **Zero mode switches** - Everything accessible
3. **Keyboard > Mouse** - But both work great
4. **Intelligence in background** - AI suggests, doesn't interrupt
5. **Files are truth** - UI is just a nice interface
6. **Fast feels smart** - Instant feedback, async intelligence
7. **Beautiful minimalism** - Clean, focused, delightful

---

The goal is **the fastest path from thought to saved note**, with smart organization emerging naturally from your patterns, not forced through rigid structures.
