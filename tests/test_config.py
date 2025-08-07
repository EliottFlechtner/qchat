#!/usr/bin/env python3
"""
Configuration test script for QChat.

This script tests that the configuration system is working correctly
by loading and validating both server and client settings.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_server_config():
    """Test server configuration loading."""
    print("🔧 Testing server configuration...")

    try:
        from server.config.settings import settings

        print(f"✅ Database URL: {settings.database_url}")
        print(f"✅ KEM Algorithm: {settings.kem_algorithm}")
        print(f"✅ Signature Algorithm: {settings.sig_algorithm}")
        print(f"✅ Debug Mode: {settings.debug}")
        print(f"✅ Log Level: {settings.log_level}")
        print(f"✅ Max Message Size: {settings.max_message_size}")

        return True
    except Exception as e:
        print(f"❌ Server configuration failed: {e}")
        return False


def test_client_config():
    """Test client configuration loading."""
    print("\n🔧 Testing client configuration...")

    try:
        from client.config.settings import client_settings

        print(f"✅ Server URL: {client_settings.server_url}")
        print(f"✅ WebSocket URL: {client_settings.ws_url}")
        print(f"✅ KEM Algorithm: {client_settings.kem_algorithm}")
        print(f"✅ Signature Algorithm: {client_settings.sig_algorithm}")
        print(f"✅ Log Level: {client_settings.log_level}")

        return True
    except Exception as e:
        print(f"❌ Client configuration failed: {e}")
        return False


def test_helper_functions():
    """Test helper functions."""
    print("\n🔧 Testing helper functions...")

    try:
        from client.utils.helpers import get_api_url, get_ws_url

        api_url = get_api_url()
        ws_url = get_ws_url()

        print(f"✅ API URL from helper: {api_url}")
        print(f"✅ WebSocket URL from helper: {ws_url}")

        return True
    except Exception as e:
        print(f"❌ Helper functions failed: {e}")
        return False


def main():
    """Run all configuration tests."""
    print("🚀 QChat Configuration Test")
    print("=" * 40)

    tests = [test_server_config, test_client_config, test_helper_functions]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All configuration tests passed!")
        return 0
    else:
        print("💥 Some configuration tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
