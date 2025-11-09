# Design Implementation Plan
## Three-Column Focus-First Interface

Based on `design_vision.md` and `layout.svg`, this plan transforms the current two-column layout into a sophisticated, keyboard-driven, mobile-responsive interface.

---

## Implementation Strategy

**Approach**: Incremental refactor with backwards compatibility
- Keep existing CRUD logic intact
- Transform templates and add new UI components
- Add responsive CSS with mobile-first approach
- Layer in keyboard shortcuts progressively
- Test at each phase on both desktop and mobile

---

## Phase 1: Foundation & Layout Architecture
**Goal**: Establish three-column responsive grid with collapsible sidebars

### 1.1 Responsive Grid System
- [ ] Create CSS grid layout with three columns
  - Left: `240px` (projects/tags sidebar)
  - Center: `680px` (focus mode panel)
  - Right: `420px` (context sidebar)
  - Total: `1340px` + gaps
- [ ] Define responsive breakpoints:
  - Desktop: `>1024px` → Three columns
  - Tablet: `768-1024px` → Center + one sidebar (toggleable)
  - Mobile: `<768px` → Center only (sidebars as overlays)
- [ ] Add CSS variables for consistent spacing:
  ```css
  --sidebar-left-width: 240px;
  --panel-center-width: 680px;
  --sidebar-right-width: 420px;
  --gap: 20px;
  ```

### 1.2 Sidebar State Management (Alpine.js)
- [ ] Create global Alpine store for UI state:
  ```javascript
  Alpine.store('ui', {
    leftSidebarOpen: true,
    rightSidebarOpen: false,
    viewMode: 'focus' // 'focus' | 'browse'
  })
  ```
- [ ] LocalStorage persistence for sidebar states
- [ ] Transition animations (200ms ease-in-out)

### 1.3 Base Template Structure
- [ ] Update `base.html` with new grid structure:
  ```html
  <div class="app-container" x-data>
    <aside class="sidebar-left" x-show="$store.ui.leftSidebarOpen">
      {% block sidebar_left %}{% endblock %}
    </aside>
    <main class="panel-center">
      {% block panel_center %}{% endblock %}
    </main>
    <aside class="sidebar-right" x-show="$store.ui.rightSidebarOpen">
      {% block sidebar_right %}{% endblock %}
    </aside>
  </div>
  ```

### 1.4 Mobile Overlay Implementation
- [ ] Left sidebar as slide-in overlay on mobile
- [ ] Right sidebar as slide-in overlay on mobile
- [ ] Touch gesture handlers (swipe to close)
- [ ] Backdrop/overlay for sidebar focus

**Testing**:
- Resize browser from 320px to 1440px
- Toggle sidebars on each breakpoint
- Verify state persistence on reload
- Test on iOS Safari and Chrome mobile

---

## Phase 2: Left Sidebar - Projects & Tags
**Goal**: Color-coded projects list and tag cloud with filtering

### 2.1 Projects Section
- [ ] Create `partials/projects-list.html`:
  - App title/logo at top
  - "PROJECTS" section header
  - Project items with:
    - Color-coded dots (CSS custom properties)
    - Project name
    - Note count (right-aligned)
  - "All Notes" as default view
  - "+ New Project" action
- [ ] Project color system:
  ```css
  --project-work: #3b82f6;      /* blue */
  --project-personal: #8b5cf6;   /* purple */
  --project-reference: #f59e0b;  /* amber */
  --project-default: #6b7280;    /* gray */
  ```
- [ ] Backend: Add endpoint `/projects` returning:
  ```json
  [
    {"name": "All Notes", "count": 142, "color": "default"},
    {"name": "Work", "count": 48, "color": "work"},
    ...
  ]
  ```
- [ ] HTMX filtering: `hx-get="/notes?project={name}"`
- [ ] Active state styling (highlight selected project)

### 2.2 Tags Section (Bottom of Sidebar)
- [ ] Create `partials/tags-cloud.html`:
  - "POPULAR TAGS" header
  - Tag pills sorted by usage frequency
  - Responsive tag sizing (larger = more used)
- [ ] Backend: Update `/api/tags` to return counts:
  ```json
  [
    {"name": "python", "count": 45},
    {"name": "meeting", "count": 32},
    ...
  ]
  ```
- [ ] Multi-tag selection:
  - Click tag to filter (adds to query)
  - AND/OR toggle (Alpine state)
  - Visual indication of selected tags
- [ ] HTMX: `hx-get="/notes?tags=python,meeting&op=and"`

### 2.3 Sidebar Toggle & Keyboard Shortcuts
- [ ] Toggle button (hamburger icon) for mobile
- [ ] Keyboard shortcut `⌘B` (Cmd+B or Ctrl+B):
  ```javascript
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
      e.preventDefault();
      Alpine.store('ui').leftSidebarOpen = !Alpine.store('ui').leftSidebarOpen;
    }
  });
  ```
- [ ] Smooth slide animation with CSS transitions
- [ ] Remember state across sessions (localStorage)

**Testing**:
- Click project → verify notes filter
- Click multiple tags → verify AND/OR logic
- Toggle sidebar with `⌘B`
- Test on mobile (overlay behavior)
- Verify note counts update after CRUD operations

---

## Phase 3: Center Panel - Focus Mode (Form)
**Goal**: Auto-expanding form that's always visible and keyboard-friendly

### 3.1 New Note Form - Structure
- [ ] Create `partials/note-form.html`:
  - Header: "New Note" with `⌘N` hint
  - Metadata row (inline, 3 fields)
  - Large content textarea
  - Word count indicator
  - Action buttons (Save, Cancel)
  - Formatting hints
  - Quick actions bar

### 3.2 Metadata Row (Inline)
- [ ] Project dropdown (140px):
  - Recently used first
  - Color-coded dots
  - Type to filter (Alpine.js)
  - "+ Create new" inline
- [ ] Type dropdown (120px):
  - Note, Task, Reference, Meeting, etc.
  - Default: "Note"
- [ ] Tags input (356px):
  - Autocomplete from existing tags
  - Comma/space separated
  - Show tag frequency in dropdown
  - Create new tags on-the-fly

### 3.3 Content Textarea - Auto-expanding
- [ ] Initial height: 300px (compact)
- [ ] Expands to 520px on focus/typing
- [ ] Smooth transition (300ms ease)
- [ ] Alpine.js state tracking:
  ```javascript
  {
    formExpanded: false,
    wordCount: 0,
    hasUnsavedChanges: false
  }
  ```
- [ ] Word count: Real-time update on input
- [ ] Placeholder: "Start writing..."

### 3.4 Auto-save & Recovery
- [ ] LocalStorage auto-save every 30 seconds:
  ```javascript
  setInterval(() => {
    if (this.hasUnsavedChanges) {
      localStorage.setItem('note-draft', JSON.stringify({
        content: this.content,
        project: this.project,
        tags: this.tags,
        timestamp: Date.now()
      }));
    }
  }, 30000);
  ```
- [ ] Recovery on page load:
  - Check for draft
  - Show "Restore draft?" prompt
  - Clear draft on successful save
- [ ] Visual indicator: "Unsaved changes •" (red dot)

### 3.5 Action Buttons & Quick Actions
- [ ] Primary button: "Save Note" (blue, ⌘Enter)
- [ ] Secondary button: "Cancel" (gray, Esc)
- [ ] Quick actions bar:
  - `[[Link to note` → Trigger wiki-link autocomplete
  - `Attach file` → File upload (future)
  - `AI classify` → Auto-tag suggestion (future)
- [ ] Formatting hints: "Markdown supported: **bold** *italic* [[wiki-link]] #tag"

### 3.6 Keyboard Shortcuts for Form
- [ ] `⌘N` → Focus form from anywhere
- [ ] `⌘Enter` → Save note
- [ ] `Esc` → Clear/reset form
- [ ] `Tab` → Navigate between fields
- [ ] `⌘1-9` → Quick project select
- [ ] `#tag` → Auto-complete tags
- [ ] `[[` → Auto-complete note links

### 3.7 Form Behavior - Edit Mode
- [ ] Click note card → Form morphs to edit mode:
  - Pre-fill all fields
  - Change header to "Edit Note"
  - Change button to "Update Note"
  - Show "Delete" button (red, right-aligned)
- [ ] After save → Reset to "New Note" mode automatically
- [ ] Smooth transition between modes (no jarring switches)

**Testing**:
- Type in textarea → verify auto-expand
- Fill form and wait → verify auto-save
- Reload page → verify draft recovery
- Press `⌘Enter` → verify save
- Press `Esc` → verify form clears
- Click existing note → verify edit mode
- Test all keyboard shortcuts
- Test on mobile (touch-friendly inputs)

---

## Phase 4: Center Panel - Recent Notes List
**Goal**: Scrollable list of recent notes below the form

### 4.1 Recent Notes Display
- [ ] Create `partials/note-card.html`:
  - Title (bold, 16px)
  - Meta line: "2 hours ago • Work" (gray, 12px)
  - Preview (2 lines max, truncated)
  - Tags (pills)
  - Hover: Show Edit/Delete buttons
- [ ] Divider above list: "↓ Recent notes below (scroll or Tab+S to browse)"
- [ ] Infinite scroll with HTMX:
  ```html
  <div hx-get="/notes?offset=20"
       hx-trigger="revealed"
       hx-swap="afterend">
  ```
- [ ] Initial load: 20 notes
- [ ] Load more: +20 on scroll to bottom

### 4.2 Time Display
- [ ] Human-readable time: "2 hours ago", "Yesterday", "3 days ago"
- [ ] JavaScript function:
  ```javascript
  function timeAgo(timestamp) {
    // Implementation using Intl.RelativeTimeFormat
  }
  ```
- [ ] Hover: Show exact timestamp tooltip

### 4.3 Click Behavior
- [ ] Click card → Load into form for editing
- [ ] HTMX: `hx-get="/notes/{id}/edit"` → Swap into form
- [ ] Smooth scroll to form on mobile
- [ ] `⌘Click` → Open in new tab (future enhancement)

### 4.4 Hover Actions
- [ ] CSS: Show action buttons on hover
- [ ] Edit button (blue)
- [ ] Delete button (red, with confirmation)
- [ ] Mobile: Swipe left to reveal actions

**Testing**:
- Scroll to bottom → verify infinite load
- Hover note card → verify actions appear
- Click note → verify form populates
- Delete note → verify confirmation
- Test time display for various dates
- Test on mobile (swipe gestures)

---

## Phase 5: Right Sidebar - Context Panel
**Goal**: Smart context with related notes, wiki-links, and AI suggestions

### 5.1 Related Notes Section
- [ ] Create `partials/context-panel.html`:
  - "CONTEXT" header
  - Related notes list (initially empty)
  - Placeholder: "Related notes will appear here"
- [ ] Backend: `/api/context?note_id={id}` returns:
  ```json
  {
    "wiki_links": [...],
    "related": [...],
    "suggested_tags": [...]
  }
  ```
- [ ] Update context as user types (debounced):
  - Extract wiki-links from content
  - Find notes with same tags
  - Semantic similarity (if embeddings enabled)
- [ ] HTMX: `hx-get="/api/context" hx-trigger="input delay:500ms"`

### 5.2 Wiki-Links Display
- [ ] Show extracted wiki-links from current note
- [ ] Click → Scroll to linked note (if in list)
- [ ] Click → Search/load note (if not visible)
- [ ] Show backlinks count: "3 notes link here"
- [ ] Visual: Purple accent for wiki-link items

### 5.3 AI Tag Suggestions
- [ ] "SUGGESTED TAGS" section
- [ ] Display tags with `+` button
- [ ] Click `+` → Add to tags input
- [ ] Backend: Simple keyword extraction initially
  ```python
  def suggest_tags(content: str) -> List[str]:
      # Extract keywords, compare to existing tags
      # Return top 3-5 suggestions
  ```
- [ ] Future: Use embeddings for smarter suggestions

### 5.4 Sidebar Auto-show Logic
- [ ] Hidden by default (clean focus)
- [ ] Auto-show when:
  - User types `[[wiki-link]]`
  - Related notes found (>2 results)
  - AI has tag suggestions
- [ ] Keyboard shortcut `⌘/` to toggle
- [ ] Remember manual toggle state (don't auto-show if manually closed)

### 5.5 Collapsible Behavior
- [ ] Toggle button (top-right of panel)
- [ ] Slide out to right (200ms transition)
- [ ] localStorage persistence
- [ ] Mobile: Overlay from right

**Testing**:
- Type wiki-link → verify sidebar appears
- Verify related notes update
- Click suggested tag → verify added to form
- Toggle with `⌘/`
- Test auto-show logic
- Test on mobile overlay

---

## Phase 6: Visual Design System
**Goal**: Implement Tailwind-inspired color system and typography

### 6.1 Color System (CSS Variables)
```css
:root {
  /* Projects */
  --color-work: #3b82f6;
  --color-personal: #8b5cf6;
  --color-reference: #f59e0b;

  /* States */
  --color-focus: #10b981;
  --color-unsaved: #ef4444;
  --color-saved: #6b7280;

  /* Backgrounds */
  --bg-primary: #ffffff;
  --bg-secondary: #f9fafb;
  --bg-hover: #f3f4f6;

  /* Text */
  --text-primary: #111827;
  --text-secondary: #374151;
  --text-tertiary: #6b7280;

  /* Borders */
  --border-light: #e5e7eb;
  --border-medium: #d1d5db;
}
```

### 6.2 Typography System
```css
/* Headings */
h1, .text-lg { font-size: 16px; font-weight: 600; color: var(--text-primary); }
h2, .text-md { font-size: 15px; font-weight: 600; color: var(--text-primary); }

/* Body */
.text { font-size: 14px; color: var(--text-secondary); }
.text-sm { font-size: 12px; color: var(--text-tertiary); }
.text-xs { font-size: 11px; color: var(--text-tertiary); }

/* Code */
code, .code { font-family: 'SF Mono', 'Monaco', monospace; font-size: 13px; }
```

### 6.3 Spacing System
```css
/* Base unit: 4px */
.spacing-xs { margin: 4px; }
.spacing-sm { margin: 8px; }
.spacing-md { margin: 12px; }
.spacing-lg { margin: 16px; }
.spacing-xl { margin: 24px; }
```

### 6.4 Animations & Transitions
```css
/* Sidebar toggle */
.sidebar-left, .sidebar-right {
  transition: transform 200ms ease-in-out;
}

/* Form expand */
.note-form textarea {
  transition: height 300ms ease;
}

/* Dropdown open */
.dropdown {
  transition: opacity 150ms ease-out;
}

/* Note card hover */
.note-card {
  transition: all 100ms ease;
}

/* Save success */
@keyframes save-success {
  0% { opacity: 0; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.05); }
  100% { opacity: 1; transform: scale(1); }
}
```

### 6.5 Component Styling
- [ ] Buttons: Rounded (4px), shadow on hover
- [ ] Inputs: Border (1px), focus ring (3px rgba)
- [ ] Cards: Border (1px), shadow (subtle)
- [ ] Tags: Pill shape (border-radius: 12px)
- [ ] Dropdowns: Shadow, border, max-height with scroll

**Testing**:
- Verify color consistency across all components
- Test animations on all transitions
- Verify hover states
- Test focus states (keyboard navigation)
- Dark mode colors (future phase)

---

## Phase 7: Keyboard Navigation System
**Goal**: Implement comprehensive keyboard shortcuts

### 7.1 Global Shortcuts Handler
```javascript
// Create global keyboard handler
const shortcuts = {
  'cmd+n': () => focusNewNote(),
  'cmd+b': () => toggleLeftSidebar(),
  'cmd+/': () => toggleRightSidebar(),
  'cmd+k': () => openCommandPalette(),
  'escape': () => clearFormOrExitMode(),
  'cmd+enter': () => saveCurrentNote()
};

document.addEventListener('keydown', (e) => {
  const key = (e.metaKey || e.ctrlKey ? 'cmd+' : '') +
               (e.shiftKey ? 'shift+' : '') +
               e.key.toLowerCase();

  if (shortcuts[key]) {
    e.preventDefault();
    shortcuts[key]();
  }
});
```

### 7.2 Note List Navigation
- [ ] `↑↓` → Navigate note list (Alpine focus tracking)
- [ ] `Enter` → Edit selected note
- [ ] `Delete` → Delete selected note (with confirmation)
- [ ] `⌘↑` → Jump to top
- [ ] `⌘↓` → Jump to bottom
- [ ] Visual focus indicator (blue border)

### 7.3 Form Navigation
- [ ] `Tab` → Next field (natural tab order)
- [ ] `Shift+Tab` → Previous field
- [ ] `⌘1-9` → Quick project select
- [ ] Tag autocomplete on `#`
- [ ] Wiki-link autocomplete on `[[`

### 7.4 Command Palette (`⌘K`)
- [ ] Fuzzy search modal overlay
- [ ] Search across:
  - Note content
  - Tags (`#python`)
  - Projects (`@work`)
  - Commands (actions)
- [ ] Keyboard navigation (↑↓, Enter)
- [ ] Recent searches
- [ ] Quick actions: "new note in work", "export to pdf"

### 7.5 Visual Hints
- [ ] Show keyboard shortcuts in UI:
  - "New Note" → `⌘N` (gray, right-aligned)
  - Buttons → `⌘Enter` on hover
  - Tooltips for actions
- [ ] "Keyboard shortcuts" help panel (toggle with `?`)

**Testing**:
- Test every shortcut combination
- Verify no conflicts with browser shortcuts
- Test on Windows (Ctrl) and Mac (Cmd)
- Verify focus indicators visible
- Test command palette fuzzy search

---

## Phase 8: Mobile Adaptations
**Goal**: Touch-friendly, mobile-optimized experience

### 8.1 Mobile Layout
- [ ] Center panel takes full width (`<768px`)
- [ ] Left sidebar as slide-in overlay (from left)
- [ ] Right sidebar as slide-in overlay (from right)
- [ ] Backdrop when sidebar open (semi-transparent black)
- [ ] Touch to close backdrop

### 8.2 Touch Gestures
- [ ] Swipe right → Open left sidebar
- [ ] Swipe left → Close left sidebar
- [ ] Swipe left on note card → Show delete button
- [ ] Pull-to-refresh → Reload notes list
- [ ] Implement with Hammer.js or native touch events

### 8.3 Mobile Navigation
- [ ] Bottom navigation bar (sticky):
  - New (+ icon, blue)
  - Browse (list icon)
  - Search (magnifying glass icon)
  - More (three dots)
- [ ] Floating action button (FAB) for "New Note" (bottom-right)
- [ ] TAP to focus form
- [ ] Form slides up from bottom (mobile modal style)

### 8.4 Mobile Form Behavior
- [ ] Form opens as bottom sheet (slide up animation)
- [ ] Full-screen on focus (maximize writing space)
- [ ] Close button (X, top-right)
- [ ] Auto-focus content textarea on open
- [ ] Virtual keyboard pushes content up (not covered)

### 8.5 Mobile-Specific Optimizations
- [ ] Larger touch targets (min 44x44px)
- [ ] Sticky form header (stays visible on scroll)
- [ ] Simplified metadata row (stacked instead of inline)
- [ ] Reduced animations for performance
- [ ] Progressive Web App (PWA) manifest

### 8.6 Tablet Layout (768-1024px)
- [ ] Two-column: Center + one sidebar
- [ ] Toggle between left/right sidebar
- [ ] Larger touch targets than desktop
- [ ] iPad split-view support

**Testing**:
- Test on iPhone (multiple sizes)
- Test on Android (multiple sizes)
- Test on iPad
- Test landscape and portrait
- Test touch gestures
- Test virtual keyboard behavior
- Test PWA install

---

## Phase 9: Advanced Features
**Goal**: Polish and power-user features

### 9.1 Search & Filters
- [ ] Search bar in top header
- [ ] Debounced search (300ms)
- [ ] Filter by:
  - Date range (">2024-01-01", "last week")
  - Tags (multiple, AND/OR)
  - Projects
  - Content (full-text)
- [ ] Combined queries: "@work #python >yesterday"
- [ ] Save searches (bookmarked filters)

### 9.2 Browse Mode (`Tab+S`)
- [ ] Form shrinks to compact top bar
- [ ] Notes list expands to fill space
- [ ] Grid view option (3-4 columns)
- [ ] List view (default)
- [ ] Sort options: Recent, Alphabetical, Modified
- [ ] Bulk select (checkboxes appear)

### 9.3 Bulk Operations
- [ ] Select multiple notes (Shift+Click)
- [ ] Bulk tag
- [ ] Bulk move to project
- [ ] Bulk delete (with confirmation)
- [ ] Bulk export

### 9.4 Export Options
- [ ] Export single note (Markdown, PDF, HTML)
- [ ] Export project (ZIP of markdown files)
- [ ] Export all notes (ZIP)
- [ ] Backend: Use `markdown2pdf` library for PDF

### 9.5 Note Linking Graph (Future)
- [ ] D3.js force-directed graph
- [ ] Nodes = notes
- [ ] Edges = wiki-links
- [ ] Click node → Navigate to note
- [ ] Filter by project/tag
- [ ] Zoom in/out

**Testing**:
- Test all search combinations
- Test browse mode toggle
- Test bulk operations
- Verify export formats
- Test graph visualization

---

## Phase 10: Performance & Polish
**Goal**: Optimize, test, and polish

### 10.1 Performance Optimizations
- [ ] Lazy load notes (virtualized scrolling)
- [ ] Debounce all search/filter inputs
- [ ] Cache frequently accessed notes
- [ ] Optimize index rebuilds (only on change)
- [ ] Minimize HTMX re-renders (use OOB swaps)

### 10.2 Loading States
- [ ] Skeleton cards while loading
- [ ] Loading spinner for slow operations
- [ ] Progress bar for file uploads
- [ ] Optimistic UI updates (update before save completes)

### 10.3 Error Handling
- [ ] Toast notifications for errors
- [ ] Inline validation for forms
- [ ] Retry failed requests
- [ ] Offline detection and warning

### 10.4 Accessibility (a11y)
- [ ] Semantic HTML (nav, main, aside, article)
- [ ] ARIA labels for all interactive elements
- [ ] Keyboard navigation (focus visible)
- [ ] Screen reader announcements
- [ ] Color contrast (WCAG AA)
- [ ] Focus trap in modals
- [ ] Skip navigation links

### 10.5 Empty States
- [ ] "No notes yet" → Illustration + CTA
- [ ] "No search results" → Suggestions
- [ ] "No tags" → Guide on how to add tags
- [ ] "No projects" → Create first project

### 10.6 Testing Checklist
- [ ] Browser testing: Chrome, Firefox, Safari, Edge
- [ ] Mobile testing: iOS Safari, Chrome Android
- [ ] Keyboard-only navigation test
- [ ] Screen reader test (VoiceOver, NVDA)
- [ ] Performance test (Lighthouse, Core Web Vitals)
- [ ] Responsive test (all breakpoints)
- [ ] Load test (1000+ notes)

**Testing**:
- Run full regression test suite
- Test with real data (import notes)
- Performance profiling
- Accessibility audit
- Cross-browser testing

---

## Implementation Order & Timeline

### Quick Win (Week 1)
- Phase 1: Layout architecture (desktop only)
- Phase 2: Left sidebar (projects/tags)
- Phase 3: Basic center form (no auto-expand yet)

### Core Functionality (Week 2)
- Phase 3: Form auto-expand and auto-save
- Phase 4: Recent notes list
- Phase 6: Visual design system

### Intelligence (Week 3)
- Phase 5: Right sidebar (context panel)
- Wiki-links integration (use existing Phase 4 code)
- Tag suggestions

### Power Features (Week 4)
- Phase 7: Keyboard navigation
- Phase 9: Search and filters
- Phase 9: Browse mode

### Mobile & Polish (Week 5)
- Phase 8: Mobile adaptations
- Phase 10: Performance and polish
- Phase 10: Accessibility

---

## Testing Strategy

### Unit Tests
- Backend: Test all API endpoints
- Frontend: Test Alpine.js components
- Utility functions (timeAgo, autocomplete, etc.)

### Integration Tests
- HTMX interactions (form submit, infinite scroll)
- Keyboard shortcuts
- Sidebar state management

### E2E Tests (Playwright)
- Create note flow
- Edit note flow
- Delete note flow
- Search and filter
- Mobile gestures

### Manual Testing
- Cross-browser (Chrome, Firefox, Safari, Edge)
- Mobile devices (iOS, Android)
- Keyboard-only navigation
- Screen reader testing

---

## Migration Notes

### From Current to New Design
1. Keep existing routes and backend logic
2. Gradually replace templates:
   - `index.html` → New three-column layout
   - `partials/` → New components
3. Preserve all existing functionality
4. Add new features incrementally
5. No breaking changes to data format

### Data Compatibility
- Existing markdown files work as-is
- Indexes continue to work
- Wiki-links already implemented (Phase 4)
- Tags and projects already supported

### Backwards Compatibility
- Old templates can coexist (feature flag)
- Allow toggle between "Classic" and "Focus" UI
- Smooth transition for users

---

## Success Metrics

### User Experience
- Time to create note: < 5 seconds (from thought to saved)
- Keyboard efficiency: All actions accessible without mouse
- Mobile usability: Touch-friendly, no pinch-zoom needed
- Search speed: < 200ms for 1000 notes

### Technical
- Lighthouse score: > 90
- First Contentful Paint: < 1.5s
- Time to Interactive: < 3s
- Accessibility score: 100

### Quality
- Zero layout shifts (CLS: 0)
- Smooth animations (60fps)
- No console errors
- WCAG AA compliant

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Set up feature flag** for new UI (toggle in settings)
3. **Start with Phase 1** (layout foundation)
4. **Test continuously** at each phase
5. **Iterate based on feedback**

---

**Philosophy**: This redesign maintains the "mean and lean" principle while adding sophisticated UX. Every feature serves the core goal: **fastest path from thought to saved note**.
