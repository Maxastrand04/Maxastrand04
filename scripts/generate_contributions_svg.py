#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import urllib.request

USERNAME = "Maxastrand04"
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "github-contributions-dark.svg")

GRAPHQL_QUERY = """
query {
  user(login: "%s") {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          firstDay
          contributionDays {
            contributionCount
            date
            weekday
            contributionLevel
          }
        }
      }
    }
  }
}
""" % USERNAME

COLOR_MAP = {
    "NONE": "#161b22",
    "FIRST_QUARTILE": "#0e4429",
    "SECOND_QUARTILE": "#006d32",
    "THIRD_QUARTILE": "#26a641",
    "FOURTH_QUARTILE": "#39d353"
}

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def fetch_data():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": GRAPHQL_QUERY}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "ContributionGraphGenerator",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    else:
        cmd = ["gh", "api", "graphql", "-f", f"query={GRAPHQL_QUERY}"]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(proc.stdout)
        return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def generate_svg(calendar):
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]
    
    col_width = 13
    row_height = 13
    box_size = 10
    left_padding = 28
    top_padding = 24
    
    num_cols = len(weeks)
    width = left_padding + num_cols * col_width + 10
    height = top_padding + 7 * row_height + 15
    
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="auto">',
        '  <style>',
        '    .label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 9px; fill: #7d8590; }',
        '    .count { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 10px; fill: #7d8590; }',
        '  </style>',
        f'  <rect width="{width}" height="{height}" fill="transparent"/>',
        f'  <text x="{left_padding}" y="12" class="count">{total} contributions in the last year</text>'
    ]
    
    # Days labels
    day_labels = [(1, "Mon"), (3, "Wed"), (5, "Fri")]
    for weekday, text in day_labels:
        y = top_padding + weekday * row_height + 8
        svg_parts.append(f'  <text x="20" y="{y}" class="label" text-anchor="end">{text}</text>')
        
    # Month labels
    prev_month = None
    for i, week in enumerate(weeks):
        first_day = week["firstDay"]
        month_idx = int(first_day.split("-")[1]) - 1
        if month_idx != prev_month and i < num_cols - 2:
            prev_month = month_idx
            x = left_padding + i * col_width
            svg_parts.append(f'  <text x="{x}" y="{top_padding - 6}" class="label">{MONTH_NAMES[month_idx]}</text>')
            
    # Squares
    for col_idx, week in enumerate(weeks):
        x = left_padding + col_idx * col_width
        for day in week["contributionDays"]:
            row_idx = day["weekday"]
            y = top_padding + row_idx * row_height
            color = COLOR_MAP.get(day["contributionLevel"], "#161b22")
            count = day["contributionCount"]
            date = day["date"]
            title = f"{count} contributions on {date}"
            svg_parts.append(
                f'  <rect x="{x}" y="{y}" width="{box_size}" height="{box_size}" rx="2" fill="{color}">'
                f'<title>{title}</title></rect>'
            )
            
    svg_parts.append('</svg>\n')
    return "\n".join(svg_parts)

def main():
    try:
        calendar = fetch_data()
        svg_content = generate_svg(calendar)
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Generated {OUTPUT_PATH}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
