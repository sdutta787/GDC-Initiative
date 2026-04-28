#!/usr/bin/env bash
#
# create-scratch-org.sh
#
# Interactive helper to create a Salesforce scratch org using the sf CLI.
# Designed for developers and non-technical users:
#   - Verifies sf CLI is installed
#   - Walks the user through authorizing a Dev Hub (with guidance to enable it first)
#   - Builds a scratch org definition file interactively (generic defaults, optional
#     features and settings)
#   - Saves the definition file to <repo>/orgs2/
#   - Creates the scratch org, optionally sets a password, and offers to open it
#
# Usage:  bash scripts/scratch-org-setup/create-scratch-org.sh

set -u
set -o pipefail

# ---------- pretty output ----------
if [ -t 1 ]; then
  BOLD=$'\033[1m'; DIM=$'\033[2m'; RED=$'\033[31m'; GREEN=$'\033[32m'
  YELLOW=$'\033[33m'; BLUE=$'\033[34m'; CYAN=$'\033[36m'; RESET=$'\033[0m'
else
  BOLD=""; DIM=""; RED=""; GREEN=""; YELLOW=""; BLUE=""; CYAN=""; RESET=""
fi

say()    { printf "%s\n" "$*"; }
info()   { printf "%s[i]%s %s\n"  "$CYAN"   "$RESET" "$*"; }
ok()     { printf "%s[✓]%s %s\n"  "$GREEN"  "$RESET" "$*"; }
warn()   { printf "%s[!]%s %s\n"  "$YELLOW" "$RESET" "$*"; }
err()    { printf "%s[x]%s %s\n"  "$RED"    "$RESET" "$*" 1>&2; }
header() { printf "\n%s== %s ==%s\n" "$BOLD" "$*" "$RESET"; }

# ---------- paths ----------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
OUT_DIR="$REPO_ROOT/orgs2"
mkdir -p "$OUT_DIR"

DOCS_URL="https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_def_file_config_values.htm"

# ---------- helpers ----------
prompt() {
  # prompt <var_name> <question> [default]
  local __var="$1" __q="$2" __def="${3-}" __ans=""
  if [ -n "$__def" ]; then
    printf "%s%s%s [%s]: " "$BOLD" "$__q" "$RESET" "$__def"
  else
    printf "%s%s%s: " "$BOLD" "$__q" "$RESET"
  fi
  IFS= read -r __ans
  if [ -z "$__ans" ] && [ -n "$__def" ]; then __ans="$__def"; fi
  printf -v "$__var" "%s" "$__ans"
}

confirm() {
  # confirm <question> [default y|n]  -> returns 0 for yes, 1 for no
  local q="$1" def="${2:-n}" ans="" hint
  if [ "$def" = "y" ]; then hint="Y/n"; else hint="y/N"; fi
  printf "%s%s%s (%s): " "$BOLD" "$q" "$RESET" "$hint"
  IFS= read -r ans
  ans="${ans:-$def}"
  case "$ans" in
    y|Y|yes|YES) return 0 ;;
    *)           return 1 ;;
  esac
}

open_url() {
  local url="$1"
  if command -v open >/dev/null 2>&1; then open "$url" >/dev/null 2>&1 &
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$url" >/dev/null 2>&1 &
  else warn "Could not detect a browser launcher. Open this URL manually: $url"
  fi
}

# JSON helpers use python3 (present on macOS). Keep them tiny and pure.
need_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    err "python3 is required by this script (used to safely build JSON). Please install it and retry."
    exit 1
  fi
}

# ---------- prerequisite checks ----------
header "Prerequisite checks"

if ! command -v sf >/dev/null 2>&1; then
  err "The Salesforce CLI ('sf') is not installed or not on PATH."
  say  "Install it from: https://developer.salesforce.com/tools/salesforcecli"
  exit 1
fi
ok "sf CLI found: $(sf --version 2>/dev/null | head -n1)"

need_python

# ---------- Dev Hub step ----------
header "Dev Hub"

cat <<EOF
A scratch org must be created from a Dev Hub org.

${BOLD}Before continuing, make sure Dev Hub is ENABLED in your org:${RESET}
  1. Log in to the org you want to use as Dev Hub (production or Developer Edition).
  2. From Setup, enter ${BOLD}Dev Hub${RESET} in the Quick Find box and select ${BOLD}Dev Hub${RESET}.
  3. Toggle ${BOLD}Enable Dev Hub${RESET} to On. (This cannot be turned off.)
  4. Optional: also enable ${BOLD}Enable Unlocked Packages and Second-Generation Managed Packages${RESET}.

EOF

if confirm "Have you already enabled Dev Hub on the target org?" "y"; then
  :
else
  warn "Please enable Dev Hub first, then re-run this script."
  exit 0
fi

# Show existing Dev Hubs (if any) so the user can pick instead of re-authing.
EXISTING_HUBS=""
ORG_LIST_FILE="/tmp/sf_org_list.$$.json"
if sf org list --json >"$ORG_LIST_FILE" 2>/dev/null; then
  EXISTING_HUBS=$(python3 - "$ORG_LIST_FILE" <<'PY'
import json, sys
path = sys.argv[1]
try:
    with open(path) as f:
        data = json.load(f)
except Exception:
    sys.exit(0)
result = data.get("result", {}) if isinstance(data, dict) else {}
hubs = []
# sf org list --json returns devHubs, nonScratchOrgs, scratchOrgs, etc.
# Also accept any org that has isDevHub=true.
seen = set()
for bucket in ("devHubs", "nonScratchOrgs", "other"):
    for item in (result.get(bucket) or []):
        if not isinstance(item, dict):
            continue
        if bucket == "devHubs" or item.get("isDevHub") is True:
            alias = item.get("alias") or ""
            username = item.get("username") or ""
            key = (alias, username)
            if username and key not in seen:
                seen.add(key)
                hubs.append(f"{alias}\t{username}")
print("\n".join(hubs))
PY
)
  rm -f "$ORG_LIST_FILE"
fi

DEVHUB_ALIAS=""
if [ -n "$EXISTING_HUBS" ]; then
  say ""
  say "${BOLD}Dev Hubs already authorized on this machine:${RESET}"
  printf "%s\n" "$EXISTING_HUBS" | awk -F'\t' 'BEGIN{i=1} {printf "  %d) alias=%s  username=%s\n", i++, ($1==""?"(none)":$1), $2}'
  say ""
  if confirm "Use one of the Dev Hubs above?" "y"; then
    prompt DEVHUB_ALIAS "Enter the alias (or username) of the Dev Hub to use"
  fi
fi

if [ -z "$DEVHUB_ALIAS" ]; then
  say ""
  say "We will now authorize a Dev Hub. A browser window will open for you to log in."
  say "${DIM}Press Enter to accept https://login.salesforce.com.${RESET}"
  prompt DEVHUB_URL   "Dev Hub login URL" "https://login.salesforce.com"
  prompt DEVHUB_ALIAS "Choose an alias to save this Dev Hub as" "DevHub"

  info "Running: sf org login web --instance-url \"$DEVHUB_URL\" --alias \"$DEVHUB_ALIAS\" --set-default-dev-hub"
  if ! sf org login web --instance-url "$DEVHUB_URL" --alias "$DEVHUB_ALIAS" --set-default-dev-hub; then
    err "Dev Hub login failed. Please verify the URL and your credentials, then retry."
    exit 1
  fi
  ok "Dev Hub authorized as '$DEVHUB_ALIAS'."
fi

# ---------- scratch org definition (interactive) ----------
header "Scratch org definition"

prompt ORG_ALIAS      "Scratch org alias"                 "my-scratch-org"
prompt ORG_NAME       "Scratch org display name (orgName)" "$ORG_ALIAS"
prompt ORG_EDITION    "Edition (Developer, Enterprise, Group, Professional, Partner Developer, Partner Enterprise, Partner Group, Partner Professional)" "Developer"
prompt ORG_DURATION   "Duration in days (1-30)"            "7"
while :; do
  prompt ORG_USERNAME "Admin username (leave blank to auto-generate; otherwise must be a valid email)" ""
  if [ -z "$ORG_USERNAME" ]; then break; fi
  if [[ "$ORG_USERNAME" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then break; fi
  warn "Username must be a valid email address (e.g. you@example.com). Please try again."
done
prompt ORG_COUNTRY    "Country (ISO 2-letter code, leave blank for default)" ""

# --- features ---
say ""
say "${BOLD}Features${RESET} let you enable org capabilities like MultiCurrency, Communities, PersonAccounts, etc."
say "You can look them up here: $DOCS_URL"
if confirm "Open the Salesforce docs page in your browser now?" "n"; then
  open_url "$DOCS_URL"
fi

FEATURES_INPUT=""
if confirm "Add features now?" "n"; then
  say "Paste a comma-separated list of feature names. Example:"
  say "  ${DIM}MultiCurrency, Communities, PersonAccounts${RESET}"
  prompt FEATURES_INPUT "Features" ""
fi

# --- settings ---
say ""
say "${BOLD}Settings${RESET} are scratch org definition 'settings' entries, e.g. lightningExperienceSettings.enableS1DesktopEnabled=true."
SETTINGS_INPUT=""
if confirm "Add settings now?" "n"; then
  say "Paste a comma-separated list of key=value pairs using dot-notation. Example:"
  say "  ${DIM}lightningExperienceSettings.enableS1DesktopEnabled=true, chatterSettings.enableChatter=true${RESET}"
  say "Values are auto-converted: true/false → boolean, digits → number, anything else → string."
  prompt SETTINGS_INPUT "Settings" ""
fi

# ---------- build the JSON definition ----------
DEF_FILE="$OUT_DIR/${ORG_ALIAS}-scratch-def.json"

need_python

write_def_file() {
python3 - "$DEF_FILE" "$ORG_NAME" "$ORG_EDITION" "$ORG_USERNAME" "$ORG_COUNTRY" "$FEATURES_INPUT" "$SETTINGS_INPUT" <<'PY'
import json, sys, os, re

out_path, org_name, edition, username, country, features_raw, settings_raw = sys.argv[1:8]

def split_csv(s):
    return [p.strip() for p in s.split(",") if p.strip()]

def coerce(val):
    v = val.strip()
    low = v.lower()
    if low == "true":  return True
    if low == "false": return False
    if low == "null":  return None
    if re.fullmatch(r"-?\d+", v):        return int(v)
    if re.fullmatch(r"-?\d+\.\d+", v):   return float(v)
    # strip surrounding quotes if present
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        return v[1:-1]
    return v

definition = {
    "orgName": org_name,
    "edition": edition,
}
if username:
    definition["username"] = username
if country:
    definition["country"] = country

features = split_csv(features_raw)
if features:
    definition["features"] = features

settings = {}
errors = []
for pair in split_csv(settings_raw):
    if "=" not in pair:
        errors.append(f"skipped (no '='): {pair}")
        continue
    key, val = pair.split("=", 1)
    path = [p for p in key.strip().split(".") if p]
    if not path:
        errors.append(f"skipped (empty key): {pair}")
        continue
    node = settings
    for segment in path[:-1]:
        node = node.setdefault(segment, {})
        if not isinstance(node, dict):
            errors.append(f"skipped (conflicts with earlier value): {pair}")
            node = None
            break
    if node is None:
        continue
    node[path[-1]] = coerce(val)

if settings:
    definition["settings"] = settings

os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(definition, f, indent=2)
    f.write("\n")

if errors:
    sys.stderr.write("\n".join("WARN: " + e for e in errors) + "\n")
PY
}

write_def_file
ok "Wrote scratch org definition to: $DEF_FILE"
say ""
say "${DIM}--- definition preview ---${RESET}"
cat "$DEF_FILE"
say "${DIM}--------------------------${RESET}"
say ""

if ! confirm "Proceed with creating the scratch org using this definition?" "y"; then
  warn "Aborted before creating the scratch org. Definition file kept at: $DEF_FILE"
  exit 0
fi

# ---------- create scratch org ----------
header "Creating scratch org"

SET_DEFAULT="n"
if confirm "Set this scratch org as the default for this project?" "y"; then
  SET_DEFAULT="y"
fi

build_create_cmd() {
  CREATE_CMD=(sf org create scratch
    --definition-file "$DEF_FILE"
    --alias "$ORG_ALIAS"
    --duration-days "$ORG_DURATION"
    --wait 20)
  if [ -n "$DEVHUB_ALIAS" ]; then
    CREATE_CMD+=(--target-dev-hub "$DEVHUB_ALIAS")
  fi
  if [ "$SET_DEFAULT" = "y" ]; then
    CREATE_CMD+=(--set-default)
  fi
}

CREATE_LOG="/tmp/sf_create.$$.log"
while :; do
  build_create_cmd
  info "Running: ${CREATE_CMD[*]}"
  if "${CREATE_CMD[@]}" 2>&1 | tee "$CREATE_LOG"; then
    rm -f "$CREATE_LOG"
    break
  fi

  if grep -q "INVALID_EMAIL_ADDRESS" "$CREATE_LOG"; then
    warn "The username in the definition was rejected as an invalid email address."
    while :; do
      prompt ORG_USERNAME "Enter a valid admin username (must be an email, e.g. you@example.com)" ""
      if [[ "$ORG_USERNAME" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then break; fi
      warn "Not a valid email address. Please try again."
    done
    write_def_file
    ok "Updated definition with new username. Retrying..."
    continue
  fi

  err "Scratch org creation failed. Check the output above for details."
  rm -f "$CREATE_LOG"
  exit 1
done
ok "Scratch org '$ORG_ALIAS' created."

# ---------- password ----------
SCRATCH_USERNAME=""
SCRATCH_PASSWORD=""
SCRATCH_LOGIN_URL=""

if confirm "Generate a password for the scratch org user?" "y"; then
  if sf org generate password --target-org "$ORG_ALIAS" >/dev/null; then
    ok "Password generated."
  else
    warn "Could not generate a password automatically."
  fi
fi

# Pull display info (username, instanceUrl, password) in JSON.
USER_FILE="/tmp/sf_user.$$.json"
if sf org display user --target-org "$ORG_ALIAS" --json >"$USER_FILE" 2>/dev/null; then
  USER_INFO=$(python3 - "$USER_FILE" <<'PY'
import json, sys
path = sys.argv[1]
try:
    with open(path) as f:
        data = json.load(f).get("result", {}) or {}
except Exception:
    data = {}
print(data.get("username") or "")
print(data.get("password") or "")
print(data.get("instanceUrl") or data.get("loginUrl") or "")
PY
)
  SCRATCH_USERNAME=$(printf "%s\n" "$USER_INFO" | sed -n '1p')
  SCRATCH_PASSWORD=$(printf "%s\n" "$USER_INFO" | sed -n '2p')
  SCRATCH_LOGIN_URL=$(printf "%s\n" "$USER_INFO" | sed -n '3p')
  rm -f "$USER_FILE"
fi

header "Scratch org ready"
printf "  %-12s %s\n" "Alias:"     "$ORG_ALIAS"
printf "  %-12s %s\n" "Username:"  "${SCRATCH_USERNAME:-(run: sf org display user --target-org $ORG_ALIAS)}"
printf "  %-12s %s\n" "Password:"  "${SCRATCH_PASSWORD:-(not set)}"
printf "  %-12s %s\n" "Login URL:" "${SCRATCH_LOGIN_URL:-(see sf org display)}"
printf "  %-12s %s\n" "Def file:"  "$DEF_FILE"
say ""

if confirm "Open the scratch org in your browser now?" "y"; then
  if ! sf org open --target-org "$ORG_ALIAS"; then
    warn "Could not open the org. You can run: sf org open --target-org $ORG_ALIAS"
  fi
fi

ok "Done."
