"""
Test script to verify the simplified {status, message} response format.
"""
import asyncio
import httpx
import json
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000"
CLASSIFY_ENDPOINT = f"{API_BASE_URL}/classify"

# Test cases for different classification types
TEST_CASES = [
    {
        "name": "Guidance Query (English)",
        "message": "How should I prepare for JEE Main?",
        "expected_classification": "guidance_based",
        "expected_status": "success"
    },
    {
        "name": "Guidance Query (Hinglish)",
        "message": "physics ki padhai kaise karu kuch samajh nahi aa raha",
        "expected_classification": "guidance_based",
        "expected_status": "success"
    },
    {
        "name": "App Related - Lectures",
        "message": "Show me physics lectures",
        "expected_classification": "app_related",
        "expected_status": "success"
    },
    {
        "name": "Exam Related - PYQ",
        "message": "Give me JEE Main previous year questions on Newton's laws",
        "expected_classification": "exam_related_info",
        "expected_status": "success"
    },
    {
        "name": "Subject Query",
        "message": "What is Newton's first law of motion?",
        "expected_classification": "subject_related",
        "expected_status": "success"
    },
    {
        "name": "Conversation (Hinglish)",
        "message": "hello mera naam ekta h",
        "expected_classification": "conversation_based",
        "expected_status": "success"
    },
    {
        "name": "Conversation (English)",
        "message": "Hi, how are you?",
        "expected_classification": "conversation_based",
        "expected_status": "success"
    },
    {
        "name": "Complaint",
        "message": "The app is not working properly",
        "expected_classification": "complaint",
        "expected_status": "success"
    }
]


def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_test_header(test_num: int, total: int, test_name: str):
    """Print test header."""
    print(f"\n\n{'='*80}")
    print(f"TEST {test_num}/{total}: {test_name}")
    print('='*80)


def validate_simple_format(response_data: dict, test_case: dict) -> tuple[bool, list]:
    """
    Validate that response matches simple format requirements.

    Returns:
        tuple: (is_valid, list of issues)
    """
    issues = []

    # Check required keys
    if 'status' not in response_data:
        issues.append("❌ Missing 'status' key")
    if 'message' not in response_data:
        issues.append("❌ Missing 'message' key")

    # Check for unexpected keys
    expected_keys = {'status', 'message'}
    actual_keys = set(response_data.keys())
    extra_keys = actual_keys - expected_keys
    if extra_keys:
        issues.append(f"❌ Unexpected keys found: {extra_keys}")

    # Validate status value
    if 'status' in response_data:
        status = response_data['status']
        if status not in ['success', 'error']:
            issues.append(f"❌ Invalid status value: '{status}' (expected 'success' or 'error')")
        elif status != test_case['expected_status']:
            issues.append(f"⚠️  Status '{status}' doesn't match expected '{test_case['expected_status']}'")

    # Validate message
    if 'message' in response_data:
        message = response_data['message']
        if not isinstance(message, str):
            issues.append(f"❌ Message is not a string: {type(message)}")
        elif not message.strip():
            issues.append("❌ Message is empty")

    return len(issues) == 0, issues


async def test_single_query(client: httpx.AsyncClient, test_case: dict, test_num: int, total: int):
    """Test a single query and validate the simplified response."""
    try:
        print_test_header(test_num, total, test_case['name'])
        print(f"Query: {test_case['message']}")
        print(f"Expected: {test_case['expected_classification']} | {test_case['expected_status']}")
        print()

        # Make API request
        response = await client.post(
            CLASSIFY_ENDPOINT,
            json={"message": test_case['message']},
            timeout=60.0
        )

        if response.status_code == 200:
            response_data = response.json()

            # Print response
            print("📥 RESPONSE:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            print()

            # Validate format
            is_valid, issues = validate_simple_format(response_data, test_case)

            if is_valid:
                print("✅ VALIDATION: PASSED")
                print(f"   ✓ Correct format: {{status, message}}")
                print(f"   ✓ Status: {response_data['status']}")
                print(f"   ✓ Message length: {len(response_data['message'])} chars")
                print(f"   ✓ Message preview: {response_data['message'][:150]}...")
                return True, None
            else:
                print("❌ VALIDATION: FAILED")
                for issue in issues:
                    print(f"   {issue}")
                return False, issues
        else:
            print(f"❌ HTTP ERROR: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return False, [f"HTTP {response.status_code}"]

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False, [str(e)]


async def run_all_tests():
    """Run all test cases."""
    print("\n" + "🧪" * 40)
    print("  SIMPLIFIED FORMAT VALIDATION TEST SUITE")
    print("🧪" * 40)
    print(f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API: {API_BASE_URL}")
    print(f"Tests: {len(TEST_CASES)}")

    # Check API health
    try:
        async with httpx.AsyncClient() as client:
            health_response = await client.get(f"{API_BASE_URL}/health", timeout=5.0)
            if health_response.status_code != 200:
                print(f"\n❌ API health check failed! Status: {health_response.status_code}")
                return
            print("\n✅ API is healthy")
    except Exception as e:
        print(f"\n❌ Cannot connect to API: {e}")
        print("Make sure the API is running: uvicorn app.main:app --reload")
        return

    # Run tests
    results = []
    async with httpx.AsyncClient() as client:
        for i, test_case in enumerate(TEST_CASES, 1):
            success, issues = await test_single_query(client, test_case, i, len(TEST_CASES))
            results.append({
                "name": test_case['name'],
                "success": success,
                "issues": issues
            })
            await asyncio.sleep(0.5)  # Small delay between tests

    # Print summary
    print("\n\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed

    print(f"\nTotal Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")

    print("\nDetailed Results:")
    for i, result in enumerate(results, 1):
        status_icon = "✅" if result['success'] else "❌"
        print(f"  {i}. {status_icon} {result['name']}")
        if not result['success'] and result['issues']:
            for issue in result['issues']:
                print(f"      {issue}")

    print("\n" + "="*80)

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Response format is correct.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the issues above.")

    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
