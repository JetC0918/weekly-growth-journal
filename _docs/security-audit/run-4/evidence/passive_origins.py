"""Read status and selected response headers only; no credentials or response bodies."""
import json
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


snapshot = json.loads(Path(__file__).with_name("github-admin.json").read_text(encoding="utf-8"))
variables = {v["name"]: v.get("value") for v in snapshot["environment_variables"]["data"]}
opener = urllib.request.build_opener(NoRedirect)
results = []
for key, paths in (("CLOUDFLARE_API_ORIGIN", ("/api/health/", "/api/reviews")), ("CLOUDFLARE_FRONTEND_ORIGIN", ("/",))):
    origin = variables[key].rstrip("/")
    for path in paths:
        url = origin + path
        request = urllib.request.Request(url, headers={"User-Agent": "Predeployment-read-only-audit/4"})
        result = {"url": url, "method": "GET", "credentials": False, "body_read": False}
        try:
            try:
                response = opener.open(request, timeout=15)
            except urllib.error.HTTPError as exc:
                response = exc
            with response:
                result["status"] = response.code
                result["headers"] = {k.lower(): v for k, v in response.headers.items() if k.lower() in {"content-type", "cache-control", "strict-transport-security", "x-frame-options", "content-security-policy", "access-control-allow-origin", "access-control-allow-credentials"}}
                result["set_cookie_present"] = bool(response.headers.get("Set-Cookie"))
                if response.headers.get("Location"):
                    target = urlsplit(response.headers["Location"])
                    result["location_without_query"] = urlunsplit((target.scheme, target.netloc, target.path, "", ""))
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
        results.append(result)
Path(__file__).with_name("passive-origins.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
print(json.dumps(results, indent=2))
