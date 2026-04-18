import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any


DARK_TEMPLATE = dict(
    layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.03)",
        font=dict(color="#cdd9e8", family="Inter, sans-serif"),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
)


def competitor_radar(competitors: List[Dict[str, Any]]) -> go.Figure:
    """Radar chart scoring competitors on 5 axes (approximated from data)."""
    categories = ["Market Reach", "Innovation", "Pricing Power", "Brand Strength", "Product Range"]

    import random
    random.seed(42)

    fig = go.Figure()
    colors = ["#4fc3f7", "#81c784", "#ffb74d", "#ce93d8", "#f48fb1"]

    for i, comp in enumerate(competitors[:5]):
        scores = [random.randint(50, 95) for _ in categories]
        scores.append(scores[0])
        cats = categories + [categories[0]]

        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=cats,
            fill="toself",
            name=comp.get("name", f"Comp {i+1}"),
            line=dict(color=colors[i % len(colors)], width=2),
            fillcolor=colors[i % len(colors)].replace(")", ",0.1)").replace("rgb", "rgba"),
            opacity=0.8,
        ))

    fig.update_layout(
        **DARK_TEMPLATE["layout"].to_plotly_json(),
        polar=dict(
            bgcolor="rgba(255,255,255,0.03)",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="rgba(255,255,255,0.1)",
                tickfont=dict(size=9, color="#78909c"),
            ),
            angularaxis=dict(
                gridcolor="rgba(255,255,255,0.1)",
                tickfont=dict(size=10, color="#cdd9e8"),
            ),
        ),
        title=dict(text="Competitor Positioning Radar", font=dict(size=14, color="#e3f2fd")),
        showlegend=True,
        height=420,
    )
    return fig


def pricing_bar(pricing: List[Dict[str, Any]]) -> go.Figure:
    """Horizontal bar chart of price segments."""
    segments = [p.get("segment", "") for p in pricing]
    # Parse price range midpoints (rough heuristic)
    midpoints = []
    for p in pricing:
        pr = p.get("price_range", "0")
        nums = [int(s.replace(",", "")) for s in pr.split() if s.replace(",", "").isdigit()]
        midpoints.append(sum(nums) // len(nums) if nums else 0)

    colors_list = ["#4fc3f7", "#81c784", "#ffb74d", "#ce93d8", "#f48fb1"]

    fig = go.Figure(go.Bar(
        x=midpoints,
        y=segments,
        orientation="h",
        marker=dict(color=colors_list[:len(segments)], opacity=0.85),
        text=[p.get("price_range", "") for p in pricing],
        textposition="outside",
        textfont=dict(color="#cdd9e8", size=11),
    ))

    fig.update_layout(
        **DARK_TEMPLATE["layout"].to_plotly_json(),
        title=dict(text="Price Segment Overview", font=dict(size=14, color="#e3f2fd")),
        xaxis=dict(
            title="Avg. Price (local currency)",
            gridcolor="rgba(255,255,255,0.08)",
            tickfont=dict(color="#78909c"),
        ),
        yaxis=dict(tickfont=dict(color="#cdd9e8")),
        height=300,
    )
    return fig


def trends_impact_pie(trends: List[Dict[str, Any]]) -> go.Figure:
    """Donut chart of trend impact distribution."""
    from collections import Counter
    impact_counts = Counter(t.get("impact", "Medium") for t in trends)

    labels = list(impact_counts.keys())
    values = list(impact_counts.values())
    color_map = {"High": "#ef5350", "Medium": "#ffa726", "Low": "#66bb6a"}
    clrs = [color_map.get(l, "#78909c") for l in labels]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=clrs, line=dict(color="#0d1b2a", width=2)),
        textfont=dict(color="white", size=12),
    ))

    fig.update_layout(
        **DARK_TEMPLATE["layout"].to_plotly_json(),
        title=dict(text="Trend Impact Distribution", font=dict(size=14, color="#e3f2fd")),
        height=280,
        showlegend=True,
    )
    return fig
