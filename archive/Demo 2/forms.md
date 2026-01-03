# Form Components

**Component Category:** Core
**Document Version:** 1.0

Form components handle user input throughout the Glintstone platform. These components prioritize accessibility, clear error states, and mobile-friendly interaction.

**Design Principles:**
- Labels always visible (no placeholder-only inputs)
- Error prevention over error handling
- Immediate validation feedback
- Large touch targets (minimum 44px)
- Clear focus states

---

## Button

### Purpose and Use Cases

Button triggers actions and navigation throughout the interface. Use for:
- Form submissions
- Navigation actions
- Task interactions
- Modal triggers

### Anatomy

```
+------------------------+
| [Icon] Label [Icon]    |
+------------------------+
```

### HTML Structure

```html
<!-- Primary button -->
<button type="button" class="button" data-variant="primary">
  Continue
</button>

<!-- Secondary button -->
<button type="submit" class="button" data-variant="secondary">
  Save changes
</button>

<!-- Ghost button -->
<button type="button" class="button" data-variant="ghost">
  Cancel
</button>

<!-- Button with icon -->
<button type="button" class="button" data-variant="primary">
  <svg aria-hidden="true" class="button__icon button__icon--start">
    <!-- icon -->
  </svg>
  Try it now
</button>

<!-- Icon-only button -->
<button
  type="button"
  class="button button--icon-only"
  aria-label="Close"
>
  <svg aria-hidden="true"><!-- close icon --></svg>
</button>

<!-- Link styled as button -->
<a href="/contribute" class="button" data-variant="primary">
  Get started
</a>
```

### Variants

| Variant | Use Case | Visual |
|---------|----------|--------|
| primary | Main action | Filled, emphasis color |
| secondary | Secondary action | Border, no fill |
| ghost | Tertiary action | Minimal, text-like |
| danger | Destructive action | Red/warning color |

### Sizes

| Size | Height | Font Size | Padding |
|------|--------|-----------|---------|
| sm | 32px | 14px | 8px 12px |
| md | 44px | 16px | 12px 24px |
| lg | 52px | 18px | 16px 32px |

### States

| State | Description | Visual Change |
|-------|-------------|---------------|
| default | Resting | Base styling |
| hover | Mouse over | Lighter/darker shade |
| focus | Keyboard focus | Focus ring |
| active | Being pressed | Darker, slight scale |
| disabled | Not interactive | Muted, no cursor |
| loading | Processing | Spinner, disabled |

### Props/Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| data-variant | string | "primary" | Visual variant |
| data-size | string | "md" | Button size |
| data-loading | boolean | false | Show loading state |
| data-full-width | boolean | false | Full container width |
| disabled | boolean | false | Disable interaction |

### Accessibility

- Use `<button>` for actions, `<a>` for navigation
- Always include accessible name (visible or aria-label)
- Loading state disables button and announces loading
- Focus ring visible at all times
- Minimum touch target: 44x44px

### Loading State

```html
<button
  type="button"
  class="button"
  data-variant="primary"
  data-loading="true"
  disabled
  aria-disabled="true"
>
  <span class="button__spinner" aria-hidden="true"></span>
  <span class="button__label">Submitting...</span>
  <span class="visually-hidden">Please wait</span>
</button>
```

---

## TextInput

### Purpose and Use Cases

TextInput captures single-line text from users. Use for:
- Names and identifiers
- Search queries
- Short responses

### Anatomy

```
Label *
+------------------------+
| Placeholder text       |
+------------------------+
Hint or error message
```

### HTML Structure

```html
<div class="form-field">
  <label for="input-name" class="form-field__label">
    Full name
    <span class="form-field__required" aria-hidden="true">*</span>
  </label>

  <input
    type="text"
    id="input-name"
    name="name"
    class="text-input"
    placeholder="Enter your full name"
    required
    aria-required="true"
    aria-describedby="input-name-hint"
  >

  <span id="input-name-hint" class="form-field__hint">
    As it appears on your publications
  </span>
</div>

<!-- With error state -->
<div class="form-field" data-state="error">
  <label for="input-email" class="form-field__label">
    Email address
  </label>

  <input
    type="email"
    id="input-email"
    name="email"
    class="text-input"
    aria-invalid="true"
    aria-describedby="input-email-error"
  >

  <span id="input-email-error" class="form-field__error" role="alert">
    Please enter a valid email address
  </span>
</div>
```

### Variants

| Variant | Use Case |
|---------|----------|
| default | Standard text input |
| search | Search with icon |
| monospace | Code/ATF input |

### States

| State | Description | ARIA |
|-------|-------------|------|
| default | Ready for input | - |
| focus | Receiving input | - |
| filled | Has value | - |
| disabled | Not editable | aria-disabled="true" |
| readonly | Display only | aria-readonly="true" |
| error | Invalid value | aria-invalid="true" |
| success | Valid value | aria-invalid="false" |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| type | string | Input type (text, email, etc.) |
| placeholder | string | Placeholder text |
| required | boolean | Field required |
| disabled | boolean | Disable input |
| readonly | boolean | Read-only display |
| data-variant | string | Visual variant |

### Accessibility

- Label always associated via `for`/`id`
- Required fields marked with aria-required
- Error messages linked via aria-describedby
- Error state uses aria-invalid
- Placeholder is NOT a substitute for label

---

## TextArea

### Purpose and Use Cases

TextArea captures multi-line text. Use for:
- Notes and comments
- Long-form input
- Correction explanations

### Anatomy

```
Label
+------------------------+
|                        |
| Multi-line input       |
|                        |
+------------------------+
Character count: 50/500
```

### HTML Structure

```html
<div class="form-field">
  <label for="textarea-notes" class="form-field__label">
    Notes
  </label>

  <textarea
    id="textarea-notes"
    name="notes"
    class="textarea"
    rows="4"
    aria-describedby="textarea-notes-hint textarea-notes-count"
  ></textarea>

  <div class="form-field__meta">
    <span id="textarea-notes-hint" class="form-field__hint">
      Optional notes about this correction
    </span>
    <span id="textarea-notes-count" class="form-field__count" aria-live="polite">
      <span class="visually-hidden">Character count:</span>
      0/500
    </span>
  </div>
</div>
```

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| rows | number | Visible rows |
| maxlength | number | Character limit |
| data-auto-resize | boolean | Grow with content |

### Accessibility

- Same pattern as TextInput
- Character count is aria-live
- Resize handle accessible

---

## Select

### Purpose and Use Cases

Select provides dropdown selection from predefined options. Use for:
- Filter selection
- Category choice
- Period/genre selection

### Anatomy

```
Label
+------------------------+
| Selected value      [v]|
+------------------------+
```

### HTML Structure

```html
<div class="form-field">
  <label for="select-period" class="form-field__label">
    Period
  </label>

  <div class="select-wrapper">
    <select id="select-period" name="period" class="select">
      <option value="">Select a period</option>
      <option value="ur-iii">Ur III (2112-2004 BCE)</option>
      <option value="old-babylonian">Old Babylonian (2000-1600 BCE)</option>
      <option value="middle-babylonian">Middle Babylonian (1400-1000 BCE)</option>
      <option value="neo-assyrian">Neo-Assyrian (911-612 BCE)</option>
      <option value="neo-babylonian">Neo-Babylonian (626-539 BCE)</option>
    </select>
    <svg class="select-wrapper__icon" aria-hidden="true">
      <!-- chevron down -->
    </svg>
  </div>
</div>
```

### States

Same as TextInput: default, focus, disabled, error.

### Accessibility

- Native `<select>` for best compatibility
- Custom styling via wrapper
- Keyboard: Arrow keys navigate options
- Screen reader announces options

---

## Checkbox

### Purpose and Use Cases

Checkbox provides boolean toggle. Use for:
- Agreement/consent
- Filter toggles
- Optional features

### Anatomy

```
[x] Label text
```

### HTML Structure

```html
<div class="form-field">
  <label class="checkbox">
    <input type="checkbox" name="agree" class="checkbox__input">
    <span class="checkbox__control" aria-hidden="true">
      <svg class="checkbox__check"><!-- check icon --></svg>
    </span>
    <span class="checkbox__label">
      I agree to the <a href="/terms">terms of service</a>
    </span>
  </label>
</div>

<!-- Indeterminate state -->
<label class="checkbox" data-state="indeterminate">
  <input type="checkbox" name="select-all" aria-checked="mixed">
  <span class="checkbox__control" aria-hidden="true">
    <svg class="checkbox__minus"><!-- minus icon --></svg>
  </span>
  <span class="checkbox__label">Select all</span>
</label>
```

### States

| State | Description | ARIA |
|-------|-------------|------|
| unchecked | Not selected | aria-checked="false" |
| checked | Selected | aria-checked="true" |
| indeterminate | Partial selection | aria-checked="mixed" |
| disabled | Not interactive | disabled attribute |

### Accessibility

- Custom visual, native input for a11y
- Input is visually hidden but accessible
- Click on label toggles checkbox
- Space key toggles when focused

---

## RadioGroup

### Purpose and Use Cases

RadioGroup provides single selection from multiple options. Use for:
- Exclusive choices
- Option selection
- Mode selection

### Anatomy

```
Question/Label
( ) Option A
(o) Option B
( ) Option C
```

### HTML Structure

```html
<fieldset class="radio-group">
  <legend class="radio-group__legend">
    Select export format
  </legend>

  <div class="radio-group__options">
    <label class="radio">
      <input
        type="radio"
        name="format"
        value="atf"
        class="radio__input"
        checked
      >
      <span class="radio__control" aria-hidden="true"></span>
      <span class="radio__content">
        <span class="radio__label">ATF Format</span>
        <span class="radio__description">
          Standard transliteration format
        </span>
      </span>
    </label>

    <label class="radio">
      <input
        type="radio"
        name="format"
        value="json"
        class="radio__input"
      >
      <span class="radio__control" aria-hidden="true"></span>
      <span class="radio__content">
        <span class="radio__label">JSON</span>
        <span class="radio__description">
          Structured data format
        </span>
      </span>
    </label>

    <label class="radio">
      <input
        type="radio"
        name="format"
        value="csv"
        class="radio__input"
      >
      <span class="radio__control" aria-hidden="true"></span>
      <span class="radio__content">
        <span class="radio__label">CSV</span>
        <span class="radio__description">
          Spreadsheet compatible
        </span>
      </span>
    </label>
  </div>
</fieldset>
```

### Variants

| Variant | Layout | Use Case |
|---------|--------|----------|
| default | Stacked | Long options |
| inline | Horizontal | Short options |
| card | Card per option | Visual options |

### Keyboard Navigation

| Key | Action |
|-----|--------|
| Tab | Move to/from group |
| Arrow Up/Down | Navigate options |
| Arrow Left/Right | Navigate options |
| Space | Select focused option |

### Accessibility

- Fieldset + legend groups related radios
- All radios share same `name` attribute
- Arrow keys navigate within group
- Only selected or first radio is tabbable

---

## EmailInput

### Purpose and Use Cases

EmailInput is a specialized text input for email capture. Use for:
- Newsletter signup
- Account creation
- Contact forms

### Anatomy

```
Label
+------------------------+
| email@example.com      |
+------------------------+
We'll never share your email
```

### HTML Structure

```html
<div class="form-field">
  <label for="input-email" class="form-field__label">
    Email address
  </label>

  <div class="input-group">
    <input
      type="email"
      id="input-email"
      name="email"
      class="text-input"
      placeholder="you@example.com"
      autocomplete="email"
      aria-describedby="input-email-hint"
    >
    <button type="submit" class="input-group__button button" data-variant="primary">
      Subscribe
    </button>
  </div>

  <span id="input-email-hint" class="form-field__hint">
    We'll never share your email.
  </span>
</div>
```

### Validation

- Native type="email" provides basic validation
- Enhanced validation on blur or submit
- Clear error message for invalid format

### Accessibility

- autocomplete="email" for autofill
- Validation errors announced
- Submit button within form

---

## Form Layout Patterns

### Standard Form

```html
<form class="form">
  <div class="stack" data-space="lg">
    <div class="form-field">
      <!-- Field 1 -->
    </div>

    <div class="form-field">
      <!-- Field 2 -->
    </div>

    <div class="cluster" data-align="end">
      <button type="button" class="button" data-variant="ghost">
        Cancel
      </button>
      <button type="submit" class="button" data-variant="primary">
        Submit
      </button>
    </div>
  </div>
</form>
```

### Inline Form

```html
<form class="form form--inline">
  <div class="form-field form-field--inline">
    <label for="search" class="visually-hidden">Search tablets</label>
    <input type="search" id="search" placeholder="Search...">
  </div>
  <button type="submit" class="button" data-variant="primary">
    Search
  </button>
</form>
```

### Multi-Column Form

```html
<form class="form">
  <div class="switcher" data-threshold="480px">
    <div class="form-field">
      <!-- First name -->
    </div>
    <div class="form-field">
      <!-- Last name -->
    </div>
  </div>

  <div class="form-field">
    <!-- Full width field -->
  </div>
</form>
```

---

## Validation Patterns

### Client-Side Validation

```html
<input
  type="email"
  required
  pattern="[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
  aria-describedby="email-error"
>
```

### Error Display

```html
<div class="form-field" data-state="error">
  <label for="email">Email</label>
  <input
    type="email"
    id="email"
    aria-invalid="true"
    aria-describedby="email-error"
  >
  <span id="email-error" class="form-field__error" role="alert">
    <svg aria-hidden="true"><!-- error icon --></svg>
    Please enter a valid email address
  </span>
</div>
```

### Validation Timing

| Event | Action |
|-------|--------|
| blur | Validate on field exit |
| change | Validate selections |
| submit | Validate all fields |
| input | Clear error when correcting |

---

## Accessibility Checklist

- [ ] All inputs have visible labels
- [ ] Required fields indicated (visual + aria-required)
- [ ] Error states use aria-invalid
- [ ] Error messages linked via aria-describedby
- [ ] Focus states visible (3:1 contrast minimum)
- [ ] Touch targets 44px minimum
- [ ] Keyboard navigation works
- [ ] Forms work without JavaScript

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial form components |
