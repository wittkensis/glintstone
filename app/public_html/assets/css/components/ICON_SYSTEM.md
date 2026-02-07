# Icon System Documentation

## Overview

Glintstone uses a systematic approach to icons based on Material Icons Sharp, providing consistent, accessible SVG icons throughout the application.

---

## Available Icons

| Icon | Name | Material Name | Use Case |
|------|------|---------------|----------|
| >> | `expand` | keyboard_double_arrow_right | Expand/enlarge views, unfold content |
| << | `collapse` | keyboard_double_arrow_left | Collapse/shrink views, fold content |
| 📚 | `layers` | collections_bookmark | Toggle composite texts, show collections |

---

## Basic Usage

### PHP Function

```php
<?php
// Simple icon
echo icon('expand');

// Icon with custom CSS classes
echo icon('expand', 'icon-lg custom-class');
?>
```

### Icon Button Helper

```php
<?php
// Creates a complete button with icon and accessible label
echo icon_button('expand', 'Expand view', 'btn-primary');

// With custom attributes
echo icon_button('layers', 'Toggle composites', 'composite-btn', 'id="composite-toggle"');
?>
```

---

## Implementation Examples

### Expand/Collapse Toggle

```php
<button class="viewer-toggle" aria-label="Toggle viewer size">
    <?= icon('expand', 'viewer-toggle__icon-expand') ?>
    <?= icon('collapse', 'viewer-toggle__icon-collapse') ?>
</button>
```

**CSS for state management:**

```css
.viewer-toggle__icon-expand,
.viewer-toggle__icon-collapse {
    display: none;
}

[data-state="collapsed"] .viewer-toggle__icon-expand {
    display: block;
}

[data-state="expanded"] .viewer-toggle__icon-collapse {
    display: block;
}
```

### Button with Icon and Text

```php
<button class="composite-toggle">
    <?= icon('layers') ?>
    <span>Composite Text</span>
</button>
```

**CSS for layout:**

```css
.composite-toggle {
    display: flex;
    align-items: center;
    gap: var(--space-2); /* Space between icon and text */
}

.composite-toggle svg {
    width: 16px;
    height: 16px;
    flex-shrink: 0; /* Prevent icon from shrinking */
}
```

---

## CSS Classes

### Icon Sizes

```css
.icon-sm { width: 16px; height: 16px; }
.icon-md { width: 24px; height: 24px; } /* Default */
.icon-lg { width: 32px; height: 32px; }
```

### Icon Button Variants

```css
.icon-btn              /* Standard icon button */
.icon-btn-ghost        /* Transparent border */
.icon-btn-primary      /* Accent color background */
.icon-btn-sm           /* Small (32x32) */
.icon-btn-lg           /* Large (48x48) */
```

---

## Accessibility

### Screen Reader Labels

All icons include `aria-hidden="true"` to prevent screen reader duplication. Buttons must include accessible labels:

```php
<!-- Good: Button has aria-label -->
<button aria-label="Expand view">
    <?= icon('expand') ?>
</button>

<!-- Good: Visible text provides context -->
<button>
    <?= icon('layers') ?>
    <span>Toggle Composites</span>
</button>

<!-- Bad: No accessible label -->
<button><?= icon('expand') ?></button>
```

### Using the Helper Function

```php
<!-- Automatically includes sr-only label -->
<?= icon_button('expand', 'Expand view', 'btn-primary') ?>
```

---

## Adding New Icons

1. **Add SVG path to `icons.php`:**

```php
$icons = [
    'expand' => '<path d="..."/>',
    'collapse' => '<path d="..."/>',
    'layers' => '<path d="..."/>',
    'new_icon' => '<path d="M..."/>', // Add here
];
```

2. **Use Material Icons Sharp for consistency:**
   - Visit [Google Fonts Icons](https://fonts.google.com/icons)
   - Select "Sharp" style variant
   - Copy SVG path data (24x24 viewBox)

3. **Document the icon:**
   - Add to "Available Icons" table above
   - Provide use case examples

---

## Best Practices

### ✅ Do

- Use semantic icon names (`expand`, not `unfold_more`)
- Include aria-labels for icon-only buttons
- Use `gap` for spacing icon + text (not margin)
- Set `flex-shrink: 0` on icons in flex layouts
- Use `fill="currentColor"` for color inheritance

### ❌ Don't

- Mix inline SVGs with the icon system
- Use icons without accessible labels
- Hardcode icon sizes (use CSS classes)
- Forget `aria-hidden="true"` on decorative icons
- Use pixel values for sizing (use rem/CSS vars)

---

## Browser Support

- All modern browsers (Chrome, Firefox, Safari, Edge)
- SVG is rendered natively, no polyfills needed
- Respects `prefers-reduced-motion` for transitions

---

## File Structure

```
/includes/
  icons.php                  # PHP icon functions

/assets/css/components/
  icons.css                  # Icon system styles
  ICON_SYSTEM.md            # This documentation
```

---

## Source Icons

All icons are from [Material Icons Sharp](https://fonts.google.com/icons?icon.style=Sharp) (Apache License 2.0):

- `expand` → keyboard_double_arrow_right (node-id: 405-1937)
- `collapse` → keyboard_double_arrow_left (node-id: 405-1608)
- `layers` → collections_bookmark (node-id: 416-5959)

Extracted from: [MUI for Figma v5.9.0 - Material Icons Sharp](https://www.figma.com/design/FKGLbMpPijjWRF226WX0Ix/)
