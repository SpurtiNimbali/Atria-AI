# UI integration package – what to zip and send

To let someone integrate this voice-first medical UI into their app, zip the following.

---

## Files to include in the zip

### 1. App and UI components (required)

```
src/app/App.tsx
src/app/components/LeftPanel.tsx
src/app/components/CenterPanel.tsx
src/app/components/RightPanel.tsx
src/app/components/Overlays.tsx
```

### 2. Entry point (optional – they may use their own)

```
src/main.tsx
```

### 3. Styles (required for fonts and Tailwind)

```
src/styles/index.css
src/styles/fonts.css
src/styles/tailwind.css
src/styles/theme.css
```

### 4. Dependencies (for their package.json)

The UI **does not** use any `src/app/components/ui/` (shadcn) components. It only needs:

| Package      | Purpose           |
|-------------|-------------------|
| `motion`    | Animations        |
| `lucide-react` | Icons          |
| `react`     | (they already have) |
| `react-dom` | (they already have) |

If they use Tailwind, they need `tailwindcss` and to process the same CSS (or equivalent). The components use Tailwind utility classes (e.g. `flex`, `rounded-xl`, `p-6`).

---

## Minimal zip contents (smallest handoff)

- `src/app/App.tsx`
- `src/app/components/LeftPanel.tsx`
- `src/app/components/CenterPanel.tsx`
- `src/app/components/RightPanel.tsx`
- `src/app/components/Overlays.tsx`
- `src/styles/fonts.css` (Google Fonts: Crimson Pro, Space Mono)
- `src/styles/index.css` (or a note to add the font import)

They can copy these into their repo and install `motion` and `lucide-react` if missing. If they don’t use Tailwind, they’ll need to add Tailwind or replace the utility classes with their own CSS.

---

## Quick file list (for zip / copy-paste)

```
src/app/App.tsx
src/app/components/LeftPanel.tsx
src/app/components/CenterPanel.tsx
src/app/components/RightPanel.tsx
src/app/components/Overlays.tsx
src/main.tsx
src/styles/index.css
src/styles/fonts.css
src/styles/tailwind.css
src/styles/theme.css
```
