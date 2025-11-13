"""
Test for specific query: "physics me important questions chahiye h"
This should return the important_questions template message.
"""
import asyncio
import httpx
import json

API_BASE_URL = "http://localhost:8000"
CLASSIFY_ENDPOINT = f"{API_BASE_URL}/classify"

QUERY = "physics me important questions chahiye h"

EXPECTED_MESSAGE_START = """📚 *Important Questions chahiye?*

*Arivihan par sirf questions nahi milte…*
✨ Har question ka *DETAILED EXPLANATION* milta h!

🎯 *Kya special h*:"""


async def test_important_questions():
    """Test the important questions query."""
    print("="*80)
    print("TESTING: Important Questions Query")
    print("="*80)
    print(f"\nQuery: {QUERY}")
    print(f"API: {CLASSIFY_ENDPOINT}\n")

    try:
        async with httpx.AsyncClient() as client:
            # Make request
            print("📤 Sending request...")
            response = await client.post(
                CLASSIFY_ENDPOINT,
                json={"message": QUERY},
                timeout=60.0
            )

            print(f"📥 Response status: {response.status_code}\n")

            if response.status_code == 200:
                response_data = response.json()

                print("="*80)
                print("FULL RESPONSE:")
                print("="*80)
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
                print()

                # Check format
                print("="*80)
                print("VALIDATION:")
                print("="*80)

                if 'status' in response_data and 'message' in response_data:
                    print("✅ Response has correct format: {status, message}")
                else:
                    print("❌ Response format is incorrect")
                    return

                status = response_data['status']
                message = response_data['message']

                print(f"\nStatus: {status}")
                print(f"Message length: {len(message)} chars")
                print(f"\nMessage content:")
                print("-"*80)
                print(message)
                print("-"*80)

                # Check if message contains expected content
                print("\n" + "="*80)
                print("CONTENT VERIFICATION:")
                print("="*80)

                checks = [
                    ("Contains '📚 *Important Questions chahiye?*'", "📚 *Important Questions chahiye?*" in message),
                    ("Contains 'Arivihan par sirf questions nahi milte'", "Arivihan par sirf questions nahi milte" in message),
                    ("Contains 'DETAILED EXPLANATION'", "DETAILED EXPLANATION" in message),
                    ("Contains '🎯 *Kya special h*:'", "🎯 *Kya special h*:" in message),
                    ("Contains explanation points", "✅" in message),
                ]

                all_passed = True
                for check_name, check_result in checks:
                    icon = "✅" if check_result else "❌"
                    print(f"{icon} {check_name}")
                    if not check_result:
                        all_passed = False

                print("\n" + "="*80)
                if all_passed:
                    print("🎉 TEST PASSED! Message contains all expected content.")
                else:
                    print("⚠️  TEST FAILED! Some expected content is missing.")
                print("="*80)

            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(response.text)

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_important_questions())
