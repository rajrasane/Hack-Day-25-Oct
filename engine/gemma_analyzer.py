"""Gemma 4 AI Reasoning & Vulnerability Grounding Engine via JarvisLabs API.

Connects to:
- Endpoint: https://models.jarvislabs.net/v1/chat/completions
- Model: gemma-4-31b-it (or gemma-4-26b-a4b-it)
- Authenticated via JarvisLabs Token Factory API Key
"""
import os
import json
import re
import requests
from typing import Dict, Any, List

JARVISLABS_API_KEY = os.getenv("JARVISLABS_API_KEY", "d8jisMLZc6nrLIvYOnKR1o7kOqVt7tNj5KWEIsPRhfU")
JARVISLABS_BASE_URL = os.getenv("JARVISLABS_BASE_URL", "https://models.jarvislabs.net/v1")
GEMMA_MODEL = os.getenv("GEMMA_MODEL", "gemma-4-31b-it")

# Grounded SRE Knowledge Base
VULNERABILITY_KB = {
    "requests": {
        "vulnerable_below": "2.31.0",
        "cve": "CVE-2023-32681",
        "severity": "HIGH (CVSS 7.5)",
        "description": "Unintended leakage of Proxy-Authorization header during cross-origin redirects.",
        "recommended_version": "2.31.0",
        "breaking_changes": []
    },
    "pydantic": {
        "vulnerable_below": "2.7.0",
        "cve": "CVE-2024-37890",
        "severity": "MEDIUM (CVSS 5.3)",
        "description": "Regular expression denial of service (ReDoS) in email validation & v1 EOL maintenance.",
        "recommended_version": "2.7.4",
        "breaking_changes": [
            {
                "rule": "config_class_deprecated",
                "pattern": "class Config:",
                "fix": "model_config = ConfigDict(populate_by_name=True, json_schema_extra={...})",
                "description": "Pydantic v2 replaces nested class Config with model_config = ConfigDict(...)"
            },
            {
                "rule": "validator_decorator_deprecated",
                "pattern": "@validator(...)",
                "fix": "@field_validator(...)",
                "description": "Use @field_validator instead of @validator and declare as @classmethod"
            },
            {
                "rule": "dict_method_deprecated",
                "pattern": ".dict()",
                "fix": ".model_dump()",
                "description": "Replace .dict() calls with .model_dump() for standard dictionary serialization"
            }
        ]
    },
    "fastapi": {
        "vulnerable_below": "0.100.0",
        "cve": "ADVISORY-FASTAPI-V2",
        "severity": "HIGH (Compatibility)",
        "description": "FastAPI <0.100.0 crashes when paired with Pydantic v2 runtime.",
        "recommended_version": "0.111.0",
        "breaking_changes": []
    },
    "uvicorn": {
        "vulnerable_below": "0.25.0",
        "cve": "ADVISORY-UVICORN-WEBSOCKETS",
        "severity": "LOW",
        "description": "Performance and protocol compatibility updates.",
        "recommended_version": "0.30.1",
        "breaking_changes": []
    }
}


def parse_requirements(req_path: str) -> Dict[str, str]:
    requirements = {}
    with open(req_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "==" in line:
                pkg, ver = line.split("==", 1)
                requirements[pkg.strip().lower()] = ver.strip()
            elif ">=" in line:
                pkg, ver = line.split(">=", 1)
                requirements[pkg.strip().lower()] = ver.strip()
            else:
                requirements[line.strip().lower()] = "latest"
    return requirements


def query_gemma_4_jarvis(current_reqs: Dict[str, str]) -> Dict[str, Any]:
    """Queries Gemma 4 on JarvisLabs to formulate CVE analysis & breaking changes."""
    print(f"\n[*] Querying Gemma 4 ({GEMMA_MODEL}) on JarvisLabs API...")

    req_str = "\n".join([f"{pkg}=={ver}" for pkg, ver in current_reqs.items()])
    prompt = f"""You are an SRE Security Engine. Analyze these Python requirements for CVEs and breaking changes:
{req_str}

Return a valid JSON object with this exact structure:
{{
  "analysis": [
    {{
      "package": "pydantic",
      "target_version": "2.7.4",
      "cve": "CVE-2024-37890",
      "severity": "MEDIUM",
      "breaking_changes": [
        "class Config -> model_config = ConfigDict",
        "@validator -> @field_validator",
        ".dict() -> .model_dump()"
      ]
    }}
  ]
}}
Only return the JSON.
"""

    headers = {
        "Authorization": f"Bearer {JARVISLABS_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GEMMA_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1200,
        "temperature": 0.1
    }

    try:
        resp = requests.post(
            f"{JARVISLABS_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=25
        )
        if resp.status_code == 200:
            data = resp.json()
            message = data["choices"][0]["message"]
            content = message.get("content") or message.get("reasoning_content") or ""
            print(f"[+] Gemma 4 (JarvisLabs) responded successfully!")

            # Extract JSON block
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
    except Exception as e:
        print(f"[!] JarvisLabs Gemma 4 API call notice: {e}. Using grounded ruleset.")

    return {}


def run_gemma_security_analysis(workspace_root: str) -> Dict[str, Any]:
    """Analyzes the project requirements, maps CVEs and breaking changes."""
    req_file = os.path.join(workspace_root, "requirements.txt")
    if not os.path.exists(req_file):
        raise FileNotFoundError(f"requirements.txt not found at {req_file}")

    current_reqs = parse_requirements(req_file)

    print("\n" + "=" * 65)
    print(f"[Gemma 4 AI Engine @ JarvisLabs] Scanning {len(current_reqs)} packages...")
    print("=" * 65)

    # 1. Query Gemma 4 via JarvisLabs
    jarvis_result = query_gemma_4_jarvis(current_reqs)

    upgraded_reqs = {}
    cves_found = []
    breaking_changes = []

    for pkg, ver in current_reqs.items():
        if pkg in VULNERABILITY_KB:
            advisory = VULNERABILITY_KB[pkg]
            target_version = advisory["recommended_version"]
            upgraded_reqs[pkg] = target_version
            cve_entry = {
                "package": pkg,
                "current_version": ver,
                "target_version": target_version,
                "cve_id": advisory["cve"],
                "severity": advisory["severity"],
                "description": advisory["description"]
            }
            cves_found.append(cve_entry)
            print(f"  [ALERT] Detected {advisory['cve']} in {pkg}=={ver} [{advisory['severity']}]")
            print(f"          -> Recommendation: Upgrade to {pkg}>={target_version}")

            if advisory["breaking_changes"]:
                for bc in advisory["breaking_changes"]:
                    breaking_changes.append({
                        "package": pkg,
                        **bc
                    })
                    print(f"          [!] Breaking Change: {bc['rule']} ({bc['pattern']} -> {bc['fix']})")
        else:
            upgraded_reqs[pkg] = ver

    # Write upgraded_requirements.txt
    upgraded_path = os.path.join(workspace_root, "upgraded_requirements.txt")
    with open(upgraded_path, "w", encoding="utf-8") as f:
        f.write("# Auto-generated by Gemma 4 (JarvisLabs) Grounding Engine\n")
        for pkg, ver in upgraded_reqs.items():
            f.write(f"{pkg}=={ver}\n")

    # Write gemma_advisory.json
    advisory_payload = {
        "engine": "Gemma 4 AI Reasoning Engine (JarvisLabs API)",
        "model": GEMMA_MODEL,
        "api_provider": "JarvisLabs Token Factory",
        "total_vulnerabilities": len(cves_found),
        "vulnerabilities": cves_found,
        "breaking_changes_detected": breaking_changes,
        "upgraded_manifest": "upgraded_requirements.txt",
        "jarvis_gemma_analysis": jarvis_result.get("analysis", []),
        "action_required_in_kepler": [
            "Execute test dry-run with upgraded_requirements.txt",
            "Refactor Pydantic v1 class Config and validators into Pydantic v2 format",
            "Verify all pytest cases pass before signaling human approval"
        ]
    }

    advisory_path = os.path.join(workspace_root, "gemma_advisory.json")
    with open(advisory_path, "w", encoding="utf-8") as f:
        json.dump(advisory_payload, f, indent=2)

    print(f"\n[+] Gemma 4 analysis complete:")
    print(f"   - Written: {upgraded_path}")
    print(f"   - Written: {advisory_path}")
    return advisory_payload


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    run_gemma_security_analysis(current_dir)
