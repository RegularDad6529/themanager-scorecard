#!/usr/bin/env python3
"""
TheManager Scorecard — Gemba Board Generator

Reads dashboard data from JSON and renders a dark-themed HTML gemba board.
Each wave/activity gets its own zone with headline KPIs.
Zones are configurable — add/remove waves in config/scorecard_config.json.

Output: HTML file + PNG screenshot (via Playwright).
"""
import json, os, sys
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")
OUTPUT_DIR = os.path.join(BASE, "output")
CONFIG_FILE = os.path.join(BASE, "config", "scorecard_config.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE, "config"), exist_ok=True)

# === CONFIG ===
# Defines which zones appear on the board and which data keys to display.
# Add/remove zones here — the generator will pick up changes automatically.
DEFAULT_CONFIG = {
    "title": "TheManager Scorecard",
    "subtitle": "6529 Daily Operations Dashboard",
    "zones": [
        {
            "id": "giphy",
            "label": "GIPHY",
            "color": "#22d3ee",
            "icon": "📊",
            "metrics": [
                {"key": "channel_views", "label": "Total Views", "format": "string"},
                {"key": "channel_uploads", "label": "Uploads", "format": "string"},
                {"key": "local_meme_cards", "label": "Meme Cards", "format": "int"},
                {"key": "failed", "label": "Failed", "format": "int"},
            ]
        },
        {
            "id": "meme_club",
            "label": "MEME CLUB",
            "color": "#34d399",
            "icon": "🗳️",
            "metrics": [
                {"key": "current_winner", "label": "Leader", "format": "handle"},
                {"key": "current_winner_votes", "label": "Votes", "format": "votes"},
                {"key": "current_winner_voters", "label": "Voters", "format": "int"},
                {"key": "active_submissions", "label": "Submissions", "format": "int"},
            ]
        },
        {
            "id": "shill_watch",
            "label": "SHILL WATCH",
            "color": "#fb7185",
            "icon": "🔍",
            "metrics": [
                {"key": "total_shills_caught", "label": "Shills Caught", "format": "int"},
            ]
        },
        {
            "id": "do_something",
            "label": "DO SOMETHING",
            "color": "#fbbf24",
            "icon": "🎯",
            "metrics": [
                {"key": "total_submissions", "label": "Submissions", "format": "int"},
                {"key": "completed", "label": "Completed", "format": "int"},
                {"key": "in_progress", "label": "In Progress", "format": "int"},
                {"key": "ms_won", "label": "MS Wins", "format": "int"},
            ]
        },
        {
            "id": "complaints",
            "label": "COMPLAINTS",
            "color": "#a78bfa",
            "icon": "📞",
            "metrics": [
                {"key": "card_images_posted", "label": "Cards Posted", "format": "int"},
                {"key": "complainers_recruited", "label": "Recruited", "format": "int"},
                {"key": "mentions_handled", "label": "Mentions", "format": "int"},
            ]
        },
        {
            "id": "vetting",
            "label": "VETTING",
            "color": "#fb923c",
            "icon": "👤",
            "metrics": [
                {"key": "total_assessments", "label": "Assessments", "format": "int"},
                {"key": "pitfalls", "label": "Pitfalls", "format": "int"},
                {"key": "weekly_commits", "label": "Commits (7d)", "format": "int"},
            ]
        },
    ]
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    # Write default config
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    return DEFAULT_CONFIG

def load_data():
    """Load the most recent dashboard data."""
    history_file = "/home/prenode/.hermes/profiles/themanager/seen/dashboard_history.json"
    if not os.path.exists(history_file):
        print("ERROR: No dashboard history found. Run dashboard_collector.py first.")
        sys.exit(1)
    
    with open(history_file) as f:
        history = json.load(f)
    
    # Get latest entries for each category
    data = {}
    for category, entries in history.items():
        if entries and isinstance(entries, list):
            # Get the most recent non-error entry
            for entry in reversed(entries):
                if "error" not in entry:
                    data[category] = entry
                    break
    
    return data

def format_value(value, fmt):
    if value is None:
        return "—"
    if fmt == "int":
        return str(int(value))
    if fmt == "votes":
        if isinstance(value, (int, float)):
            if value >= 1_000_000:
                return f"{value/1_000_000:.1f}M"
            elif value >= 1_000:
                return f"{value/1_000:.1f}K"
            return str(int(value))
        return str(value)
    if fmt == "handle":
        return f"@{value}" if value and not str(value).startswith("@") else str(value)
    if fmt == "string":
        return str(value)
    return str(value)

def generate_html(config, data):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    zones = config.get("zones", [])
    
    # Build zone cards HTML
    zone_cards = []
    for zone in zones:
        zone_data = data.get(zone["id"], {})
        color = zone.get("color", "#64748b")
        icon = zone.get("icon", "■")
        label = zone.get("label", zone["id"].upper())
        
        metrics_html = []
        for metric in zone.get("metrics", []):
            key = metric["key"]
            val = zone_data.get(key)
            formatted = format_value(val, metric.get("format", "string"))
            metrics_html.append(f"""
              <div class="metric">
                <div class="metric-value" style="color: {color}">{formatted}</div>
                <div class="metric-label">{metric['label']}</div>
              </div>""")
        
        metrics_str = "".join(metrics_html)
        
        # Determine number of metrics for grid
        n_metrics = len(zone.get("metrics", []))
        if n_metrics <= 1:
            grid_cols = "1"
        elif n_metrics <= 2:
            grid_cols = "2"
        elif n_metrics <= 4:
            grid_cols = "2"
        else:
            grid_cols = "3"
        
        zone_cards.append(f"""
        <div class="zone-card" style="border-color: {color}40;">
          <div class="zone-header" style="border-bottom-color: {color}30;">
            <span class="zone-icon">{icon}</span>
            <span class="zone-label" style="color: {color}">{label}</span>
          </div>
          <div class="zone-metrics" style="grid-template-columns: repeat({grid_cols}, 1fr);">
            {metrics_str}
          </div>
        </div>""")
    
    zones_html = "".join(zone_cards)
    
    # Count zones for grid layout
    n_zones = len(zones)
    if n_zones <= 2:
        zones_grid = "1"
    elif n_zones <= 4:
        zones_grid = "2"
    else:
        zones_grid = "3"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TheManager Scorecard — {today}</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
  font-family: 'JetBrains Mono', monospace;
  background: #020617;
  min-height: 100vh;
  padding: 2rem;
  color: white;
}}

.scorecard {{
  max-width: 1200px;
  margin: 0 auto;
}}

.header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #1e293b;
}}

.header-left {{
  display: flex;
  align-items: center;
  gap: 0.75rem;
}}

.pulse-dot {{
  width: 10px;
  height: 10px;
  background: #22d3ee;
  border-radius: 50%;
  animation: pulse 2s infinite;
}}

@keyframes pulse {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.4; }}
}}

h1 {{
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.025em;
  text-transform: uppercase;
}}

.header-date {{
  color: #475569;
  font-size: 0.875rem;
  font-weight: 500;
}}

.zones {{
  display: grid;
  grid-template-columns: repeat({zones_grid}, 1fr);
  gap: 1rem;
}}

.zone-card {{
  background: rgba(15, 23, 42, 0.6);
  border-radius: 0.75rem;
  border: 1px solid;
  padding: 1.25rem;
  transition: transform 0.2s;
}}

.zone-header {{
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-bottom: 0.75rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid;
}}

.zone-icon {{
  font-size: 1.1rem;
}}

.zone-label {{
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}}

.zone-metrics {{
  display: grid;
  gap: 1rem;
}}

.metric {{
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}}

.metric-value {{
  font-size: 1.5rem;
  font-weight: 800;
  line-height: 1.2;
}}

.metric-label {{
  font-size: 0.65rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}}

.footer {{
  text-align: center;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #1e293b;
  color: #475569;
  font-size: 0.7rem;
}}

.footer a {{
  color: #475569;
  text-decoration: none;
}}
</style>
</head>
<body>
<div class="scorecard">
  <div class="header">
    <div class="header-left">
      <div class="pulse-dot"></div>
      <h1>{config.get('title', 'TheManager Scorecard')}</h1>
    </div>
    <div class="header-date">{today}</div>
  </div>
  
  <div class="zones">
{zones_html}
  </div>
  
  <div class="footer">
    TheManager Scorecard · 6529 Daily Operations · <a href="https://github.com/RegularDad6529/themanager-scorecard">github.com/RegularDad6529/themanager-scorecard</a>
  </div>
</div>
</body>
</html>"""
    
    return html

def screenshot_html(html_path, png_path, width=1200, height=800):
    """Use Playwright to screenshot the HTML to a PNG."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(500)  # Wait for fonts to load
        page.screenshot(path=png_path, full_page=True)
        browser.close()

def main():
    config = load_config()
    data = load_data()
    
    if not data:
        print("ERROR: No data available")
        sys.exit(1)
    
    # Generate HTML
    html = generate_html(config, data)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    html_path = os.path.join(OUTPUT_DIR, f"scorecard_{today}.html")
    png_path = os.path.join(OUTPUT_DIR, f"scorecard_{today}.png")
    
    with open(html_path, "w") as f:
        f.write(html)
    print(f"HTML saved: {html_path}")
    
    # Also save a copy as index.html for git display
    index_path = os.path.join(BASE, "index.html")
    with open(index_path, "w") as f:
        f.write(html)
    print(f"Index saved: {index_path}")
    
    # Save data snapshot
    data_path = os.path.join(DATA_DIR, f"data_{today}.json")
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Data saved: {data_path}")
    
    # Screenshot
    try:
        screenshot_html(os.path.abspath(html_path), os.path.abspath(png_path))
        print(f"PNG saved: {png_path}")
    except Exception as e:
        print(f"Screenshot failed: {e}")
        print("HTML is still available for manual screenshot")

if __name__ == "__main__":
    main()