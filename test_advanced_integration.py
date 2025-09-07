#!/usr/bin/env python3
"""
Quick test to verify advanced endpoints integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    try:
        from api_server import app
        print("✅ api_server imported successfully")

        from src.api.advanced_endpoints import advanced_router
        print("✅ advanced_endpoints imported successfully")

        # Check if router is properly configured
        routes = [str(route) for route in advanced_router.routes]
        print(f"✅ Advanced router has {len(routes)} routes")

        # Check if advanced router is included in main app
        app_routes = [str(route) for route in app.routes]
        advanced_routes = [r for r in app_routes if '/api/v2' in r]
        print(f"✅ Main app has {len(advanced_routes)} advanced routes")

        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_service_imports():
    """Test that service modules can be imported"""
    try:
        from src.services.analytics_service import get_analytics_service
        from src.services.user_management_service import get_user_management_service
        from src.services.gallery_service import get_gallery_service
        from src.services.notification_service import get_notification_service
        from src.services.batch_service import get_batch_service

        print("✅ All service modules imported successfully")

        # Test service instantiation
        analytics = get_analytics_service()
        user_svc = get_user_management_service()
        gallery = get_gallery_service()
        notifications = get_notification_service()
        batch_svc = get_batch_service()

        print("✅ All services instantiated successfully")
        return True
    except Exception as e:
        print(f"❌ Service import error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing advanced endpoints integration...")
    print()

    success = True
    success &= test_imports()
    success &= test_service_imports()

    print()
    if success:
        print("🎉 All tests passed! Advanced endpoints are properly integrated.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
