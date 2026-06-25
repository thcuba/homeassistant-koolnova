#!/usr/bin/env python3
"""
Script to test specific restart endpoints and explore redirects.
"""

import subprocess
import json
import time

def test_endpoint_full(url: str, method: str = "GET") -> dict:
    """Test an endpoint and return full information including redirect headers."""
    try:
        cmd = [
            "curl", "-s", "-I", "-X", method,  # -I for headers, -X for method
            "-H", "User-Agent: Mozilla/5.0",
            "-H", "accept: application/json, text/plain, */*",
            "-H", "accept-language: fr",
            "-H", "origin: https://app.koolnova.com",
            "-H", "referer: https://app.koolnova.com/",
            "-L",  # Follow redirects
            "-m", "10",
            url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

        # Parse response
        response_lines = result.stdout.strip().split('\n')
        status_line = response_lines[0] if response_lines else ""
        headers = {}

        for line in response_lines[1:]:
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key.lower()] = value

        return {
            "url": url,
            "method": method,
            "status_line": status_line,
            "status_code": status_line.split(' ')[1] if len(status_line.split(' ')) > 1 else "UNKNOWN",
            "headers": headers,
            "location": headers.get("location"),
            "final_url": headers.get("location") or url
        }

    except Exception as e:
        return {
            "url": url,
            "method": method,
            "error": str(e)
        }

def main():
    """Test specific endpoints and explore redirects."""

    print("🔬 TEST OF SPECIFIC ENDPOINTS AND REDIRECTS")
    print("=" * 70)

    # Specific endpoints to test
    specific_endpoints = [
        # Specific topics (since we know /topics/ exists)
        ("topics/reboot", "GET"),
        ("topics/reboot", "POST"),
        ("topics/restart", "GET"),
        ("topics/restart", "POST"),
        ("topics/reset", "GET"),
        ("topics/reset", "POST"),
        ("topics/reload", "GET"),
        ("topics/reload", "POST"),

        # More variations
        ("topics/control", "GET"),
        ("topics/power", "GET"),
        ("topics/manage", "GET"),
        ("topics/admin", "GET"),

        # Projects
        ("projects/restart", "GET"),
        ("projects/reset", "GET"),
        ("projects/reconnect", "GET"),

        # Admin with different methods
        ("admin/", "GET"),
        ("admin/", "POST"),
        ("admin/restart", "GET"),
        ("admin/restart", "POST"),
        ("admin/login/", "GET"),
        ("admin/login/", "POST"),

        # More admin
        ("admin/auth/", "GET"),
        ("admin/logout/", "GET"),
        ("admin/password_change/", "GET"),

        # API admin
        ("api/admin/", "GET"),
        ("api/admin/restart", "POST"),

        # Django admin patterns
        ("admin/koolnova/", "GET"),
        ("admin/koolnova/topic/", "GET"),
        ("admin/koolnova/project/", "GET"),

        # System
        ("system/admin", "GET"),
        ("system/control", "GET"),
        ("system/manage", "GET"),

        # Direct control
        ("control/", "GET"),
        ("control/system", "GET"),
        ("control/restart", "POST"),
        ("control/reset", "POST"),

        # Management
        ("manage/", "GET"),
        ("manage/system", "GET"),
        ("manage/control", "GET"),
        ("manage/restart", "POST"),

        # Power
        ("power/", "GET"),
        ("power/control", "GET"),
        ("power/restart", "POST"),
        ("power/reset", "POST"),
    ]

    base_url = "https://api.koolnova.com/"
    all_results = []

    print(f"Testing {len(specific_endpoints)} specific endpoints...")
    print()

    for i, (endpoint, method) in enumerate(specific_endpoints, 1):
        full_url = base_url + endpoint
        print(".", end="", flush=True)

        result = test_endpoint_full(full_url, method)
        result["endpoint"] = endpoint

        all_results.append(result)

        # Small pause
        time.sleep(0.2)

    print("\n" + "="*70)
    print("📊 RESULTS ANALYSIS")
    print("="*70)

    # Classify results
    redirects_302 = []
    not_found_404 = []
    unauthorized_401 = []
    other_responses = []

    for result in all_results:
        code = result.get("status_code", "ERROR")
        endpoint = result["endpoint"]
        method = result["method"]

        if code == "302":
            redirects_302.append((endpoint, method, result.get("location", "UNKNOWN")))
        elif code == "404":
            not_found_404.append((endpoint, method))
        elif code == "401":
            unauthorized_401.append((endpoint, method))
        else:
            other_responses.append((endpoint, method, code))

    # Show results
    print(f"🔄 302 REDIRECTS (possibly admin): {len(redirects_302)}")
    for endpoint, method, location in redirects_302:
        print(f"   {method} {endpoint} → {location}")

    print(f"\n✅ 401 AUTHORIZATION REQUIRED: {len(unauthorized_401)}")
    for endpoint, method in unauthorized_401:
        print(f"   {method} {endpoint}")

    print(f"\n❌ 404 NOT FOUND: {len(not_found_404)}")
    for endpoint, method in not_found_404:
        print(f"   {method} {endpoint}")

    if other_responses:
        print(f"\n🤔 OTHER RESPONSES: {len(other_responses)}")
        for endpoint, method, code in other_responses:
            print(f"   {method} {endpoint} → {code}")

    # Special analysis of admin redirects
    print("\n🎯 ADMIN REDIRECTS ANALYSIS")
    print("-" * 40)

    admin_redirects = [r for r in redirects_302 if "admin" in r[0]]
    if admin_redirects:
        print("Admin redirects found:")
        for endpoint, method, location in admin_redirects:
            print(f"   {method} {endpoint}")
            print(f"   → Redirects to: {location}")

            # Check if it's Django admin login
            if "login" in location or "admin" in location:
                print("   💡 Possibly Django administration login")
            print()
    else:
        print("No specific admin redirects found")

    # Save detailed results
    with open('tests/specific_endpoints_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Detailed results saved to: tests/specific_endpoints_results.json")

    # Conclusions
    print("\n🎯 CONCLUSIONS:")
    print("-" * 40)

    if unauthorized_401:
        print(f"✅ {len(unauthorized_401)} endpoints require authentication (possibly exist)")

    if redirects_302:
        print(f"🔄 {len(redirects_302)} endpoints redirect (possibly to admin login)")

    if not_found_404:
        print(f"❌ {len(not_found_404)} endpoints do not exist")

    print("\n💡 Endpoints that require authentication could exist")
    print("   and function with valid administrator credentials.")

if __name__ == "__main__":
    main()
