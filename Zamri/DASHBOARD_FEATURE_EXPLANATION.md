# Atelier Leather Co. Dashboard Feature Explanation

This document explains every visible dashboard feature, button, filter, control, and status indicator in the current standalone dashboard.

## 1. Global Layout

### Brand Block

The top of the sidebar shows the brand mark, brand name, and location line. It identifies the operating brand and reinforces the heritage leather positioning. The brand name can be changed from the Tweaks panel.

### Operations Navigation

The navigation buttons switch between dashboard modules:

- Liveboard: opens the executive operating summary.
- Purchase Funnel: opens conversion, drop-off, and channel analysis.
- Inventory: opens SKU velocity, stock, capital, and reorder analysis.
- Payments: opens payment rail success, failures, and settlement schedule.
- Margins: opens contribution margin, category economics, and margin leakage.
- Returns: opens return reasons, RMA queue, and refund impact.
- Suppliers: opens supplier scorecards and purchase orders.

Badges beside navigation items indicate workload or count context. For example, Inventory shows SKU count context, Returns shows open return workload, and Suppliers shows active supplier count.

## 2. Ask the Data Card

### Question Textarea

Use this field to type a natural-language business question, such as "Which leather shoe color sold best this week?" It is intended for owner-level analysis without manually reading every panel.

### Ask Button

The Ask button submits the typed question to the assistant. The assistant returns a short retail analyst answer with plausible figures and direct recommendations.

### Thinking State

While the assistant is processing, the card shows a thinking/loading message. This prevents duplicate submissions.

### Answer Panel

After a successful response, the answer appears below the Ask button. If the assistant is unavailable, an error message asks the user to try again.

## 3. Liveboard Page

### Liveboard Active Pill

Shows that the dashboard is in live operating mode. It supports trust in the page as a real-time command view.

### Synced Timestamp

Shows the last sync time and operating scope: stores, channels, and SKU count. It helps users judge freshness.

### Revenue Today KPI

Shows current-day revenue, target comparison, and sparkline trend. Use it to understand whether the day is ahead or behind plan.

### Orders KPI

Shows order volume over the last 24 hours and checkout context. Use it to compare order count against revenue and AOV.

### Average Order Value KPI

Shows average order value and benchmark comparison. Use it to monitor premium basket quality.

### UPI Success KPI

Shows real-time UPI payment success. Use it to detect payment reliability issues that could block orders.

### Product Lifecycle Funnel Panel

Shows In-Cart, In-Checkout, and Payment Successful stages. Use it to separate low demand from checkout friction and payment failures.

### Funnel Insight Toggle Content

The owner-action insight explains what to do with the funnel data. It can be shown or hidden from the Tweaks panel.

### Payment Reliability Panel

Shows success rates for UPI, Net Banking, Cards, and International Cards. Use it to identify degraded payment rails.

### SKU-Level Inventory Intelligence Panel

Shows key SKUs with ABC class, on-hand units, velocity, and status. Use it to identify fast-moving items that need reorder action.

### Net Contribution Margin Panel

Shows how gross sales are reduced by COGS, packaging, authentication, fees, and logistics. Use it to understand true retained margin.

### Implementation Roadmap

Shows delivery phases: Discovery, Integration, Design, Launch, and Iteration. Use it as a client-facing implementation progress indicator.

## 4. Purchase Funnel Page

### Time Range Segmented Control

Buttons: Today, 7d, 30d, QTD.

Use these buttons to change the analysis window for funnel data. In the prototype, the selected segment updates active state; in production it should refetch or recalculate the funnel metrics.

### Visit to Purchase KPI

Shows conversion from visits to purchases. Use it as the main funnel health metric.

### Avg Session Value KPI

Shows estimated value per session. Use it to compare traffic quality across time windows.

### Checkout Friction KPI

Shows payment-stage abandonment. Use it to identify revenue leakage at checkout.

### Recovery KPI

Shows recovered cart value and recovered cart count. Use it to measure retargeting or email recovery effectiveness.

### Full Lifecycle Funnel

Shows stages from Visited to Payment Successful, including step-over-step drop-off. Use it to identify where users leave the purchase path.

### Why We Lose Orders Donut

Shows reasons such as shipping cost shock, payment failure, comparison shopping, unclear size guide, and other. Use it to prioritize conversion fixes.

### Channel Performance Panel

Shows order share and trend by Direct, Instagram, Email, Google, Referral, and Affiliate. Use it to compare channel productivity.

## 5. Inventory Page

### Category Segmented Control

Buttons: All, Jackets, Footwear, Handbags, Belts, Accessories.

Use these buttons to filter the SKU ledger by category. The filtered count and table rows update to match the selected category.

### Total SKUs KPI

Shows active SKU count across categories. Use it as inventory scope context.

### Capital Tied KPI

Shows capital locked in inventory. Use it to monitor working-capital efficiency.

### Critical Alerts KPI

Shows SKUs likely to stock out soon. Use it to prioritize urgent replenishment.

### Dead Stock KPI

Shows slow or non-moving stock value. Use it to plan markdowns or liquidation.

### ABC Distribution Matrix

Plots SKUs by capital tied and monthly velocity. Use it to identify:

- Class A: high-value or high-velocity items to keep stocked.
- Class B: monitor items.
- Class C: slow items that may need liquidation.

### Reorder Queue

Shows auto-suggested reorder actions for critical and reorder-status SKUs. Use it to prepare purchase orders.

### SKU Ledger

Shows product, category, class, on-hand units, on-order units, velocity, capital, and status. Use it as the main stock review table.

## 6. Payments Page

### Composite Success KPI

Shows weighted payment success across rails. Use it to understand payment health at the business level.

### Settled Today KPI

Shows amount settled to bank. Use it to separate sales from actual cash movement.

### Failed Transactions KPI

Shows failed payment count and at-risk value. Use it to trigger gateway or retry investigation.

### Avg Settlement KPI

Shows settlement lag in days. Use it to watch cash-flow timing.

### Payment Reliability Table

Shows rail, success percentage, trend sparkline, volume, transaction count, failed count, and action status. Use it to identify which rail is stable, needs monitoring, or needs investigation.

### Failed Transactions Feed

Shows transaction ID, customer, reason, rail, amount, and time. Use it to debug failure patterns such as card decline, 3DS timeout, insufficient funds, gateway timeout, or risk flag.

### Settlement Schedule

Shows expected incoming and outgoing cash events. Status labels include Paid, Pending, and Outgoing. Use it for short-term cash planning.

## 7. Margins Page

### Net Contribution KPI

Shows retained contribution after all variable costs. Use it as the core profitability metric.

### Gross Margin KPI

Shows headline margin before full operating deductions. Use it to compare with net contribution.

### Best Category KPI

Shows the strongest net-margin category. Use it to identify where additional inventory or marketing can be efficient.

### Worst Category KPI

Shows the weakest category. Use it to identify markdown or assortment review needs.

### Where the Margin Goes Waterfall

Shows deductions from every $1,000 sold: COGS, packaging, authentication, fees, logistics, and returns. Use it to explain why gross margin differs from real retained margin.

### Category Contribution Panel

Shows net percentage and revenue by category. Use it to compare category-level efficiency.

### Margin Leaders

Shows top SKUs by net margin. Use it to decide what products deserve more visibility or stock.

### Margin Drag Review

Shows low-margin SKUs or categories. Use it to trigger discount, pricing, sourcing, or assortment decisions.

## 8. Returns Page

### Return Rate KPI

Shows 30-day return rate. Use it to monitor reverse-logistics health.

### Open RMAs KPI

Shows open return authorizations. Use it to track operations workload.

### Refunded Today KPI

Shows daily refund amount and closed RMA count. Use it to understand cash and margin reversal.

### Margin Reversed KPI

Shows net margin lost to returns after restock recovery. Use it to understand return cost beyond refund amount.

### Return Reasons Donut

Shows why customers return items: size/fit, quality concern, color mismatch, changed mind, or damaged in transit. Use it to prioritize fixes.

### Return Rate by Category

Shows which categories cause the most return pressure. Use it to identify category-specific issues such as footwear sizing.

### Return Authorization Pipeline

Shows active RMAs with customer, item, reason, amount, date, and status. Use it to manage queue, inspection, approval, replacement, and refund work.

## 9. Suppliers Page

### Active Suppliers KPI

Shows active supplier count and qualification pipeline. Use it to understand network breadth.

### On-Time Delivery KPI

Shows supplier SLA performance. Use it to spot delivery reliability issues.

### Quality Score KPI

Shows quality performance. Use it to monitor defects and supplier craftsmanship.

### Open POs KPI

Shows committed value in active purchase orders. Use it for procurement and cash planning.

### Workshop Performance Scorecards

Each supplier card shows supplier name, location, specialization, total score, SLA, QA, lead time, and 90-day spend. Use it to compare workshop reliability and provenance.

### In-Flight POs Table

Shows purchase order number, supplier, items, amount, ETA, and status. Use it to track procurement execution.

## 10. Status Badges

### Healthy / Stable / Paid / Approved / Refunded / Shipped

Indicates the item or process is operating normally.

### Watch / Monitor / Pending / In Production / Queue

Indicates the item is active and should be watched but is not yet critical.

### Reorder / Inspect / Replace / Outgoing

Indicates an operational action is required or underway.

### Critical / Investigate / Delayed

Indicates urgent attention is needed.

## 11. Tweaks Panel

### Close Button

Closes the floating Tweaks panel.

### Accent Control

Options: oxblood, brass, teal, tan.

Use it to change the dashboard accent color for presentation or brand variation.

### Funnel Insight Toggle

Turns the Liveboard funnel insight callout on or off.

### Ask-the-Data Card Toggle

Shows or hides the sidebar Ask the data card.

### Brand Text Field

Changes the brand name displayed in the sidebar.

### Thumbnail Rail Toggle

Appears only in supported host environments. It shows or hides a deck thumbnail rail when the dashboard is used inside a presentation-style host.

## 12. Current Prototype Limitations

- Most data is static demo data.
- Navigation and filters are client-side only.
- Table rows do not open detail views.
- Status badges are informational, not clickable workflow actions.
- The Ask feature depends on an assistant API exposed as `window.claude.complete`.
- There is no authentication, export, backend persistence, or production data ingestion yet.

