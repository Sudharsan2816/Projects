# Zamri — Atelier Leather Co. Analytics Dashboard

![React](https://img.shields.io/badge/React-SPA-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-typed-3178C6?logo=typescript&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind-CSS-06B6D4?logo=tailwindcss&logoColor=white)
![Status](https://img.shields.io/badge/status-prototype-orange)

Executive operations liveboard for a premium leather goods brand. One interface covers every critical signal an owner, operations manager, or finance lead needs to act within 10 seconds of opening.

---

## Overview

A standalone React SPA with static demo data, built to prove the concept before connecting real commerce, inventory, and payment systems. The design system ("Heritage Leather Atelier") uses cream surfaces, charcoal text, oxblood/brass accents, and serif headlines to match the brand's quiet-luxury positioning.

**Problem solved:** Luxury retail operators see sales, payment failures, inventory risk, returns, and supplier delays in separate tools. This creates slow decisions and hides the operational cause behind a metric change.

---

## Navigation

| Section | What it shows |
|---------|---------------|
| **Liveboard** | Revenue today, orders, AOV, UPI success rate, funnel summary, payment reliability, inventory intelligence, margin waterfall |
| **Purchase Funnel** | Visit-to-purchase conversion, checkout friction, drop-off reasons, channel performance |
| **Inventory** | ABC scatter matrix, reorder queue, SKU ledger with velocity, capital, and status by category |
| **Payments** | Rail reliability, failed transactions, settlement schedule |
| **Margins** | Net contribution waterfall, category margins, margin leaders and drag items |
| **Returns** | RMA pipeline, return reasons, return rate by category |
| **Suppliers** | Workshop scorecards, in-flight POs, SLA and quality scores |

---

## Features

- **KPI cards** — label, value, delta, trend, sparkline; reusable across all pages
- **Client-side charts** — sparklines, funnel bars, donut charts, waterfall bars, ABC scatter matrix (no external chart library)
- **Ask the data** — natural-language AI assistant panel for retail analysis questions
- **Tweaks panel** — presentation mode: swap accent colour (oxblood / brass / teal / tan), toggle modules, edit brand name
- **Status system** — 18 distinct operational statuses: critical, reorder, watch, healthy, delayed, inspecting, and more
- **Segmented filters** — date range on Purchase Funnel, category filter on Inventory

---

## Design System

| Token | Value |
|-------|-------|
| Surface | Cream `#FAF8F5` |
| Text | Charcoal `#2C2C2C` |
| Primary accent | Oxblood `#8B1A1A` |
| Secondary accent | Brass `#B8860B` |
| Heading font | Playfair Display (serif) |
| Body font | Inter |
| Layout | Fixed 1440 px, letterboxed on smaller screens |

---

## Production Roadmap

The prototype uses static demo data. The production integration path:

```
Shopify / WooCommerce   → sessions, orders, revenue, AOV, channel attribution
Inventory System        → SKU, stock levels, velocity, capital tied
Payment Gateway         → rails, success rate, settlements, failures
RMA System              → returns, refunds, replacements
Supplier Portal         → POs, SLA, quality scores, lead times
          │
          ▼
     Data API (FastAPI / Node)
          │
          ▼
     Dashboard (React)
```

Planned additions: real-time alerts, drill-down drawers, role-based views (owner / finance / ecommerce / inventory), CSV/PDF export, mobile layouts.

---

## Documentation

| File | Contents |
|------|----------|
| [`PRD.md`](./PRD.md) | Full product requirements: goals, functional requirements, data schema, success metrics, out-of-scope |
| [`DASHBOARD_FEATURE_EXPLANATION.md`](./DASHBOARD_FEATURE_EXPLANATION.md) | Detailed feature breakdown for each dashboard section |
