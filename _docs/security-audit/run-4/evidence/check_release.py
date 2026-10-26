"""Validate observed origin values and passively inspect HEAD responses with native TLS."""
import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse

base = Path(__file__).parent
snapshot = json.loads((base / "github-admin.json").read_text(encoding="utf-8"))
variables = {v["name"]: v.get("value") for v in snapshot["environment_variables"]["data"]}
configuration = []
for name in ("CLOUDFLARE_API_ORIGIN", "CLOUDFLARE_FRONTEND_ORIGIN"):
    parsed = urlparse(variables[name])
    configuration.append({"name": name, "value": variables[name], "workflow_accepts_origin": not (parsed.scheme != "https" or not parsed.netloc or parsed.path), "parsed_path": parsed.path})
responses = []
selected_headers = {"content-type", "cache-control", "strict-transport-security", "content-security-policy", "x-frame-options", "access-control-allow-origin", "access-control-allow-credentials", "server", "cf-cache-status"}
for name, paths in (("CLOUDFLARE_API_ORIGIN", ("/api/health/", "/api/reviews")), ("CLOUDFLARE_FRONTEND_ORIGIN", ("/",))):
    for path in paths:
        url = variables[name].rstrip("/") + path
        result = subprocess.run(["curl.exe", "--silent", "--show-error", "--head", "--dump-header", "-", "--output", "NUL", "--write-out", "\n%{http_code}", "--max-time", "15", url], capture_output=True, text=True)
        raw_headers, _, status = result.stdout.rstrip().rpartition("\n")
        blocks = [block for block in raw_headers.split("\n\n") if block.startswith("HTTP/")]
        final_headers = {}
        cookie_present = False
        for line in (blocks[-1].splitlines()[1:] if blocks else []):
            key, sep, value = line.partition(":")
            if sep and key.lower() in selected_headers:
                final_headers[key.lower()] = value.strip()
            cookie_present |= bool(sep and key.lower() == "set-cookie")
        responses.append({"url": url, "method": "HEAD", "exit": result.returncode, "status": status, "headers": final_headers, "set_cookie_present": cookie_present, "error": result.stderr.strip(), "tls_verification_disabled": False, "response_body_read": False})
report = {"origin_configuration": configuration, "native_head_responses": responses}
(base / "release-check.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
