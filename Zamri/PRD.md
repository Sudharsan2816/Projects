# Atelier Leather Co. Dashboard PRD

## 1. Product Overview

The Atelier Leather Co. dashboard is an executive operations liveboard for a premium leather goods business. It gives owners, operators, merchandising teams, finance teams, and supply-chain managers one curated view of revenue, orders, funnel leakage, inventory risk, payment reliability, margin health, returns, and supplier performance.

The current implementation is a standalone browser dashboard backed by static demo data and in-browser React state. The product goal is to evolve this prototype into a production analytics dashboard connected to commerce, inventory, payment, return, and supplier systems.

## 2. Problem Statement

Luxury retail operators often see sales, payment failures, inventory risk, returns, and supplier delays in separate tools. This creates slow decision-making and hides the operational cause behind a metric change. The dashboard solves this by presenting the most important operating signals in one owner-friendly interface.

## 3. Target Users

- Brand owner / founder: needs a five-second read on business health and urgent decisions.
- Operations manager: monitors stock, supplier status, returns, and fulfillment risk.
- Ecommerce manager: tracks funnel conversion, checkout drop-off, and channel performance.
- Finance manager: watches settlement timing, payment failures, refunds, and margin leakage.
- Merchandising team: identifies high-velocity SKUs, dead stock, category performance, and reorder needs.

## 4. Product Goals

- Show current business health across revenue, orders, AOV, and payment success.
- Surface funnel leaks and checkout friction before revenue is lost.
- Identify inventory actions: critical stock, reorder items, dead stock, and category filters.
- Expose payment rail reliability, failed transactions, and settlement timing.
- Explain true contribution margin after cost, packaging, authentication, fees, logistics, and returns.
- Track RMA causes and active return pipeline.
- Monitor suppliers, purchase orders, SLA, quality, and lead times.
- Provide a natural-language "Ask the data" assistant for quick retail analysis.
- Preserve the quiet-luxury visual style defined in `DESIGN.md`.

## 5. Current Feature Scope

### Navigation and Shell

The dashboard uses a fixed left sidebar with seven routes:

- Liveboard
- Purchase Funnel
- Inventory
- Payments
- Margins
- Returns
- Suppliers

Each navigation item changes the active page and resets the main content scroll position. Count badges show key workload totals such as funnel alerts, SKU count, open returns, and supplier count.

### Liveboard

The Liveboard is the default page and acts as the executive summary. It includes:

- Header with date, sync timestamp, operating footprint, and live status.
- KPI cards for revenue today, orders, average order value, and UPI success.
- Product lifecycle funnel from cart to checkout to successful payment.
- Funnel insight callout for owner action.
- Payment reliability by rail.
- SKU-level inventory intelligence table.
- Net contribution margin waterfall.
- Implementation roadmap.

### Purchase Funnel

The Purchase Funnel page expands conversion analysis with:

- Date-range segmented control: Today, 7d, 30d, QTD.
- KPIs for visit-to-purchase conversion, average session value, checkout friction, and recovery.
- Full lifecycle funnel from visits to successful payment.
- Drop-off reasons donut chart.
- Channel performance table showing order share and trend.

### Inventory

The Inventory page covers SKU-level stock and capital decisions with:

- Category segmented control: All, Jackets, Footwear, Handbags, Belts, Accessories.
- KPIs for total SKUs, capital tied, critical alerts, and dead stock.
- ABC distribution scatter matrix.
- Reorder queue.
- SKU ledger with product, category, class, on-hand units, on-order units, velocity, capital, and status.

### Payments

The Payments page monitors rail reliability and settlement with:

- Composite payment success.
- Settled-today amount.
- Failed transaction count.
- Average settlement lag.
- Payment reliability table by rail.
- Failed transaction feed.
- Settlement schedule.

### Margins

The Margins page explains contribution economics with:

- Net contribution, gross margin, best category, and worst category KPIs.
- Margin waterfall per $1,000 sold.
- Category contribution chart.
- Margin leaders.
- Margin drag items for review.

### Returns

The Returns page covers reverse logistics and return cost with:

- Return rate, open RMAs, refunded today, and margin reversed KPIs.
- Return reason donut chart.
- Return rate by category.
- Active RMA pipeline with customer, item, reason, amount, date, and status.

### Suppliers

The Suppliers page covers vendor reliability with:

- Active suppliers, on-time delivery, quality score, and open PO KPIs.
- Workshop scorecards with SLA, QA, lead time, provenance, and 90-day spend.
- In-flight purchase orders table with supplier, item, amount, ETA, and status.

### Ask the Data

The sidebar includes an Ask the data card:

- Textarea for a business question.
- Ask action to request a short analyst-style answer.
- Loading state while the assistant responds.
- Error state if the assistant is unavailable.
- Optional result panel with answer text.

### Edit / Tweaks Mode

The prototype includes a floating Tweaks panel for presentation control:

- Accent selector: oxblood, brass, teal, tan.
- Funnel insight toggle.
- Ask-the-data card toggle.
- Brand-name text field.
- Close button for the panel.
- Optional thumbnail rail toggle when hosted in a deck-like environment.

## 6. Functional Requirements

### FR1: Dashboard Routing

The user must be able to switch between all seven operational pages using the sidebar. The active page must be visually highlighted, and main content must reset to the top after navigation.

### FR2: KPI Cards

Each KPI card must show a label, optional tag, value, optional unit, trend/delta, supporting context, and optional sparkline. KPIs must be reusable across pages.

### FR3: Segmented Filters

Segmented filters must update visible data within the current page without leaving the route. Current filters include funnel time range and inventory category.

### FR4: Status Indicators

Operational statuses must be visually distinct and readable. Current statuses include healthy, watch, reorder, critical, stable, monitor, investigate, paid, pending, outgoing, queued, inspecting, approved, replacing, refunded, shipped, in production, and delayed.

### FR5: Tables and Lists

Tables must support dense operational scanning with clear column labels, right-aligned financial values, compact product metadata, and status badges.

### FR6: Charts and Visualizations

The dashboard must support compact charts that do not require external chart libraries in the prototype:

- Sparklines
- Funnel bars
- Donut charts
- Velocity bars
- Waterfall bars
- ABC scatter matrix
- Heatmap-style payment surfaces if expanded

### FR7: Ask the Data

The user must be able to type a natural-language question and trigger an assistant response. The response should be concise, business-oriented, and relevant to leather retail operations.

### FR8: Presentation Tweaks

The user must be able to adjust brand accent, hide/show selected modules, and edit the brand name for demo customization.

## 7. Non-Functional Requirements

- Visual style must follow the Heritage Leather Atelier design system: cream surfaces, charcoal text, oxblood/brass/tan accents, serif headlines, and restrained luxury styling.
- Dashboard must remain scannable at a fixed 1440px layout and scale down using the standalone page letterbox behavior.
- Interactions must be immediate and client-side for the prototype.
- Future production version must separate real data from presentation state.
- Financial and operational metrics must use consistent formatting.
- The dashboard should avoid distracting animation except subtle live/status indicators.

## 8. Data Requirements

Production integration should support:

- Commerce events: sessions, product views, add-to-cart, checkout start, payment success, revenue, AOV, channel attribution.
- Inventory: SKU, category, class, on-hand units, on-order units, velocity, capital tied, status.
- Payments: rail, success rate, transaction amount, failure reason, settlement date, MDR, FX.
- Returns: RMA ID, customer, item, reason, amount, status, refund date, replacement status.
- Suppliers: supplier name, country, specialization, SLA, quality score, lead time, PO amount, ETA, status.
- Assistant context: summarized operational metrics and approved business definitions.

## 9. Success Metrics

- Time to identify top operational issue: under 10 seconds.
- Reduction in missed critical stock alerts.
- Faster detection of payment rail degradation.
- Increased recovery of abandoned checkout value.
- Better visibility into true contribution margin by category and SKU.
- Reduced return rate through reason-level action.
- Improved on-time supplier performance and PO visibility.

## 10. Out of Scope for Current Prototype

- User authentication and role permissions.
- Real backend data ingestion.
- Exporting reports.
- Editable tables.
- CRUD workflows for purchase orders, RMAs, or inventory.
- Notification delivery through email, SMS, Slack, or WhatsApp.
- Drill-down detail pages beyond the current routed sections.

## 11. Future Enhancements

- Connect to Shopify, WooCommerce, ERP, inventory management, payment gateway, and RMA systems.
- Add real-time alerts for critical SKUs, degraded payment rails, delayed POs, and return spikes.
- Add detail drawers for SKU, transaction, RMA, and supplier records.
- Add saved assistant questions and recommended action cards.
- Add CSV/PDF export for finance and operations meetings.
- Add role-based views for owner, finance, ecommerce, inventory, and supplier teams.
- Add mobile/tablet responsive layouts.
- Add audit trail for decisions taken from the dashboard.

