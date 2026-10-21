# 🍏 Vellum Web — Apple Design Edition

> **Author & Lead Architect:** Amine Zouaghi  
> **Design Framework:** Apple Human Interface & Emil Kowalski's Apple Design Framework  
> **Platform:** Windows 10 / Windows 11  
> **Port:** `http://localhost:3001`

---

## 🌟 What is the Apple Design Edition?

This edition of Vellum Web has been specifically crafted according to Emil Kowalski's [Apple Design Skill](https://github.com/emilkowalski/skills/blob/main/skills/apple-design/SKILL.md) guidelines, bringing macOS/iOS level tactile elegance, fluid response physics, and layered material vibrancy to a 100% private, local-first academic research studio.

---

## 📐 Implemented Apple Design Principles

### 1. Tactile Response Physics (Zero Latency)
- **Instant Press Feedback:** Every interactive element (buttons, cards, segmented pills, modal triggers) applies `.apple-press` with `active:scale-[0.965-0.97]` and an immediate spring recovery:
  ```css
  --apple-spring-smooth: cubic-bezier(0.16, 1, 0.3, 1);
  ```
- No sluggish linear transitions; all interactions feel physical and alive under the mouse or trackpad.

### 2. Translucent Materials & Specular Borders
- **Frosted Vibrancy (`.apple-glass`):**
  ```css
  background: rgba(255, 255, 255, 0.80); /* Light */
  background: rgba(0, 0, 0, 0.65);       /* Space Black */
  backdrop-filter: blur(24px) saturate(190%);
  border: 1px solid rgba(255, 255, 255, 0.18);
  ```
- Translucent floating toolbars and headers sample and blur underlying content dynamically.

### 3. Continuous Squircle Radii
- Avoids rigid sharp corners by utilizing continuous squircle curvature:
  - Cards: `rounded-[1.5rem]` (24px continuous radius)
  - Modals & Sheets: `rounded-[2rem]` (32px continuous radius)
  - Control Pills: `rounded-full`

### 4. Apple Optical Hierarchy & Typography
- **San Francisco-inspired Optical Tracking:**
  - Tight title tracking: `tracking-[-0.03em]`
  - Balanced subtitle kerning: `tracking-tight`
  - Crisp micro-labels: `text-[10px]` uppercase with balanced spacing.
- **Cupertino System Colors:**
  - System Blue: `#0071e3` (Light) / `#0a84ff` (Dark)
  - System Emerald: `#34c759` / `#30d158`
  - System Amber: `#ff9500` / `#ff9f0a`
  - System Red: `#ff3b30` / `#ff453a`

### 5. Spotlight Search & Modal Dialogue Sheets
- Search bar designed after macOS Spotlight with high-contrast active focus rings.
- Modal dialogs behave like iOS/macOS fluid sheets with deep 24px backdrop blur.

---

## 🚀 How to Run

Double-click:
```cmd
Launch_Web_Apple.bat
```
or run from the parent directory:
```cmd
4_Launch_Apple_Web_App.bat
```

The app will boot on **`http://localhost:3001`**, allowing you to compare it side-by-side with the standard version on **`http://localhost:3000`**!
