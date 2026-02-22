# Styling Approach: CSS Classes Only

## Q3: How Should UI Elements Be Styled?

### Answer: CSS Classes Only - Manual Styling Later

**Decision:** Use **semantic CSS classes** without inline styles. The user will determine the actual visual styling manually later.

---

## Rationale

1. **Separation of Concerns**
   - HTML structure defines semantic meaning
   - CSS handles visual presentation
   - Changes to styling don't require code changes

2. **Design System Flexibility**
   - User can apply design system tokens later
   - Easy to theme (dark mode, high contrast, etc.)
   - Consistent with existing ATF viewer patterns

3. **Maintainability**
   - All styling in one place (CSS files)
   - Easier to refactor visual design
   - No scattered inline styles to update

---

## Class Naming Convention

### BEM Methodology (Block Element Modifier)

Following existing codebase patterns from `/app/static/css/components/atf-viewer/`:

```css
/* Block */
.translation-pipeline { }

/* Element */
.translation-pipeline__line { }
.translation-pipeline__token { }
.translation-pipeline__translation { }

/* Modifier */
.translation-pipeline__token--damaged { }
.translation-pipeline__token--missing { }
.translation-pipeline__line--active { }
```

---

## Semantic Class Structure

### Translation Pipeline Container

```html
<div class="translation-pipeline">
  <div class="translation-pipeline__header">
    <div class="translation-pipeline__metadata"></div>
    <div class="translation-pipeline__pipeline-status"></div>
  </div>

  <div class="translation-pipeline__content">
    <div class="translation-pipeline__surface-tabs"></div>
    <div class="translation-pipeline__lines"></div>
  </div>

  <div class="translation-pipeline__sidebar">
    <div class="translation-pipeline__dictionary"></div>
  </div>
</div>
```

### Line Structure

```html
<div class="translation-line" data-line-id="282193">
  <div class="translation-line__number">1</div>

  <div class="translation-line__atf">
    <span class="translation-line__surface-label">obverse</span>
    <span class="translation-line__text">ninda</span>
  </div>

  <div class="translation-line__tokens">
    <span class="translation-token" data-token-id="556573">
      <span class="translation-token__form">ninda</span>
      <span class="translation-token__reading">NINDA</span>
    </span>
  </div>

  <div class="translation-line__lemma">
    <span class="translation-lemma">
      <span class="translation-lemma__cf">ninda[bread]</span>
      <span class="translation-lemma__gw">bread</span>
      <span class="translation-lemma__pos">N</span>
    </span>
  </div>

  <div class="translation-line__translation">
    <span class="translation-text">bread</span>
    <span class="translation-source">cdli</span>
  </div>
</div>
```

### Token States

```html
<!-- Intact token -->
<span class="translation-token translation-token--intact">ninda</span>

<!-- Damaged token -->
<span class="translation-token translation-token--damaged">ninda#</span>

<!-- Missing/broken token -->
<span class="translation-token translation-token--missing">[...]</span>

<!-- Uncertain reading -->
<span class="translation-token translation-token--uncertain">ninda?</span>

<!-- Corrected reading -->
<span class="translation-token translation-token--corrected">ninda!</span>
```

### Sign Functions

```html
<!-- Logogram -->
<span class="translation-token translation-token--logogram">NINDA</span>

<!-- Syllabogram -->
<span class="translation-token translation-token--syllabic">ni</span>

<!-- Determinative -->
<span class="translation-token translation-token--determinative">{d}</span>

<!-- Number -->
<span class="translation-token translation-token--numeric">10</span>
```

### Pipeline Status Indicators

```html
<div class="pipeline-status">
  <div class="pipeline-status__stage pipeline-status__stage--complete">
    <span class="pipeline-status__label">ATF</span>
    <span class="pipeline-status__value">100%</span>
  </div>

  <div class="pipeline-status__stage pipeline-status__stage--pending">
    <span class="pipeline-status__label">Tokens</span>
    <span class="pipeline-status__value">Pending</span>
  </div>

  <div class="pipeline-status__stage pipeline-status__stage--partial">
    <span class="pipeline-status__label">Lemmas</span>
    <span class="pipeline-status__value">45%</span>
  </div>
</div>
```

---

## Data Attributes for Functionality

Use `data-*` attributes for JavaScript interaction (not styling):

```html
<!-- Line identification -->
<div class="translation-line"
     data-line-id="282193"
     data-surface="obverse"
     data-line-number="1">

<!-- Token interaction -->
<span class="translation-token"
      data-token-id="556573"
      data-clickable="true">

<!-- Lemma lookup -->
<span class="translation-lemma"
      data-entry-id="o0027567"
      data-has-dictionary="true">

<!-- Translation metadata -->
<div class="translation-text"
     data-source="cdli"
     data-language="en"
     data-match-method="positional">
```

---

## Existing Patterns to Follow

From `/app/static/css/components/atf-viewer/words.css`:

```css
/* Existing classes we can reference */
.atf-word { }
.atf-word--damaged { }
.atf-word--uncertain { }
.atf-word--corrected { }
.atf-logo { }
.atf-broken { }
.atf-determinative { }
```

**Approach:**
- Reuse existing `.atf-*` classes where appropriate
- Add new `.translation-*` classes for new components
- Keep naming consistent with existing patterns

---

## CSS File Structure

### Proposed Organization

```
/app/static/css/components/translation-pipeline/
├── index.css               # Imports all component styles
├── layout.css              # Grid/flex layout
├── line.css                # Line component styles
├── token.css               # Token component styles
├── lemma.css               # Lemma component styles
├── translation.css         # Translation text styles
├── pipeline-status.css     # Pipeline status indicator styles
└── states.css              # Damage states, active states
```

### Example: `token.css`

```css
/* Placeholder structure - user will style later */

.translation-token {
  /* Base token styling */
}

.translation-token--logogram {
  /* Logogram-specific styling */
}

.translation-token--syllabic {
  /* Syllabogram-specific styling */
}

.translation-token--damaged {
  /* Damaged token styling */
}

.translation-token--missing {
  /* Missing token styling */
}

.translation-token--uncertain {
  /* Uncertain reading styling */
}

.translation-token--clickable {
  /* Interactive token styling */
}

.translation-token--active {
  /* Active/selected token styling */
}
```

---

## Implementation Notes

### Component Generation

```javascript
// Generate semantic HTML with classes
function renderToken(token) {
  const classes = ['translation-token'];

  // Add state modifiers
  if (token.damage === 'damaged') classes.push('translation-token--damaged');
  if (token.damage === 'missing') classes.push('translation-token--missing');

  // Add function modifiers
  if (token.sign_function === 'logo') classes.push('translation-token--logogram');
  if (token.sign_function === 'syllabic') classes.push('translation-token--syllabic');

  // Add interaction modifiers
  if (token.clickable) classes.push('translation-token--clickable');

  return `
    <span class="${classes.join(' ')}"
          data-token-id="${token.id}"
          data-clickable="${token.clickable}">
      ${token.form || token.reading}
    </span>
  `;
}
```

### State Management via Classes

```javascript
// Add/remove state classes dynamically
function setTokenActive(tokenElement, active) {
  if (active) {
    tokenElement.classList.add('translation-token--active');
  } else {
    tokenElement.classList.remove('translation-token--active');
  }
}

function setLineExpanded(lineElement, expanded) {
  if (expanded) {
    lineElement.classList.add('translation-line--expanded');
  } else {
    lineElement.classList.remove('translation-line--expanded');
  }
}
```

---

## Testing Checklist

- [ ] All visual elements use classes (no inline styles)
- [ ] Class names follow BEM convention
- [ ] Data attributes used only for functionality (not styling)
- [ ] CSS classes are semantic (describe meaning, not appearance)
- [ ] Modifiers properly namespaced (`block__element--modifier`)
- [ ] Reuse existing ATF viewer classes where applicable
- [ ] CSS file structure mirrors component hierarchy
- [ ] State changes use class addition/removal (not style manipulation)

---

## Benefits of This Approach

1. **Flexibility:** Styling can change completely without touching HTML/JS
2. **Consistency:** All styling centralized in CSS files
3. **Performance:** Class changes are faster than style recalculation
4. **Maintainability:** Easy to find and update styles
5. **Accessibility:** Semantic classes improve screen reader navigation
6. **Theming:** Easy to swap entire design systems

---

## Future: Kenilworth Design System Integration

When ready to apply styling, user can:

1. Load Kenilworth design tokens
2. Map semantic classes to design system
3. Apply color, typography, spacing tokens
4. Add dark mode variants
5. Implement accessibility enhancements

**Example mapping:**
```css
/* Map semantic class to design system */
.translation-token--damaged {
  color: var(--color-warning);
  text-decoration: underline;
  text-decoration-style: wavy;
  text-decoration-color: var(--color-warning);
}

.translation-token--logogram {
  font-weight: var(--font-weight-bold);
  text-transform: uppercase;
  color: var(--color-logogram);
}
```

---

## Conclusion

**Use CSS classes exclusively. User will apply Kenilworth design system styling later.**
