#!/usr/bin/env python3
"""
Flask app that serves an interactive web UI for creating Salesforce scratch orgs.
Launched by create-scratch-org.sh --web (default mode).
"""

import json
import os
import queue
import re
import signal
import subprocess
import sys
import threading
import uuid
from pathlib import Path

# Support local vendor directory for Flask install
VENDOR_DIR = Path(__file__).resolve().parent / "vendor"
if VENDOR_DIR.exists():
    sys.path.insert(0, str(VENDOR_DIR))

from flask import Flask, Response, jsonify, render_template, request

app = Flask(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
OUT_DIR = REPO_ROOT / "scratch-orgs-templates"
FEATURES_FILE = SCRIPT_DIR / "features.json"
SETTINGS_FILE = SCRIPT_DIR / "settings.json"

jobs: dict[str, dict] = {}


def load_features():
    with open(FEATURES_FILE) as f:
        return json.load(f)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/features")
def get_features():
    return jsonify(load_features())


@app.route("/api/settings")
def get_settings():
    with open(SETTINGS_FILE) as f:
        return jsonify(json.load(f))


@app.route("/api/devhubs")
def get_devhubs():
    """List Dev Hubs already authorized on this machine."""
    try:
        result = subprocess.run(
            ["sf", "org", "list", "--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return jsonify([])

        data = json.loads(result.stdout)
        result_data = data.get("result", {})
        hubs = []
        seen = set()

        for bucket in ("devHubs", "nonScratchOrgs", "other"):
            for item in (result_data.get(bucket) or []):
                if not isinstance(item, dict):
                    continue
                if bucket == "devHubs" or item.get("isDevHub") is True:
                    alias = item.get("alias") or ""
                    username = item.get("username") or ""
                    if username and (alias, username) not in seen:
                        seen.add((alias, username))
                        hubs.append({"alias": alias, "username": username})

        return jsonify(hubs)
    except Exception:
        return jsonify([])


@app.route("/api/authorize", methods=["POST"])
def authorize_devhub():
    """Authorize a new Dev Hub via sf org login web (opens browser for OAuth)."""
    data = request.json or {}
    alias = data.get("alias", "DevHub")
    login_url = data.get("loginUrl", "https://login.salesforce.com")

    try:
        result = subprocess.run(
            [
                "sf", "org", "login", "web",
                "--instance-url", login_url,
                "--alias", alias,
                "--set-default-dev-hub",
            ],
            capture_output=True, text=True, timeout=300
        )

        if result.returncode == 0:
            return jsonify({"success": True, "alias": alias, "message": f"Dev Hub '{alias}' authorized successfully."})
        else:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Authorization failed."
            return jsonify({"success": False, "message": error_msg})
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "message": "Authorization timed out. Please try again."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/api/preview", methods=["POST"])
def preview():
    """Generate a scratch org definition JSON preview."""
    data = request.json
    definition = build_definition(data)
    return jsonify(definition)


@app.route("/api/create", methods=["POST"])
def create_org():
    """Start scratch org creation and return a job ID for streaming output."""
    data = request.json

    if data.get("_action") == "open":
        alias = data.get("alias", "")
        subprocess.Popen(["sf", "org", "open", "--target-org", alias])
        return jsonify({"ok": True})

    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "status": "running",
        "queue": queue.Queue(),
        "data": data,
    }

    thread = threading.Thread(target=run_create_job, args=(job_id, data), daemon=True)
    thread.start()

    return jsonify({"jobId": job_id})


@app.route("/api/stream/<job_id>")
def stream(job_id):
    """SSE endpoint to stream job output to the browser."""
    if job_id not in jobs:
        return Response("Job not found", status=404)

    def generate():
        q = jobs[job_id]["queue"]
        while True:
            try:
                msg = q.get(timeout=60)
                if msg is None:
                    yield f"data: {json.dumps({'type': 'done', 'status': jobs[job_id]['status']})}\n\n"
                    break
                yield f"data: {json.dumps(msg)}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/shutdown", methods=["POST"])
def shutdown():
    """Gracefully shut down the server."""
    os.kill(os.getpid(), signal.SIGTERM)
    return jsonify({"ok": True})


def build_definition(data):
    """Build a scratch org definition dict from form data."""
    definition = {
        "orgName": data.get("orgName", "my-scratch-org"),
        "edition": data.get("edition", "Developer"),
    }

    if data.get("username"):
        definition["username"] = data["username"]
    if data.get("country"):
        definition["country"] = data["country"]
    if data.get("description"):
        definition["description"] = data["description"]
    if data.get("language"):
        definition["language"] = data["language"]
    if data.get("release"):
        definition["release"] = data["release"]
    if data.get("hasSampleData"):
        definition["hasSampleData"] = True

    features = data.get("features", [])
    if features:
        definition["features"] = features

    settings_raw = data.get("settings", {})
    if settings_raw:
        definition["settings"] = settings_raw

    return definition


def run_create_job(job_id, data):
    """Execute scratch org creation in a background thread."""
    q = jobs[job_id]["queue"]

    def emit(msg_type, text):
        q.put({"type": msg_type, "text": text})

    try:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        alias = data.get("alias", "my-scratch-org")
        def_file = OUT_DIR / f"{alias}-scratch-def.json"

        definition = build_definition(data)
        with open(def_file, "w") as f:
            json.dump(definition, f, indent=2)
            f.write("\n")

        emit("info", f"Wrote definition to: {def_file}")
        emit("info", f"Definition:\n{json.dumps(definition, indent=2)}")

        duration = data.get("duration", "7")
        devhub = data.get("devHub", "")
        set_default = data.get("setDefault", True)

        cmd = [
            "sf", "org", "create", "scratch",
            "--definition-file", str(def_file),
            "--alias", alias,
            "--duration-days", str(duration),
            "--wait", "20",
        ]

        if devhub:
            cmd += ["--target-dev-hub", devhub]
        if set_default:
            cmd.append("--set-default")

        emit("info", f"Running: {' '.join(cmd)}")

        ansi_re = re.compile(r'\x1b\[[0-9;]*[A-Za-z]|\x1b\].*?\x07|\r')

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, env={**os.environ, "FORCE_COLOR": "0", "NO_COLOR": "1"}
        )

        for line in proc.stdout:
            clean = ansi_re.sub('', line.rstrip("\n")).strip()
            if clean:
                emit("output", clean)

        proc.wait()

        if proc.returncode != 0:
            emit("error", f"Scratch org creation failed (exit code {proc.returncode}).")
            jobs[job_id]["status"] = "failed"
            q.put(None)
            return

        emit("success", f"Scratch org '{alias}' created successfully!")

        if data.get("generatePassword", True):
            emit("info", "Generating password...")
            pw_result = subprocess.run(
                ["sf", "org", "generate", "password", "--target-org", alias],
                capture_output=True, text=True
            )
            if pw_result.returncode == 0:
                emit("success", "Password generated.")
            else:
                emit("warning", "Could not generate password automatically.")

        emit("info", "Fetching org details...")
        display_result = subprocess.run(
            ["sf", "org", "display", "user", "--target-org", alias, "--json"],
            capture_output=True, text=True
        )

        if display_result.returncode == 0:
            try:
                user_data = json.loads(display_result.stdout).get("result", {})
                details = {
                    "username": user_data.get("username", ""),
                    "password": user_data.get("password", ""),
                    "instanceUrl": user_data.get("instanceUrl") or user_data.get("loginUrl", ""),
                    "alias": alias,
                    "defFile": str(def_file),
                }
                emit("details", json.dumps(details))
            except json.JSONDecodeError:
                pass

        jobs[job_id]["status"] = "success"

    except Exception as e:
        emit("error", f"Unexpected error: {str(e)}")
        jobs[job_id]["status"] = "failed"

    q.put(None)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print(f"Starting Scratch Org UI on http://localhost:{port}")
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
