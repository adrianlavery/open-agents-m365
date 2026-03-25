"""Mock response templates for the Analytics Agent."""


def build_response(prompt: str) -> str:
    """
    Return a mock analytics insight response based on the prompt.
    Incorporates time period and metric keywords for demo realism.
    """
    prompt_lower = prompt.lower()

    # Detect period
    if "q1" in prompt_lower:
        period, prev_period = "Q1 2026", "Q4 2025"
    elif "q2" in prompt_lower:
        period, prev_period = "Q2 2026", "Q1 2026"
    elif "q3" in prompt_lower:
        period, prev_period = "Q3 2025", "Q2 2025"
    elif "q4" in prompt_lower:
        period, prev_period = "Q4 2025", "Q3 2025"
    elif "last month" in prompt_lower or "this month" in prompt_lower:
        period, prev_period = "March 2026", "February 2026"
    elif "last year" in prompt_lower or "annual" in prompt_lower or "yearly" in prompt_lower:
        period, prev_period = "FY 2025", "FY 2024"
    else:
        period, prev_period = "Q3 2025", "Q2 2025"

    # Detect focus area
    if "channel" in prompt_lower or "platform" in prompt_lower:
        focus = "channel"
    elif "conversion" in prompt_lower or "revenue" in prompt_lower:
        focus = "conversion"
    elif "brand" in prompt_lower or "awareness" in prompt_lower:
        focus = "brand"
    elif "social" in prompt_lower:
        focus = "social"
    else:
        focus = "overall"

    return f"""Analytics Insight Report — {period}

═══════════════════════════════════════════

EXECUTIVE SUMMARY
  Overall campaign performance in {period} exceeded benchmarks across key metrics.
  Total impressions up 14% vs {prev_period}. Conversion rate improved by 0.8pp,
  driven by optimised retargeting and a shift toward higher-intent placements.

PERFORMANCE METRICS — {period}

  Metric                    {period}       vs {prev_period}
  ─────────────────────────────────────────────────────────
  Total Impressions          48.2M        +14.0%  ▲
  Unique Reach               13.6M        +9.2%   ▲
  Clicks                     241,000      +18.4%  ▲
  Click-Through Rate (CTR)   0.50%        +0.06pp ▲
  Conversions                10,242       +22.1%  ▲
  Conversion Rate            4.25%        +0.8pp  ▲
  Cost Per Click (CPC)       £2.08        -4.1%   ▼ (improved)
  Cost Per Conversion        £47.20       -7.3%   ▼ (improved)
  Return on Ad Spend (ROAS)  3.8×         +0.4×   ▲

{_channel_section(focus)}

KEY INSIGHTS

  1. PAID SOCIAL outperformed all other channels on CTR (+32% above plan).
     Instagram Reels drove 41% of total social conversions at 38% lower CPM than
     in {prev_period}.

  2. RETARGETING efficiency improved significantly — 7-day window audiences showed
     2.3× higher conversion rate vs. prospecting audiences. Recommend increasing
     retargeting budget allocation from 15% to 22% in next period.

  3. BRAND CONSIDERATION lifted by 6pp in post-campaign survey vs. pre-campaign
     baseline. Strongest lift in 25–34 demographic (+9pp).

  4. CONNECTED TV underperformed on direct conversion but showed strong halo effect:
     +18% search volume uplift in markets where CTV was active.

RECOMMENDATIONS FOR {_next_period(period)}

  Priority 1 — Scale retargeting allocation: shift 7% of prospecting budget to
  retargeting. Forecast: +450 incremental conversions at same total spend.

  Priority 2 — Pause underperforming placements: 3 programmatic placements
  with CPM > £8 and CTR < 0.15% should be paused. Reallocate to Instagram Reels.

  Priority 3 — Test new creative: current hero creative is at frequency saturation
  (avg 5.2× in target demo). Refresh with 2 new variants for remainder of flight.

  Priority 4 — Expand lookalike audience seed: current seed is 45K users.
  Expanding to top 30% purchasers (est. 120K) should improve prospecting efficiency.

ANOMALIES & ALERTS
  ⚠ Spike detected in bot traffic on 3rd-party display placements (14 Mar).
    Estimated impact: 180K invalid impressions filtered from reported totals.
  ✓ No significant brand safety incidents recorded this period.
  ✓ Viewability rate maintained above 70% threshold across all placements.

──────────────────────────────────────────
[STUB RESPONSE — Analytics Agent v1.0.0]
Prompt received: "{prompt[:80]}{"..." if len(prompt) > 80 else ""}"
"""


def _channel_section(focus: str) -> str:
    if focus == "channel":
        return """TOP PERFORMING CHANNELS

  Rank  Channel              Impressions  Conversions  Conv. Rate  CPC
  ─────────────────────────────────────────────────────────────────────
  1     Paid Social          18.4M        4,210        22.9%       £1.42
  2     Programmatic Display  12.1M        2,890        23.9%       £1.85
  3     Paid Search           6.2M         2,104        33.9%       £2.41
  4     Connected TV          8.8M         612          7.0%        £4.10
  5     Email CRM             2.7M         426          15.8%       £0.38
"""
    elif focus == "conversion":
        return """CONVERSION FUNNEL ANALYSIS

  Stage               Users     Conversion   Drop-off
  ─────────────────────────────────────────────────────
  Impressions         48.2M     —            —
  Clicks              241,000   0.50%        —
  Landing page        198,000   82.2%        17.8%
  Product page        94,000    47.5%        52.5%
  Add to cart         28,200    30.0%        70.0%
  Checkout initiated  14,600    51.8%        48.2%
  Conversion          10,242    70.2%        29.8%

  Key friction point: product page → cart (30% conversion). A/B test recommended.
"""
    else:
        return ""


def _next_period(period: str) -> str:
    mapping = {
        "Q1 2026": "Q2 2026",
        "Q2 2026": "Q3 2026",
        "Q3 2025": "Q4 2025",
        "Q4 2025": "Q1 2026",
        "March 2026": "April 2026",
        "FY 2025": "FY 2026",
    }
    return mapping.get(period, "NEXT PERIOD")
