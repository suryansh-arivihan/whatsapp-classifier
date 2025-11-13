"""
Diagnostic test to trace the full classification flow.
"""
import asyncio
import httpx
import json

API_BASE_URL = "http://localhost:8000"
TEST_QUERY = "physics me important questions chahiye h"


async def test_with_full_response():
    """Test and show the classification details."""
    print("="*80)
    print("DIAGNOSTIC TEST: Important Questions Query")
    print("="*80)
    print(f"\nQuery: {TEST_QUERY}\n")

    # First, let's see what classification type it gets
    print("🔍 This query should be classified as...")
    print("   Expected: exam_related_info (asking_important_question)")
    print("   Or maybe: app_related")
    print()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/classify",
                json={"message": TEST_QUERY},
                timeout=60.0
            )

            if response.status_code == 200:
                data = response.json()

                print("📥 SIMPLIFIED RESPONSE:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                print()

                print("="*80)
                print("ANALYSIS:")
                print("="*80)
                print(f"✓ Format: {'status' in data and 'message' in data}")
                print(f"✓ Status: {data.get('status')}")
                print(f"✓ Message preview: {data.get('message', '')[:100]}...")
                print()

                # Now let's understand what happened
                print("="*80)
                print("ISSUE DIAGNOSIS:")
                print("="*80)
                print()
                print("The query 'physics me important questions chahiye h' is likely:")
                print("  1. Being classified as 'exam_related_info' with sub-classification 'asking_important_question'")
                print("  2. Going to exam_handler instead of app_handler")
                print("  3. exam_handler is calling external API which returns a generic response")
                print()
                print("The 'important_questions' template exists in CONTENT_RESPONSES but:")
                print("  - It's only used by app_handler (app_related classification)")
                print("  - This query is being classified as exam_related, not app_related")
                print()
                print("SOLUTION OPTIONS:")
                print("  A. Change main_classifier to classify this as 'app_related'")
                print("  B. Modify exam_handler to use CONTENT_RESPONSES for 'asking_important_question'")
                print("  C. Add logic to detect 'important questions' queries and route to app_handler")
                print()

            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_with_full_response())
