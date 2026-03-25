"""Mock response templates for the Media Agent."""


def build_response(prompt: str) -> str:
    """
    Return a mock media plan response based on the prompt.
    Extracts budget and timeline hints from the prompt for demo realism.
    """
    prompt_lower = prompt.lower()

    # Budget extraction heuristic
    budget_str = "£500,000"
    for symbol in ["£", "$", "€"]:
        if symbol in prompt:
            parts = prompt.split(symbol)
            for part in parts[1:]:
                digits = ""
                for ch in part.replace(",", "").replace("k", "000").replace("m", "000000"):
                    if ch.isdigit():
                        digits += ch
                    elif digits:
                        break
                if digits:
                    val = int(digits)
                    budget_str = f"{symbol}{val:,}"
                    break

    # Quarter detection
    if "q1" in prompt_lower:
        period = "Q1 (Jan–Mar)"
    elif "q2" in prompt_lower:
        period = "Q2 (Apr–Jun)"
    elif "q3" in prompt_lower:
        period = "Q3 (Jul–Sep)"
    elif "q4" in prompt_lower:
        period = "Q4 (Oct–Dec)"
    else:
        period = "Q3 (Jul–Sep)"

    # Audience hint
    if "gen z" in prompt_lower or "gen-z" in prompt_lower:
        primary_channel = "TikTok / Instagram Reels"
        secondary_channel = "YouTube pre-roll"
        display_share = 10
        social_share = 55
        video_share = 25
        ooh_share = 10
    elif "b2b" in prompt_lower:
        primary_channel = "LinkedIn Sponsored Content"
        secondary_channel = "Industry trade publications"
        display_share = 15
        social_share = 45
        video_share = 20
        ooh_share = 20
    else:
        primary_channel = "Digital display + social"
        secondary_channel = "Connected TV / VOD"
        display_share = 25
        social_share = 35
        video_share = 25
        ooh_share = 15

    return f"""Media Plan — {period}
Budget: {budget_str}

═══════════════════════════════════════════

EXECUTIVE SUMMARY
  Recommended full-funnel media strategy for {period} with a total investment of
  {budget_str}. Plan prioritises {primary_channel} for reach efficiency, with
  {secondary_channel} for brand consideration uplift.

BUDGET ALLOCATION

  Channel                   Share    Budget
  ─────────────────────────────────────────
  Digital display           {display_share:>3}%    {_pct(budget_str, display_share)}
  Paid social               {social_share:>3}%    {_pct(budget_str, social_share)}
  Online video              {video_share:>3}%    {_pct(budget_str, video_share)}
  OOH / DOOH                {ooh_share:>3}%    {_pct(budget_str, ooh_share)}
  ─────────────────────────────────────────
  TOTAL                     100%    {budget_str}

CHANNEL STRATEGY

  Primary:   {primary_channel}
    Rationale: Highest reach index vs. target audience. CPM efficiency 18% above
    category benchmark. Recommended spend: {_pct(budget_str, social_share + display_share)}.

  Secondary: {secondary_channel}
    Rationale: High-attention environment for consideration messaging. Average
    view-through rate 72%. Recommended spend: {_pct(budget_str, video_share)}.

  Support:   OOH / DOOH — contextual placements near point-of-purchase.
    Recommended spend: {_pct(budget_str, ooh_share)}.

AUDIENCE TARGETING
  • 1st-party CRM lookalike audiences (seed: top 20% purchasers)
  • Interest and intent segments via DSP
  • Contextual targeting: lifestyle, culture, food & drink verticals
  • Retargeting pool: website visitors (30-day window)

FLIGHT SCHEDULE
  Week 1–2:   Awareness burst — maximum reach; higher frequency cap (5/week)
  Week 3–6:   Sustain — balanced reach and retargeting; optimise toward CTR
  Week 7–8:   Conversion push — retargeting heavy; lower funnel creative

FORECAST KPIs
  Metric                      Forecast
  ─────────────────────────────────────
  Total impressions            42M
  Unique reach                 12M (est. 65% of target universe)
  Average frequency             3.5×
  Clicks                       210,000
  CTR (blended)                0.50%
  Estimated conversions        8,400
  Cost per conversion          {_cost_per(budget_str, 8400)}

MEASUREMENT PLAN
  • Weekly reporting cadence via unified dashboard
  • Brand lift study (Awareness, Consideration, Purchase Intent) — n=1,000
  • Attribution: data-driven model across channels

──────────────────────────────────────────
[STUB RESPONSE — Media Agent v1.0.0]
Prompt received: "{prompt[:80]}{"..." if len(prompt) > 80 else ""}"
"""


def _pct(budget_str: str, pct: int) -> str:
    """Format a percentage of the budget string."""
    try:
        symbol = budget_str[0] if budget_str[0] in "£$€" else "£"
        raw = int("".join(c for c in budget_str if c.isdigit()))
        val = int(raw * pct / 100)
        return f"{symbol}{val:,}"
    except Exception:
        return f"~{pct}% of budget"


def _cost_per(budget_str: str, units: int) -> str:
    try:
        symbol = budget_str[0] if budget_str[0] in "£$€" else "£"
        raw = int("".join(c for c in budget_str if c.isdigit()))
        return f"{symbol}{raw // units:,}"
    except Exception:
        return "N/A"
