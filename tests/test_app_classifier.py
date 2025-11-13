"""
Test script for app_related_classifier_main sub-classification routing
"""
import asyncio
import sys
sys.path.append('/home/ubuntu/apps/whatsapp-classifier')

from app.services.app_related_classifier import app_related_classifier_main


async def test_classification():
    """Test different query types"""

    # Test 1: Subscription related query
    print("\n" + "="*60)
    print("TEST 1: Subscription Related Query")
    print("="*60)
    json_data_subscription = {
        "userQuery": "What is the price of the Unnati batch?",
        "subject": "Physics",
        "language": "hindi",
        "requestType": "text"
    }

    try:
        result = await app_related_classifier_main(json_data_subscription, "test_user_123", "app_related")
        print(f"Classification: {result.get('classifiedAs')}")
        print(f"Response Type: {type(result.get('response'))}")
        if isinstance(result.get('response'), dict):
            print(f"Response Text (first 100 chars): {result['response'].get('text', '')[:100]}...")
        else:
            print(f"Response (first 100 chars): {str(result.get('response'))[:100]}...")
        print("✓ Subscription test passed")
    except Exception as e:
        print(f"✗ Subscription test failed: {e}")

    # Test 2: App data related query
    print("\n" + "="*60)
    print("TEST 2: App Data Related Query")
    print("="*60)
    json_data_app_data = {
        "userQuery": "I need physics chapter notes",
        "subject": "Physics",
        "language": "hindi",
        "requestType": "text"
    }

    try:
        result = await app_related_classifier_main(json_data_app_data, "test_user_123", "app_related")
        print(f"Classification: {result.get('classifiedAs')}")
        print(f"Response: {result.get('response')}")
        print("✓ App data test passed")
    except Exception as e:
        print(f"✗ App data test failed: {e}")

    # Test 3: Screen data related query
    print("\n" + "="*60)
    print("TEST 3: Screen Data Related Query")
    print("="*60)
    json_data_screen = {
        "userQuery": "How do I download lectures?",
        "subject": "Physics",
        "language": "english",
        "requestType": "text"
    }

    try:
        result = await app_related_classifier_main(json_data_screen, "test_user_123", "app_related")
        print(f"Classification: {result.get('classifiedAs')}")
        print(f"Response Type: {type(result.get('response'))}")
        if isinstance(result.get('response'), dict):
            print(f"Response Text (first 100 chars): {result['response'].get('text', '')[:100]}...")
        else:
            print(f"Response (first 100 chars): {str(result.get('response'))[:100]}...")
        print("✓ Screen data test passed")
    except Exception as e:
        print(f"✗ Screen data test failed: {e}")

    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_classification())
