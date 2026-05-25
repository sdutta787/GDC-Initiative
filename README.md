# Scratch Org Creator

An interactive tool for creating Salesforce scratch orgs with a modern web-based UI. No more memorizing feature names or manually editing JSON definition files.

## Quick Start

```bash
bash create-scratch-org.sh
```

This opens an interactive web UI in your browser where you can configure and create scratch orgs visually.

## Prerequisites

| Requirement | How to Install |
|---|---|
| **Salesforce CLI (`sf`)** | [Install Guide](https://developer.salesforce.com/tools/salesforcecli) |
| **Python 3** | Pre-installed on macOS. Windows: [python.org](https://www.python.org/downloads/) |
| **Dev Hub enabled** | Setup > Dev Hub > Enable Dev Hub (in your production or Developer Edition org) |

Flask (the web framework) is installed automatically on first run — no manual setup needed.

## Usage

### Web UI Mode (default)

```bash
bash create-scratch-org.sh
```

The browser opens with a step-by-step wizard:

1. **Dev Hub** — Select or enter your authorized Dev Hub
2. **Definition** — Set org alias, edition, duration, username, country
3. **Features** — Search and select from 296 official Salesforce features (grouped by category)
4. **Settings** — Toggle common settings or add custom dot-notation settings
5. **Create** — Review the JSON definition and create the org with live console output

### CLI Mode

```bash
bash create-scratch-org.sh --cli
```

Uses the traditional terminal-based interactive flow (no browser needed).

### Help

```bash
bash create-scratch-org.sh --help
```

## Features

- **Searchable Feature Picker** — All 296 features from official Salesforce documentation (Spring '26, API v66.0) organized into 20 categories
- **Live JSON Preview** — See the scratch org definition file update in real-time as you make selections
- **Real-time Console Output** — Watch the `sf org create scratch` command output streamed live to the browser
- **Auto-detect Dev Hubs** — Lists already-authorized Dev Hubs so you don't have to remember aliases
- **Feature Value Support** — Features that require numeric values (like `FieldService:5`) get dedicated input fields with valid range hints
- **Common Settings Toggles** — One-click toggles for Lightning Experience, Chatter, Enhanced Notes, Path Assistant, etc.
- **Copy/Download JSON** — Export the generated definition file without creating the org
- **Graceful Fallback** — If the web UI can't start, the script automatically falls back to CLI mode

## Feature Categories

Features are organized into these groups for easy discovery:

| Category | Examples |
|---|---|
| Core Platform | API, AuthorApex, DebugApex, PlatformCache, RecordTypes |
| Sales Cloud | SalesCloudEinstein, HighVelocitySales, PipelineInspection, PersonAccounts |
| Service Cloud | ServiceCloud, LiveAgent, Knowledge, CaseClassification, Chatbot |
| Commerce | B2BCommerce, B2CCommerceGMV, OrderManagement, CPQ |
| Experience Cloud | Communities, Sites, ExternalIdentityLogin |
| Analytics & Einstein | DevelopmentWave, EinsteinAnalyticsPlus, Einstein1AIPlatform |
| Field Service | FieldService, LightningScheduler, FieldServiceDispatcherUser |
| Automation | Workflow, ProcessBuilder, BusinessRulesEngine, DecisionTable |
| Data & Integration | ChangeDataCapture, PlatformConnect, StreamingAPI, CustomerDataPlatform |
| Security & Identity | PlatformEncryption, MutualAuthentication, FieldAuditTrail |
| Marketing | MarketingCloud, MarketingUser |
| Industries | Health Cloud, Financial Services, Manufacturing, Education, Public Sector, Nonprofit |

## Project Structure

```
.
├── create-scratch-org.sh            # Main entry point (run this)
├── scratch-org-ui/
│   ├── app.py                       # Flask web server
│   ├── features.json                # 296 features from Salesforce docs
│   ├── requirements.txt             # Python dependencies
│   ├── templates/
│   │   └── index.html               # Web UI (single-page app)
│   └── vendor/                      # Auto-installed Flask (gitignored)
└── scratch-orgs-templates/          # Generated definition files saved here
```

## Updating the Features List

The features list in `scratch-org-ui/features.json` is sourced from the [official Salesforce documentation](https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_def_file_config_values.htm). To update it when new Salesforce releases add features:

1. Check the docs page above for new entries
2. Add them to `features.json` following the existing format:

```json
{
  "name": "FeatureName",
  "description": "What it does",
  "category": "Category Name",
  "requiresValue": false
}
```

For features that need a numeric value:

```json
{
  "name": "FeatureName",
  "description": "What it does",
  "category": "Category Name",
  "requiresValue": true,
  "valueRange": "1-25"
}
```

## Troubleshooting

| Issue | Solution |
|---|---|
| `sf` command not found | Install Salesforce CLI: `npm install -g @salesforce/cli` |
| Flask won't install (SSL error) | Run manually: `pip3 install --trusted-host pypi.org flask` |
| "Dev Hub is not enabled" | In your org: Setup > Dev Hub > Toggle On |
| Browser doesn't open | Copy the URL from the terminal and open manually |
| Port already in use | The script auto-selects a random available port |
| Web UI won't start | Use `--cli` flag for terminal mode: `bash create-scratch-org.sh --cli` |

## Additional Resources

- [Salesforce DX Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm)
- [Scratch Org Definition File Reference](https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_def_file.htm)
- [Supported Features and Settings](https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_def_file_config_values.htm)
- [Salesforce CLI Command Reference](https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm)
