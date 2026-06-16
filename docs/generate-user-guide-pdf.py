#!/usr/bin/env python3
"""Generate a styled HTML User Guide with embedded screenshots, then convert to PDF."""

import base64
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
IMAGES_DIR = SCRIPT_DIR / "images"
OUTPUT_HTML = SCRIPT_DIR / "USER_GUIDE.html"
OUTPUT_PDF = SCRIPT_DIR / "USER_GUIDE.pdf"

IMAGES = {
    "step1-devhub": IMAGES_DIR / "step1-devhub.png",
    "step2-definition": IMAGES_DIR / "step2-definition.png",
    "step3-features-search": IMAGES_DIR / "step3-features-search.png",
    "step3-features-values": IMAGES_DIR / "step3-features-values.png",
    "step4-settings": IMAGES_DIR / "step4-settings.png",
    "step4-custom-settings": IMAGES_DIR / "step4-custom-settings.png",
    "step5-create": IMAGES_DIR / "step5-create.png",
}


def embed_image(path: Path) -> str:
    if not path.exists():
        return ""
    data = base64.b64encode(path.read_bytes()).decode()
    return f'<img src="data:image/png;base64,{data}" class="screenshot" />'


def build_html() -> str:
    imgs = {k: embed_image(v) for k, v in IMAGES.items()}

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>Scratch Org Creator — User Guide</title>
<style>
  @page {{ margin: 20mm 15mm; }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #1a1a2e;
    line-height: 1.6;
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 30px;
    background: #fff;
  }}
  h1 {{
    font-size: 2.2em;
    color: #0d1b2a;
    border-bottom: 3px solid #4361ee;
    padding-bottom: 12px;
    margin-bottom: 8px;
  }}
  h2 {{
    font-size: 1.6em;
    color: #1b263b;
    margin-top: 50px;
    border-left: 5px solid #4361ee;
    padding-left: 14px;
  }}
  h3 {{
    font-size: 1.2em;
    color: #415a77;
    margin-top: 30px;
  }}
  .subtitle {{
    font-size: 1.1em;
    color: #555;
    margin-bottom: 30px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 0.92em;
  }}
  th, td {{
    border: 1px solid #ddd;
    padding: 10px 12px;
    text-align: left;
  }}
  th {{
    background: #f0f4ff;
    font-weight: 600;
  }}
  tr:nth-child(even) {{ background: #fafbff; }}
  .screenshot {{
    display: block;
    max-width: 100%;
    margin: 20px auto;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  }}
  code {{
    background: #f0f2f5;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.9em;
    font-family: 'SF Mono', Menlo, monospace;
  }}
  pre {{
    background: #1e1e2e;
    color: #cdd6f4;
    padding: 16px 20px;
    border-radius: 8px;
    overflow-x: auto;
    font-size: 0.88em;
    line-height: 1.5;
  }}
  .tip {{
    background: #eef6ff;
    border-left: 4px solid #4361ee;
    padding: 12px 16px;
    border-radius: 4px;
    margin: 16px 0;
  }}
  .tip strong {{ color: #4361ee; }}
  .warning {{
    background: #fff8e6;
    border-left: 4px solid #f0a500;
    padding: 12px 16px;
    border-radius: 4px;
    margin: 16px 0;
  }}
  .warning strong {{ color: #b87b00; }}
  .step-badge {{
    display: inline-block;
    background: #4361ee;
    color: white;
    font-weight: 700;
    font-size: 0.85em;
    padding: 3px 10px;
    border-radius: 12px;
    margin-right: 8px;
  }}
  .page-break {{ page-break-before: always; }}
  ul {{ padding-left: 24px; }}
  li {{ margin-bottom: 6px; }}
</style>
</head>
<body>

<h1>Scratch Org Creator</h1>
<p class="subtitle">User Guide — Step-by-step walkthrough for creating Salesforce scratch orgs</p>

<hr/>

<h2>Prerequisites</h2>
<p>Before you begin, ensure the following are installed and configured on your machine:</p>

<table>
<tr><th>#</th><th>Requirement</th><th>How to Verify</th><th>Install Instructions</th></tr>
<tr><td>1</td><td><strong>Salesforce CLI (sf)</strong></td><td>Run <code>sf --version</code></td><td><a href="https://developer.salesforce.com/tools/salesforcecli">Download</a> or <code>npm install -g @salesforce/cli</code></td></tr>
<tr><td>2</td><td><strong>Python 3</strong></td><td>Run <code>python3 --version</code></td><td>Pre-installed on macOS. Windows: <a href="https://www.python.org/downloads/">python.org</a></td></tr>
<tr><td>3</td><td><strong>Dev Hub Enabled</strong></td><td>Setup &rarr; Dev Hub &rarr; "Enabled"</td><td>Setup &rarr; Dev Hub &rarr; Toggle "Enable Dev Hub" ON</td></tr>
<tr><td>4</td><td><strong>Web Browser</strong></td><td>Chrome, Safari, Firefox, or Edge</td><td>Already available</td></tr>
</table>

<h3>Files Required</h3>
<p>You need <strong>one single file</strong> to get started:</p>
<table>
<tr><th>File</th><th>Description</th></tr>
<tr><td><code>scratch-org-creator.sh</code></td><td>Self-contained installer script (~191 KB). Contains everything — no other files needed.</td></tr>
</table>

<p><em>Alternatively</em>, if working from the source repository:</p>
<table>
<tr><th>File / Folder</th><th>Description</th></tr>
<tr><td><code>create-scratch-org.sh</code></td><td>Main launcher script</td></tr>
<tr><td><code>scratch-org-ui/app.py</code></td><td>Python Flask backend</td></tr>
<tr><td><code>scratch-org-ui/features.json</code></td><td>296 Salesforce features database</td></tr>
<tr><td><code>scratch-org-ui/settings.json</code></td><td>39 categorized org settings</td></tr>
<tr><td><code>scratch-org-ui/templates/index.html</code></td><td>Web UI interface</td></tr>
</table>

<hr/>

<h2>Getting Started</h2>
<p>Open your terminal and run:</p>
<pre>bash scratch-org-creator.sh</pre>

<p>The tool will automatically:</p>
<ul>
<li>Verify Python 3 and Salesforce CLI are installed</li>
<li>Install Flask (first time only, takes a few seconds)</li>
<li>Start a local web server on port 8484</li>
<li>Open your default browser to the interactive UI</li>
</ul>

<pre>
&#x2554;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2557;
&#x2551;      Scratch Org Creator  v1.0       &#x2551;
&#x255A;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x255D;

[i] Starting web server on http://localhost:8484 ...
[&#x2713;] Web UI running at: http://localhost:8484

Press Ctrl+C to stop the server when done.
</pre>

<div class="page-break"></div>

<h2><span class="step-badge">Step 1</span> Select Your Dev Hub</h2>

{imgs["step1-devhub"]}

<p><strong>What is a Dev Hub?</strong><br/>
A Dev Hub is the Salesforce org that manages and creates your scratch orgs. You must have one authorized before proceeding.</p>

<h3>What to do:</h3>
<ol>
<li><strong>If your Dev Hub is already listed</strong> — Click on it (e.g., "CCIPracticeDevHub", "DevHub", "Th-DevHub"). The alias auto-fills below.</li>
<li><strong>If no Dev Hubs appear</strong> — Use the "Authorize a New Dev Hub" section:
  <ul>
    <li>Enter an alias (any name you choose)</li>
    <li>Select login type: "Production / Developer" for most orgs</li>
    <li>Click <strong>Authorize Dev Hub</strong></li>
    <li>A Salesforce login page opens — log in and grant access</li>
    <li>Once done, your org appears in the list</li>
  </ul>
</li>
<li>Click <strong>Next: Definition</strong> to continue.</li>
</ol>

<div class="tip"><strong>Tip:</strong> You can have multiple Dev Hubs authorized. Pick the one appropriate for your project.</div>

<div class="page-break"></div>

<h2><span class="step-badge">Step 2</span> Configure Org Definition</h2>

{imgs["step2-definition"]}

<p>This step defines the basic properties of your scratch org.</p>

<h3>Field Reference:</h3>
<table>
<tr><th>Field</th><th>What to Enter</th><th>Required?</th></tr>
<tr><td><strong>Scratch Org Alias</strong></td><td>Short identifier (e.g., "my-feature-org")</td><td>Yes</td></tr>
<tr><td><strong>Org Display Name</strong></td><td>Human-readable name (e.g., "Feature Testing")</td><td>Yes</td></tr>
<tr><td><strong>Edition</strong></td><td>Developer, Enterprise, Group, or Professional</td><td>Yes</td></tr>
<tr><td><strong>Duration (days)</strong></td><td>1–30 days. Drag the slider to set.</td><td>Yes</td></tr>
<tr><td><strong>Admin Username</strong></td><td>Leave blank to auto-generate, or enter a valid email format</td><td>No</td></tr>
<tr><td><strong>Country Code</strong></td><td>2-letter ISO code (US, IN, AU, etc.)</td><td>No</td></tr>
<tr><td><strong>Description</strong></td><td>Brief purpose of the org</td><td>No</td></tr>
<tr><td><strong>Language</strong></td><td>Language code (e.g., "en_US")</td><td>No</td></tr>
<tr><td><strong>Release</strong></td><td>Default (Current), Previous, or Preview</td><td>No</td></tr>
<tr><td><strong>Include sample data</strong></td><td>Toggle ON to pre-populate sample records</td><td>No</td></tr>
</table>

<div class="tip"><strong>Tip:</strong> Use "Developer" edition for standard development. Choose "Enterprise" only when you need to test Enterprise-specific features. A duration of 7–14 days is typical.</div>

<p>Click <strong>Next: Features</strong> to continue.</p>

<div class="page-break"></div>

<h2><span class="step-badge">Step 3</span> Select Features</h2>

{imgs["step3-features-search"]}

<p><strong>What are Features?</strong><br/>
Features enable specific Salesforce capabilities in your scratch org. There are <strong>296 features</strong> available, organized into categories like Analytics, Sales Cloud, Service Cloud, Marketing, etc.</p>

<h3>What to do:</h3>
<ol>
<li><strong>Click the search box</strong> — It says "Type to search and select features"</li>
<li><strong>Search or browse</strong> — Type a keyword (e.g., "Analytics") to filter, or scroll through categories</li>
<li><strong>Click a feature</strong> to select it — it appears as a blue tag in the input</li>
<li><strong>Remove a feature</strong> by clicking the &times; on its tag</li>
</ol>

<p>The counter (e.g., "4 selected") updates as you add/remove features. The features list shows the feature name and a brief description for each option.</p>

<h3>Features That Require Values</h3>

{imgs["step3-features-values"]}

<p>Some features need a numeric parameter. When you select one (like <strong>AddInsightsQueryLimit</strong>), a "Feature Values" section appears below with an input field showing the valid range (e.g., 1–30).</p>

<div class="tip"><strong>Tip:</strong> The JSON Preview on the right updates live as you make selections. Features with values appear as <code>"FeatureName:value"</code> in the output.</div>

<p>Click <strong>Next: Settings</strong> to continue.</p>

<div class="page-break"></div>

<h2><span class="step-badge">Step 4</span> Configure Settings</h2>

{imgs["step4-settings"]}

<p><strong>What are Settings?</strong><br/>
Settings control specific behaviors of your org — like enabling Lightning Experience, Chatter, encryption, password policies, etc.</p>

<h3>What to do:</h3>
<ol>
<li><strong>Browse by category</strong> — Click any category header to expand/collapse it</li>
<li><strong>Toggle ON/OFF</strong> — Each setting has a toggle switch:
  <ul>
    <li><strong>Dark grey (off)</strong> = not included in definition</li>
    <li><strong>Purple/blue (on)</strong> = will be enabled</li>
  </ul>
</li>
<li><strong>Use search</strong> — Type in the search box to filter settings across all categories</li>
<li><strong>Check badge counts</strong> — The counter (e.g., "2/3") shows enabled vs total settings per category</li>
</ol>

<p>The "5 enabled" badge at the top shows total active settings across all categories.</p>

<h3>Custom Settings</h3>

{imgs["step4-custom-settings"]}

<p>For settings not in the pre-built list:</p>
<ol>
<li>Scroll to the "Custom Settings" section at the bottom</li>
<li>Click <strong>+ Add Row</strong></li>
<li>Enter the <strong>dot-notation path</strong> in the left field (e.g., <code>caseSettings.systemUserEmail</code>)</li>
<li>Enter the <strong>value</strong> in the right field (e.g., <code>support@acme.com</code>)</li>
<li>Add additional rows as needed</li>
<li>Click &times; to remove any row</li>
</ol>

<div class="warning"><strong>Note:</strong> Custom setting paths must follow Salesforce's scratch org definition format. Refer to <a href="https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_def_file.htm">Salesforce documentation</a> for valid paths.</div>

<p>Click <strong>Next: Review &amp; Create</strong> to continue.</p>

<div class="page-break"></div>

<h2><span class="step-badge">Step 5</span> Review &amp; Create</h2>

{imgs["step5-create"]}

<h3>What to do:</h3>
<ol>
<li><strong>Review the JSON Preview</strong> — The right panel shows the complete scratch org definition that will be used</li>
<li><strong>Set optional toggles:</strong>
  <ul>
    <li><strong>Set as default scratch org</strong> — ON if this should become your active working org</li>
    <li><strong>Generate a password</strong> — ON to auto-generate login credentials for the admin user</li>
  </ul>
</li>
<li><strong>Click "Create Scratch Org"</strong></li>
</ol>

<h3>During Creation:</h3>
<p>The button changes to "Creating..." and you'll see real-time console output showing progress:</p>
<ul>
<li><strong>Prepare Request</strong> — Building the org request</li>
<li><strong>Send Request</strong> — Sending to Salesforce (typically 10-15 seconds)</li>
<li><strong>Wait For Org</strong> — Salesforce is provisioning your org</li>
<li><strong>Available</strong> — Org has been created</li>
<li><strong>Authenticate</strong> — Setting up authentication</li>
<li><strong>Deploy Settings</strong> — Applying your selected settings</li>
<li><strong>Done</strong> — Org is ready to use!</li>
</ul>

<h3>After Success:</h3>
<ul>
<li>A green card appears with your org credentials (username, password, instance URL)</li>
<li>Click <strong>"Open Org in Browser"</strong> to jump into the new org immediately</li>
<li>Use <strong>"Copy JSON"</strong> or <strong>"Download"</strong> buttons to save the definition file for reuse</li>
</ul>

<hr/>

<h2>Session Recovery</h2>
<p>If you accidentally close the browser or the server stops mid-configuration:</p>
<ul>
<li><strong>Your progress is automatically saved</strong> — All form data is stored locally</li>
<li><strong>Just restart the script</strong> — Run <code>bash scratch-org-creator.sh</code> again</li>
<li><strong>Previous selections are restored</strong> — A "Session Restored" banner appears</li>
<li>You'll be returned to the exact step you were on with all data intact</li>
</ul>
<p>To start completely fresh, click "Start Fresh" on the restore banner.</p>

<hr/>

<h2>Troubleshooting</h2>
<table>
<tr><th>Problem</th><th>Solution</th></tr>
<tr><td>"sf command not found"</td><td>Install Salesforce CLI: <code>npm install -g @salesforce/cli</code></td></tr>
<tr><td>"python3 not found"</td><td>Install Python 3 from <a href="https://www.python.org/downloads/">python.org</a></td></tr>
<tr><td>"Could not install Flask"</td><td>Run manually: <code>pip3 install flask</code></td></tr>
<tr><td>Browser doesn't open</td><td>Copy the URL from terminal output and open manually</td></tr>
<tr><td>"Dev Hub is not enabled"</td><td>In your Salesforce org: Setup &rarr; Dev Hub &rarr; Toggle ON</td></tr>
<tr><td>Org creation fails</td><td>Check console output for error details — common causes: expired auth, invalid features</td></tr>
<tr><td>Port already in use</td><td>Kill existing servers: <code>kill $(lsof -t -i:8484)</code></td></tr>
</table>

<hr/>
<p style="text-align: center; color: #888; font-size: 0.85em; margin-top: 40px;">
  Scratch Org Creator &mdash; User Guide &mdash; Generated {__import__('datetime').date.today().strftime('%B %d, %Y') if False else "May 2026"}
</p>

</body>
</html>"""


def main():
    import datetime
    html = build_html().replace("May 2026", datetime.date.today().strftime("%B %d, %Y"))

    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"[OK] HTML written to: {OUTPUT_HTML}")

    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
    ]

    chrome = None
    for p in chrome_paths:
        if Path(p).exists():
            chrome = p
            break

    if not chrome:
        print("[!] Chrome not found. HTML generated, but cannot auto-convert to PDF.")
        print(f"    Open {OUTPUT_HTML} in a browser and print to PDF manually.")
        sys.exit(0)

    print("[...] Converting to PDF via Chrome headless...")
    result = subprocess.run(
        [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--print-to-pdf={OUTPUT_PDF}",
            "--print-to-pdf-no-header",
            str(OUTPUT_HTML),
        ],
        capture_output=True,
        text=True,
    )

    if OUTPUT_PDF.exists():
        size_kb = OUTPUT_PDF.stat().st_size / 1024
        print(f"[OK] PDF written to: {OUTPUT_PDF} ({size_kb:.0f} KB)")
    else:
        print(f"[!] PDF conversion failed: {result.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    main()
