"""Mock response templates for the Creative Agent."""


def build_response(prompt: str) -> str:
    """
    Return a mock creative campaign response based on the prompt.
    Incorporates prompt keywords for demo realism without real LLM calls.
    """
    prompt_lower = prompt.lower()

    # Extract flavour from prompt keywords
    if "summer" in prompt_lower:
        season = "Summer"
        theme = "sun-soaked energy and outdoor vibes"
    elif "winter" in prompt_lower or "christmas" in prompt_lower or "holiday" in prompt_lower:
        season = "Winter"
        theme = "warmth, togetherness, and festive spirit"
    elif "autumn" in prompt_lower or "fall" in prompt_lower:
        season = "Autumn"
        theme = "harvest warmth and cosy moments"
    elif "spring" in prompt_lower:
        season = "Spring"
        theme = "renewal, freshness, and new beginnings"
    else:
        season = "Year-Round"
        theme = "authentic connection and everyday moments"

    if "gen z" in prompt_lower or "gen-z" in prompt_lower:
        audience = "Gen Z (18–26)"
        tone = "bold, lo-fi authentic, socially conscious"
        channels = "TikTok, Instagram Reels, YouTube Shorts"
    elif "millennial" in prompt_lower:
        audience = "Millennials (27–42)"
        tone = "aspirational yet relatable, value-driven"
        channels = "Instagram, LinkedIn, podcasts"
    elif "b2b" in prompt_lower:
        audience = "B2B decision-makers"
        tone = "authoritative, insight-led, ROI-focused"
        channels = "LinkedIn, industry publications, email"
    else:
        audience = "Broad consumer (18–45)"
        tone = "inclusive, upbeat, story-driven"
        channels = "Instagram, Facebook, OOH, digital display"

    brand_hint = ""
    for word in ["brand", "beverage", "product", "company", "app"]:
        if word in prompt_lower:
            brand_hint = f" for {word}"
            break

    return f"""Creative Campaign Brief — {season} Campaign{brand_hint}

═══════════════════════════════════════════

CONCEPT: "Refresh Your World"

TARGET AUDIENCE
  {audience}

CAMPAIGN THEME
  {theme}

TONE OF VOICE
  {tone}

KEY MESSAGE
  Every moment deserves to be extraordinary. Our {season.lower()} campaign invites
  {audience.split("(")[0].strip()} to embrace {theme} — with our brand at the centre
  of every shared experience.

CREATIVE EXECUTIONS
  1. Hero Video (30s) — slow-motion lifestyle montage set to an original indie track.
     Visual language: natural light, candid laughter, product in motion.
  2. Social Series (6×15s) — "Your Moment" UGC-style clips seeded with micro-influencers.
  3. Static Display — minimalist product-forward visuals with bold seasonal colour palette.
  4. OOH — commuter placements using bold typography: "Make it a {season} to remember."

RECOMMENDED CHANNELS
  Primary:   {channels}
  Secondary: Programmatic display, email CRM
  Support:   PR seeding to lifestyle and culture press

CREATIVE DIRECTION
  Art direction: warm saturated tones, candid documentary style.
  Typography: contemporary sans-serif, generous white space.
  Photography: real people, real moments — no stock imagery.

CAMPAIGN KPIs
  • Brand awareness lift: +8 percentage points in target demo
  • Social reach: 25M impressions over 6-week flight
  • UGC submissions: 5,000+ under campaign hashtag
  • Engagement rate: ≥4.5% across paid social

TIMELINE
  Week 1–2:   Creative production + influencer briefing
  Week 3:     Soft launch — social seeding
  Week 4–8:   Full media flight
  Week 9:     Performance review + optimisation

──────────────────────────────────────────
[STUB RESPONSE — Creative Agent v1.0.0]
Prompt received: "{prompt[:80]}{"..." if len(prompt) > 80 else ""}"
"""
