"""Read-only GitHub configuration snapshot; never request secret values."""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = "repos/JetC0918/weekly-growth-journal"


def read(path, select=lambda value: value):
    result = subprocess.run(["gh", "api", f"{ROOT}/{path}".rstrip("/")], capture_output=True, text=True)
    if result.returncode:
        return {"ok": False, "error": result.stderr.strip()}
    value = json.loads(result.stdout) if result.stdout.strip() else None
    return {"ok": True, "data": select(value)}


def variables(value):
    visible = {"CLOUDFLARE_DEPLOY_ENABLED", "CLOUDFLARE_API_ORIGIN", "CLOUDFLARE_FRONTEND_ORIGIN"}
    return [{"name": item["name"], **({"value": item["value"]} if item["name"] in visible else {})} for item in value["variables"]]


snapshot = {
    "captured_at": datetime.now(timezone.utc).isoformat(),
    "repository": read("", lambda r: {k: r.get(k) for k in ("full_name", "private", "default_branch", "pushed_at", "security_and_analysis")}),
    "environment": read("environments/cloudflare-production", lambda e: {k: e.get(k) for k in ("name", "protection_rules", "deployment_branch_policy")}),
    "deployment_branch_policies": read("environments/cloudflare-production/deployment-branch-policies"),
    "repository_variables": read("actions/variables?per_page=100", variables),
    "environment_variables": read("environments/cloudflare-production/variables?per_page=100", variables),
    "environment_secret_names": read("environments/cloudflare-production/secrets?per_page=100", lambda s: [item["name"] for item in s["secrets"]]),
    "dependabot_enabled": read("vulnerability-alerts"),
    "dependabot_open_alert_summary": read("dependabot/alerts?state=open&per_page=100", lambda alerts: [{"number": a["number"], "package": a["dependency"]["package"]["name"], "severity": a["security_advisory"]["severity"], "ghsa_id": a["security_advisory"]["ghsa_id"]} for a in alerts]),
    "code_scanning_open_alert_summary": read("code-scanning/alerts?state=open&per_page=100", lambda alerts: [{"number": a["number"], "state": a["state"], "tool": a["tool"]["name"], "rule": a["rule"]["id"]} for a in alerts]),
}
destination = Path(__file__).with_name("github-admin.json")
destination.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
print(json.dumps(snapshot, indent=2))
