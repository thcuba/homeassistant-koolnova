#!/usr/bin/env python3
"""
Script to test restart/reconnection endpoints without authentication.
"""

import subprocess
import json
import time
from typing import Dict, List

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
            "-m", "10",  # 10 second timeout
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
    elif code.startswith("ERROR"):
        return f"⚠️ ERROR: {code}"
    else:
        return f"🤔 OTHER: {code}"

def main():
    """Test all candidate restart/reconnection endpoints."""

    print("🔬 TEST OF RESTART/RECONNECTION ENDPOINTS")
    print("=" * 60)
    print("Established pattern:")
    print("  401 = ✅ Endpoint exists but requires authentication")
    print("  404 = ❌ Endpoint does not exist")
    print()

    # Candidate endpoints organized by category
    endpoints_by_category = {
        "🔄 HUB/CONTROLLER": [
            "hub/123/restart",
            "hub/123/reboot",
            "hub/123/reset",
            "hub/restart",
            "hub/reboot",
            "hub/reset",
        ],
        "📡 MODULES/DEVICES": [
            "modules/123/reboot",
            "modules/123/reset",
            "modules/123/restart",
            "devices/123/reboot",
            "devices/123/reset",
            "devices/123/restart",
            "devices/123/reconnect",
        ],
        "🏠 TOPICS/PROJECTS": [
            "topics/123/reconnect",
            "topics/123/reset",
            "topics/123/restart",
            "topics/reconnect",
            "projects/123/reconnect",
            "projects/123/reset",
            "projects/123/restart",
        ],
        "⚙️ SYSTEM": [
            "system/restart",
            "system/reset",
            "system/reboot",
            "system/reload",
            "system/network/reset",
            "system/mqtt/reconnect",
            "system/mqtt/reset",
        ],
        "🌐 CONNECTION/NETWORK": [
            "network/reset",
            "network/restart",
            "network/reconnect",
            "connection/reset",
            "connection/restart",
            "wifi/reset",
            "wifi/reconnect",
        ],
        "🔧 CONFIGURATION": [
            "config/reset",
            "config/restart",
            "config/reload",
            "settings/reset",
            "profile/reset",
        ],
        "📊 OTHER POSSIBLE": [
            "admin/restart",
            "control/restart",
            "server/restart",
            "api/restart",
            "service/restart",
        ]
    }

    base_url = "https://api.koolnova.com/"
    all_results = {}

    for category, endpoints in endpoints_by_category.items():
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

            # Small pause to avoid overloading
            time.sleep(0.5)

        all_results[category] = category_results

    # FINAL SUMMARY
    print("\n" + "="*60)
    print("📊 FINAL SUMMARY - ENDPOINTS THAT EXIST")
    print("="*60)

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
        print("2. Verify which HTTP methods they accept (GET, POST, PUT, PATCH)")
        print("3. Implement those that work in the integration")
        print("4. Document required parameters")

        # Save results in JSON
        with open('tests/restart_endpoints_results.json', 'w') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        print("\n📄 Results saved to: tests/restart_endpoints_results.json")
    else:
        print("\n❌ No candidate endpoints found")

if __name__ == "__main__":
    main()
