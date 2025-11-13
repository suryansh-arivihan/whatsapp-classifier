"""
Test script to observe API responses for different classification types.
This script will help identify the exact response structure before simplification.
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
        "name": "Guidance Query",
        "message": "How should I prepare for JEE Main?",
        "expected_classification": "guidance_based"
    },
    {
        "name": "App Related Query",
        "message": "Show me physics lectures",
        "expected_classification": "app_related"
    },
    {
        "name": "Exam Related - PYQ",
        "message": "Give me JEE Main previous year questions on Newton's laws",
        "expected_classification": "exam_related_info"
    },
    {
        "name": "Subject Query",
        "message": "What is Newton's first law of motion?",
        "expected_classification": "subject_related"
    },
    {
        "name": "Conversation Query",
        "message": "Hi, how are you?",
        "expected_classification": "conversation_based"
    },
    {
        "name": "Complaint Query",
        "message": "The app is not working properly",
        "expected_classification": "complaint"
    }
]


def print_separator(title=""):
    """Print a formatted separator."""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)


def print_response_analysis(response_data: dict, test_name: str):
    """Analyze and print the response structure."""
    print_separator(f"RESPONSE ANALYSIS: {test_name}")

    print("\n1. TOP-LEVEL KEYS:")
    print(f"   Keys: {list(response_data.keys())}")

    print("\n2. CLASSIFICATION INFO:")
    print(f"   Classification: {response_data.get('classification')}")
    print(f"   Sub-classification: {response_data.get('sub_classification')}")
    print(f"   Subject: {response_data.get('subject')}")
    print(f"   Language: {response_data.get('language')}")

    print("\n3. RESPONSE_DATA STRUCTURE:")
    response_data_content = response_data.get('response_data')
    if response_data_content:
        print(f"   Keys: {list(response_data_content.keys())}")
        print(f"   Status: {response_data_content.get('status')}")
        print(f"   Message: {response_data_content.get('message')}")

        print("\n4. RESPONSE_DATA -> DATA STRUCTURE:")
        data_content = response_data_content.get('data')
        if data_content:
            if isinstance(data_content, dict):
                print(f"   Data is a dict with keys: {list(data_content.keys())}")
                print(f"   Data preview: {json.dumps(data_content, indent=2)[:300]}...")
            else:
                print(f"   Data type: {type(data_content)}")
                print(f"   Data content: {str(data_content)[:200]}...")
        else:
            print("   No data found")

        print("\n5. METADATA:")
        metadata = response_data_content.get('metadata')
        if metadata:
            print(f"   Metadata: {json.dumps(metadata, indent=2)}")
    else:
        print("   No response_data found!")

    print("\n6. WHAT USER SHOULD SEE (PROPOSED):")
    if response_data_content:
        proposed_status = response_data_content.get('status')
        # Try to extract the actual message for the user
        data_content = response_data_content.get('data')
        if isinstance(data_content, dict):
            # Check for common message fields
            proposed_message = (
                data_content.get('text') or
                data_content.get('message') or
                data_content.get('response') or
                str(data_content)
            )
        else:
            proposed_message = str(data_content)

        print(f"   Status: {proposed_status}")
        print(f"   Message preview: {str(proposed_message)[:200]}...")

    print("\n" + "=" * 80)


async def test_single_query(client: httpx.AsyncClient, test_case: dict):
    """Test a single query and analyze the response."""
    try:
        print_separator(f"TESTING: {test_case['name']}")
        print(f"Message: {test_case['message']}")
        print(f"Expected Classification: {test_case['expected_classification']}")

        # Make API request
        response = await client.post(
            CLASSIFY_ENDPOINT,
            json={"message": test_case['message']},
            timeout=30.0
        )

        if response.status_code == 200:
            response_data = response.json()
            print_response_analysis(response_data, test_case['name'])
            return True
        else:
            print(f"\n❌ ERROR: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all test cases."""
    print("\n" + "🔬" * 40)
    print("  WHATSAPP CLASSIFIER - RESPONSE OBSERVATION TESTING")
    print("🔬" * 40)
    print(f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Total test cases: {len(TEST_CASES)}")

    # Check if API is running
    try:
        async with httpx.AsyncClient() as client:
            health_response = await client.get(f"{API_BASE_URL}/health", timeout=5.0)
            if health_response.status_code != 200:
                print(f"\n❌ API health check failed! Status: {health_response.status_code}")
                print("Make sure the API is running: uvicorn app.main:app --reload")
                return
            print("\n✅ API is healthy and ready")
    except Exception as e:
        print(f"\n❌ Cannot connect to API: {e}")
        print("Make sure the API is running: uvicorn app.main:app --reload")
        return

    # Run test cases
    results = []
    async with httpx.AsyncClient() as client:
        for i, test_case in enumerate(TEST_CASES, 1):
            print(f"\n\n{'='*80}")
            print(f"TEST {i}/{len(TEST_CASES)}")
            success = await test_single_query(client, test_case)
            results.append({
                "name": test_case['name'],
                "success": success
            })

            # Small delay between tests
            await asyncio.sleep(1)

    # Print summary
    print_separator("TEST SUMMARY")
    successful = sum(1 for r in results if r['success'])
    print(f"\nTotal Tests: {len(results)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {len(results) - successful}")

    print("\nDetailed Results:")
    for i, result in enumerate(results, 1):
        status = "✅" if result['success'] else "❌"
        print(f"  {i}. {status} {result['name']}")

    print("\n" + "=" * 80)
    print("\n📝 CHECK THE API LOGS to see detailed pipeline logging!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
