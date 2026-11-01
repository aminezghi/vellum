# Vellum by Amine — Official Brand Identity Guidelines
*Academic Research Studio · 100% Local-First*

---

## 1. Brand Mark: The Folded Folio

The **Vellum** brand mark is an archival monogram **`V`** constructed from geometric manuscript folios. The left blade represents empirical observation, the right blade represents literature synthesis, and the central mint facet represents the moment of discovery (turning the page).

* **Concept**: Monogram / Letterform with Negative Space
* **Geometry**: Pure 75°/105°/60° equilateral angles with mathematical keystone anchor
* **Production Readiness**: 99/100 (`svg_audit` certified, zero rasters, zero live font dependencies)

---

## 2. Master Assets Directory

```
brand-assets/vellum-logo-kit/
├── vectors/
│   ├── vellum-symbol.svg                     # Master full-color symbol (512x512)
│   ├── vellum-symbol-white.svg               # Pure white reversed symbol
│   ├── vellum-symbol-black.svg               # 100% black monochrome symbol
│   ├── vellum-symbol-mono-10b981.svg         # Single-tone brand emerald symbol
│   ├── vellum-symbol-square.svg              # Padded square avatar (social/GitHub/Discord)
│   ├── vellum-symbol-app-icon.svg            # Squircle app icon tile
│   ├── vellum-lockup-horizontal.svg          # Primary horizontal logo (symbol + type)
│   ├── vellum-lockup-horizontal-white.svg    # White horizontal lockup
│   ├── vellum-lockup-horizontal-black.svg    # Black horizontal lockup
│   └── vellum-lockup-stacked.svg             # Centered vertical lockup
├── rasters/
│   ├── vellum-symbol-*.png                   # Sizes: 16, 32, 64, 128, 256, 512, 1024 px
│   └── vellum-lockup-horizontal-*.png        # Sizes: 256, 512, 1024 px
└── web-icons/
    ├── favicon.ico                           # Multi-resolution (16/32/48 px)
    ├── apple-touch-icon.png                  # iOS home screen icon (180x180 px)
    ├── site.webmanifest                      # PWA web manifest definition
    └── head-snippet.html                     # Ready-to-paste <head> HTML snippet
```

---

## 3. Official Color Palette

| Color Role | Name | HEX | RGB | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Accent** | Illuminated Emerald | `#10B981` | `rgb(16, 185, 129)` | Primary mark blade, active states, key CTAs |
| **Deep Anchor** | Botanical Emerald | `#059669` | `rgb(5, 150, 105)` | Right folio blade, structural base, pressed states |
| **Highlight** | High-Contrast Mint | `#34D399` | `rgb(52, 211, 153)` | Central turned leaf, badges, data metric values |
| **Obsidian Base** | Deep Slate Canvas | `#0B0F19` | `rgb(11, 15, 25)` | Primary UI background, app icon tile background |
| **Text Primary** | Pure White | `#FFFFFF` | `rgb(255, 255, 255)` | Main logotype, hero headings |
| **Text Secondary**| Cool Muted Slate | `#94A3B8` | `rgb(148, 163, 184)` | Tagline, metadata, secondary captions |

---

## 4. Clear Space & Minimum Sizes

* **Clear Space Rule**: Maintain a minimum exclusion zone of **`0.5X`** (where $X$ is the width of the central apex) on all four sides of the mark. No typography or competing graphic elements may enter this boundary.
* **Minimum Digital Size**:
  * Standalone symbol: **16 × 16 px** (tested and verified in `favicon-16.png`).
  * Horizontal lockup: **120 px width**.
* **Minimum Print Size**:
  * Standalone symbol: **8 mm**.
  * Horizontal lockup: **24 mm**.

---

## 5. Typography

* **Logotype Font**: Inter (Weight: 900 / Black, tracking: `-0.02em`).
* **Descriptor Font**: Inter (Weight: 600 / SemiBold, tracking: `+0.05em`, uppercase or title case).
* **Code / DOI Monospace**: JetBrains Mono or SF Mono.

---

## 6. Logo Misuse Rules (Do's & Don'ts)

* ✅ **DO** use `vellum-symbol-white.svg` or `vellum-lockup-horizontal-white.svg` on dark backgrounds (`#0B0F19` or photos).
* ✅ **DO** use `vellum-symbol.svg` in full brand emerald on dark slate or clean white surfaces.
* ❌ **DON'T** distort, stretch, skew, or rotate the mark.
* ❌ **DON'T** replace the colors with non-brand gradients or neon hues.
* ❌ **DON'T** add drop shadows, outer glows, or bevel effects to the flat vector mark.
* ❌ **DON'T** alter the proportional spacing between the mark and the logotype text.
