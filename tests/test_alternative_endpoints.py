#!/usr/bin/env python3
"""
Script to test alternative restart/reconnection endpoints.
"""

import subprocess
import json
import time

def test_endpoint(url: str) -> str:
    """Test an endpoint and return the HTTP code."""
    try:
        cmd = [
            "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
            "-H", "User-Agent: Mozilla/5.0",
            "-H", "accept: application/json, text/plain, */*",
            "-H", "accept-language: fr",
            "-H", "origin: https://app.koolnova.com",
            "-H", "referer: https://app.koolnova.com/",
            "-m", "10",
            url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

def classify_response(code: str) -> str:
    """Classify the HTTP response."""
    if code == "401":
        return "✅ EXISTS (requires auth)"
    elif code == "403":
        return "✅ EXISTS (forbidden)"
    elif code == "404":
        return "❌ DOES NOT EXIST"
    elif code == "405":
        return "✅ EXISTS (method not allowed)"
    elif code == "200":
        return "✅ EXISTS (public access)"
    elif code.startswith("ERROR"):
        return f"⚠️ ERROR: {code}"
    else:
        return f"🤔 OTHER: {code}"

def main():
    """Test alternative restart/reconnection endpoints."""

    print("🔬 TEST OF ALTERNATIVE RESTART/RECONNECTION ENDPOINTS")
    print("=" * 70)

    # Alternative endpoints based on common patterns
    alternative_endpoints = {
        "🔄 CONTROL/POWER": [
            "control/restart", "control/reset", "control/reboot",
            "power/restart", "power/reset", "power/reboot",
            "manage/restart", "manage/reset", "manage/reboot",
        ],
        "🌐 NETWORKING": [
            "network/restart", "network/reset", "network/reload",
            "connection/restart", "connection/reset", "connection/reload",
            "connectivity/reset", "connectivity/restart",
            "interface/reset", "interface/restart",
        ],
        "📡 MQTT/COMMS": [
            "mqtt/restart", "mqtt/reset", "mqtt/reconnect", "mqtt/reload",
            "communication/reset", "communication/restart",
            "link/reset", "link/restart", "link/reconnect",
        ],
        "⚙️ MAINTENANCE": [
            "maintenance/restart", "maintenance/reset",
            "service/restart", "service/reset", "service/reload",
            "daemon/restart", "daemon/reset",
        ],
        "🔧 ADMIN": [
            "admin/restart", "admin/reset", "admin/reload",
            "superuser/restart", "superuser/reset",
            "root/restart", "root/reset",
        ],
        "📊 SYSTEM": [
            "system/control", "system/power", "system/manage",
            "platform/restart", "platform/reset",
            "core/restart", "core/reset", "core/reload",
        ],
        "🏠 HOME AUTOMATION": [
            "home/restart", "home/reset", "home/reload",
            "automation/restart", "automation/reset",
            "smart/restart", "smart/reset",
        ],
        "🔗 INTEGRATION": [
            "integration/restart", "integration/reset", "integration/reload",
            "api/restart", "api/reset", "api/reload",
            "endpoint/restart", "endpoint/reset",
        ]
    }

    base_url = "https://api.koolnova.com/"
    all_results = {}

    for category, endpoints in alternative_endpoints.items():
        print(f"\n{category}")
        print("-" * 50)

        category_results = {}
        for endpoint in endpoints:
            full_url = base_url + endpoint
            print(f"🔍 Testing: {endpoint}", end=" ... ")

            code = test_endpoint(full_url)
            classification = classify_response(code)
            print(f"{code} → {classification}")

            category_results[endpoint] = {
                "code": code,
                "classification": classification
            }

            time.sleep(0.3)  # Short pause

        all_results[category] = category_results

    # FINAL SUMMARY
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY - ALTERNATIVE ENDPOINTS")
    print("="*70)

    existing_endpoints = []
    for category, results in all_results.items():
        category_existing = []
        for endpoint, data in results.items():
            if "EXISTS" in data["classification"]:
                category_existing.append(endpoint)

        if category_existing:
            print(f"\n{category}:")
            for endpoint in category_existing:
                print(f"  ✅ {endpoint}")

            existing_endpoints.extend(category_existing)

    print(f"\n🎯 TOTAL CANDIDATE ENDPOINTS FOUND: {len(existing_endpoints)}")

    if existing_endpoints:
        print("\n💡 NEXT STEPS:")
        print("1. Test these endpoints with valid credentials")
        print("2. Verify HTTP methods (GET, POST, PUT, PATCH)")
        print("3. Verify if additional parameters are required")
        print("4. Implement the ones that work")

        # Save results
        with open('tests/alternative_endpoints_results.json', 'w') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        print("\n📄 Results saved to: tests/alternative_endpoints_results.json")
    else:
        print("\n❌ No candidate endpoints found")
        print("💡 Koolnova API seems to be more basic than expected")

if __name__ == "__main__":
    main()
