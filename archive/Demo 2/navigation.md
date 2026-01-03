# Navigation Components

**Component Category:** Core
**Document Version:** 1.0

Navigation components provide wayfinding and orientation throughout the Glintstone platform. These components adapt to user tier and context while maintaining consistent patterns.

**Design Principles:**
- Consistent location across contexts
- Clear current location indication
- Progressive complexity by user tier
- Mobile-first responsive patterns
- Keyboard fully navigable

---

## Header

### Purpose and Use Cases

Header provides global navigation, branding, and user actions. Present on all authenticated pages and the marketing page.

### Anatomy

```
Desktop:
+------------------------------------------------------------------+
| [Logo: Glintstone]   Contribute  Explore  Learn  [Search] [User] |
+------------------------------------------------------------------+

Mobile:
+------------------------------------------------------------------+
| [Menu]        [Logo: Glintstone]                    [Search]     |
+------------------------------------------------------------------+
```

### HTML Structure

```html
<header class="header" role="banner">
  <!-- Skip link (first focusable element) -->
  <a href="#main-content" class="skip-link">
    Skip to main content
  </a>

  <div class="header__container">
    <!-- Logo/Home link -->
    <a href="/" class="header__logo" aria-label="Glintstone home">
      <svg aria-hidden="true"><!-- Logo SVG --></svg>
      <span class="header__wordmark">Glintstone</span>
    </a>

    <!-- Primary navigation -->
    <nav class="header__nav" aria-label="Main navigation">
      <ul class="header__nav-list" role="list">
        <li>
          <a href="/contribute" class="nav-item" aria-current="page">
            Contribute
          </a>
        </li>
        <li>
          <a href="/explore" class="nav-item">
            Explore
          </a>
        </li>
        <li>
          <a href="/learn" class="nav-item">
            Learn
          </a>
        </li>
        <!-- Expert-only item (conditionally rendered) -->
        <li data-tier="expert">
          <a href="/review" class="nav-item">
            Review
          </a>
        </li>
      </ul>
    </nav>

    <!-- Actions -->
    <div class="header__actions">
      <!-- Search -->
      <button
        type="button"
        class="header__search-toggle"
        aria-label="Open search"
        aria-expanded="false"
        aria-controls="search-panel"
      >
        <svg aria-hidden="true"><!-- search icon --></svg>
      </button>

      <!-- User menu (authenticated) -->
      <div class="header__user">
        <button
          type="button"
          class="header__user-toggle"
          aria-label="User menu"
          aria-expanded="false"
          aria-haspopup="menu"
        >
          <span class="header__avatar">
            <img src="avatar.jpg" alt="">
            <span class="header__avatar-fallback">JS</span>
          </span>
        </button>

        <div class="header__user-menu" role="menu" hidden>
          <a href="/profile" role="menuitem">Profile</a>
          <a href="/settings" role="menuitem">Settings</a>
          <hr role="separator">
          <button type="button" role="menuitem">Sign out</button>
        </div>
      </div>

      <!-- Sign in (unauthenticated) -->
      <a href="/sign-in" class="button" data-variant="primary">
        Sign in
      </a>
    </div>

    <!-- Mobile menu toggle -->
    <button
      type="button"
      class="header__mobile-toggle"
      aria-label="Open menu"
      aria-expanded="false"
      aria-controls="mobile-nav"
    >
      <svg aria-hidden="true"><!-- hamburger icon --></svg>
    </button>
  </div>
</header>
```

### Variants

| Variant | Context | Differences |
|---------|---------|-------------|
| default | App pages | Full navigation |
| marketing | Landing page | Simplified, prominent CTA |
| minimal | Task flow | Logo only, exit action |

### States

| State | Description |
|-------|-------------|
| default | Normal display |
| scrolled | Sticky after scroll (optional shadow) |
| mobile-open | Mobile menu expanded |
| search-open | Search panel expanded |

### Navigation by User Tier

| Nav Item | Passerby | Early Learner | Expert |
|----------|----------|---------------|--------|
| Contribute | Quick tasks | Task queue + transcription | + Review |
| Explore | Featured | Full archive | + Publication pipeline |
| Learn | Teaser | Full curriculum | "Teach" mode |
| Review | Hidden | Hidden | Visible |
| Profile | Hidden | Basic | Full |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-variant | string | Header variant |
| data-tier | string | Current user tier |
| data-authenticated | boolean | User signed in |
| data-transparent | boolean | Transparent background |

### Accessibility

- Skip link as first focusable element
- Proper landmark role (banner)
- ARIA labels on all interactive elements
- Menu follows ARIA menu pattern
- Focus trapped in open menus
- Escape closes menus

---

## NavItem

### Purpose and Use Cases

NavItem is a single navigation link within any navigation context.

### Anatomy

```
[Icon] Label [Badge]
```

### HTML Structure

```html
<!-- Standard nav item -->
<a href="/contribute" class="nav-item">
  <svg class="nav-item__icon" aria-hidden="true">
    <!-- icon -->
  </svg>
  <span class="nav-item__label">Contribute</span>
</a>

<!-- Nav item with badge -->
<a href="/review" class="nav-item" aria-current="page">
  <svg class="nav-item__icon" aria-hidden="true">
    <!-- icon -->
  </svg>
  <span class="nav-item__label">Review</span>
  <span class="nav-item__badge" aria-label="8 pending reviews">8</span>
</a>

<!-- Nav item (button variant) -->
<button type="button" class="nav-item" aria-expanded="false">
  <svg class="nav-item__icon" aria-hidden="true">
    <!-- icon -->
  </svg>
  <span class="nav-item__label">More</span>
  <svg class="nav-item__chevron" aria-hidden="true">
    <!-- chevron -->
  </svg>
</button>
```

### States

| State | Description | Visual |
|-------|-------------|--------|
| default | Inactive | Standard text |
| hover | Mouse over | Subtle background |
| focus | Keyboard focus | Focus ring |
| active | Being pressed | Darker background |
| current | Current page | Bold, indicator |
| disabled | Not available | Muted, no interaction |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| aria-current | string | "page" for current |
| data-badge | string | Badge content |
| data-icon | string | Icon name |

### Accessibility

- Use aria-current="page" for current page
- Badge has aria-label for context
- Keyboard navigable (Tab)
- Focus visible

---

## Breadcrumb

### Purpose and Use Cases

Breadcrumb shows the user's location in the site hierarchy. Use for:
- Deep navigation (tablet detail page)
- Multi-step flows
- Archive exploration

### Anatomy

```
Home / Explore / Tablets / YBC 4644
```

### HTML Structure

```html
<nav class="breadcrumb" aria-label="Breadcrumb">
  <ol class="breadcrumb__list">
    <li class="breadcrumb__item">
      <a href="/" class="breadcrumb__link">Home</a>
      <span class="breadcrumb__separator" aria-hidden="true">/</span>
    </li>
    <li class="breadcrumb__item">
      <a href="/explore" class="breadcrumb__link">Explore</a>
      <span class="breadcrumb__separator" aria-hidden="true">/</span>
    </li>
    <li class="breadcrumb__item">
      <a href="/explore/tablets" class="breadcrumb__link">Tablets</a>
      <span class="breadcrumb__separator" aria-hidden="true">/</span>
    </li>
    <li class="breadcrumb__item" aria-current="page">
      <span class="breadcrumb__current">YBC 4644</span>
    </li>
  </ol>
</nav>
```

### Variants

| Variant | Display |
|---------|---------|
| default | Full path |
| collapsed | ...middle items collapsed |
| mobile | Back arrow + parent only |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-items | string | JSON path array |
| data-collapse-at | number | Items before collapse |

### Accessibility

- Uses nav landmark with aria-label
- Ordered list semantics
- aria-current="page" on last item
- Separators are decorative (aria-hidden)

---

## TabGroup

### Purpose and Use Cases

TabGroup provides tabbed navigation within a page section. Use for:
- Content organization (tablet surfaces)
- View switching (transcription/translation)
- Filter groupings

### Anatomy

```
[Tab 1] [Tab 2] [Tab 3]
================================
|                              |
|     Tab Panel Content        |
|                              |
================================
```

### HTML Structure

```html
<div class="tab-group">
  <div class="tab-group__tabs" role="tablist" aria-label="Content views">
    <button
      role="tab"
      aria-selected="true"
      aria-controls="panel-transcription"
      id="tab-transcription"
      class="tab-group__tab"
    >
      Transcription
    </button>
    <button
      role="tab"
      aria-selected="false"
      aria-controls="panel-translation"
      id="tab-translation"
      class="tab-group__tab"
      tabindex="-1"
    >
      Translation
    </button>
    <button
      role="tab"
      aria-selected="false"
      aria-controls="panel-context"
      id="tab-context"
      class="tab-group__tab"
      tabindex="-1"
    >
      Context
    </button>
  </div>

  <div
    role="tabpanel"
    id="panel-transcription"
    aria-labelledby="tab-transcription"
    class="tab-group__panel"
  >
    <!-- Transcription content -->
  </div>

  <div
    role="tabpanel"
    id="panel-translation"
    aria-labelledby="tab-translation"
    class="tab-group__panel"
    hidden
  >
    <!-- Translation content -->
  </div>

  <div
    role="tabpanel"
    id="panel-context"
    aria-labelledby="tab-context"
    class="tab-group__panel"
    hidden
  >
    <!-- Context content -->
  </div>
</div>
```

### Variants

| Variant | Visual | Use Case |
|---------|--------|----------|
| default | Underline indicator | Standard tabs |
| pills | Button-style tabs | Distinct options |
| contained | Full border panel | Isolated content |

### Keyboard Navigation

| Key | Action |
|-----|--------|
| Tab | Move to tab list, then to panel |
| Arrow Left/Right | Navigate between tabs |
| Home | First tab |
| End | Last tab |
| Enter/Space | Activate focused tab |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-variant | string | Visual variant |
| data-selected | string | Selected tab ID |
| data-orientation | string | horizontal/vertical |

### Accessibility

- Full ARIA tablist pattern
- Only selected tab is focusable (tabindex management)
- Arrow keys navigate tabs
- Panel associates with tab via aria-labelledby

---

## SurfaceTabs

### Purpose and Use Cases

SurfaceTabs is a specialized TabGroup for switching tablet surfaces. A common pattern in Glintstone.

### Anatomy

```
[Obverse] [Reverse] [Edge]
```

### HTML Structure

```html
<div
  class="surface-tabs"
  role="tablist"
  aria-label="Tablet surfaces"
>
  <button
    role="tab"
    aria-selected="true"
    data-surface="obverse"
    class="surface-tabs__tab"
  >
    <span class="surface-tabs__label">Obverse</span>
    <span class="surface-tabs__count" aria-label="12 lines">12</span>
  </button>

  <button
    role="tab"
    aria-selected="false"
    data-surface="reverse"
    class="surface-tabs__tab"
    tabindex="-1"
  >
    <span class="surface-tabs__label">Reverse</span>
    <span class="surface-tabs__count" aria-label="8 lines">8</span>
  </button>

  <button
    role="tab"
    aria-selected="false"
    data-surface="edge"
    class="surface-tabs__tab"
    tabindex="-1"
    disabled
  >
    <span class="surface-tabs__label">Edge</span>
    <span class="surface-tabs__count" aria-label="no text">-</span>
  </button>
</div>
```

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-surface | string | Current surface |
| data-surfaces | string | Available surfaces |

### Accessibility

- Same as TabGroup
- Line counts have proper aria-labels

---

## MobileNav

### Purpose and Use Cases

MobileNav provides the mobile navigation drawer that appears when the header menu toggle is activated.

### Anatomy

```
+---------------------------+
| [X Close]                 |
+---------------------------+
|                           |
| [Home]                    |
| [Contribute]              |
| [Explore]                 |
| [Learn]                   |
|                           |
+---------------------------+
|                           |
| [Profile]                 |
| [Settings]                |
| [Sign out]                |
|                           |
+---------------------------+
```

### HTML Structure

```html
<div
  class="mobile-nav"
  id="mobile-nav"
  role="dialog"
  aria-label="Navigation menu"
  aria-modal="true"
  hidden
>
  <div class="mobile-nav__backdrop" data-action="close"></div>

  <nav class="mobile-nav__panel">
    <header class="mobile-nav__header">
      <span class="mobile-nav__title">Menu</span>
      <button
        type="button"
        class="mobile-nav__close"
        aria-label="Close menu"
        data-action="close"
      >
        <svg aria-hidden="true"><!-- close icon --></svg>
      </button>
    </header>

    <ul class="mobile-nav__primary" role="list">
      <li>
        <a href="/" class="mobile-nav__item">
          <svg aria-hidden="true"><!-- icon --></svg>
          Home
        </a>
      </li>
      <li>
        <a href="/contribute" class="mobile-nav__item" aria-current="page">
          <svg aria-hidden="true"><!-- icon --></svg>
          Contribute
        </a>
      </li>
      <li>
        <a href="/explore" class="mobile-nav__item">
          <svg aria-hidden="true"><!-- icon --></svg>
          Explore
        </a>
      </li>
      <li>
        <a href="/learn" class="mobile-nav__item">
          <svg aria-hidden="true"><!-- icon --></svg>
          Learn
        </a>
      </li>
    </ul>

    <hr class="mobile-nav__divider" role="separator">

    <ul class="mobile-nav__secondary" role="list">
      <li>
        <a href="/profile" class="mobile-nav__item">
          Profile
        </a>
      </li>
      <li>
        <a href="/settings" class="mobile-nav__item">
          Settings
        </a>
      </li>
      <li>
        <button type="button" class="mobile-nav__item">
          Sign out
        </button>
      </li>
    </ul>
  </nav>
</div>
```

### Animation

**Open:**
- Backdrop fades in (200ms)
- Panel slides in from left (250ms, ease-out)
- Focus moves to close button

**Close:**
- Panel slides out (200ms)
- Backdrop fades out (150ms)
- Focus returns to toggle button

### Focus Management

1. On open: Focus moves to close button
2. Focus trapped within panel
3. Tab cycles through focusable elements
4. Escape closes menu
5. On close: Focus returns to trigger

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-open | boolean | Menu open state |

### Accessibility

- role="dialog" with aria-modal
- Focus trapped while open
- Escape key closes
- Backdrop click closes
- aria-current on current page

---

## Usage Guidelines

### Header + MobileNav Coordination

```html
<header class="header">
  <!-- Desktop nav in header -->
  <nav class="header__nav" aria-label="Main navigation">
    <!-- Hidden on mobile -->
  </nav>

  <button
    type="button"
    class="header__mobile-toggle"
    aria-label="Open menu"
    aria-expanded="false"
    aria-controls="mobile-nav"
  >
    <!-- Visible on mobile -->
  </button>
</header>

<div class="mobile-nav" id="mobile-nav" hidden>
  <!-- Same nav items, mobile layout -->
</div>
```

### Responsive Breakpoints

| Breakpoint | Header Behavior |
|------------|-----------------|
| < 768px | Logo + mobile toggle only |
| >= 768px | Full navigation visible |

### Tab Navigation Within Pages

```html
<div class="page-content">
  <div class="tab-group" data-variant="default">
    <div role="tablist">
      <button role="tab" aria-selected="true">Tab 1</button>
      <button role="tab" aria-selected="false">Tab 2</button>
    </div>

    <div role="tabpanel">
      <!-- Content changes, URL does not -->
    </div>
  </div>
</div>
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial navigation components |
