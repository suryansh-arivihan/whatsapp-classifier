"""
Test FAQ handler to verify it's working with exam_faq_query.py
"""
from app.services.exam_faq_query import exam_faq_query_main

TEST_QUERY = "phsyics me sabse jyada number ka kis chapter se aata h"

print("="*80)
print("FAQ HANDLER TEST")
print("="*80)
print(f"\nQuery: {TEST_QUERY}\n")

# Prepare payload
payload = {
    "userQuery": TEST_QUERY,
    "subject": "Physics",
    "language": "hinglish",
    "requestType": "text"
}

print("Payload:")
print("-"*80)
for key, value in payload.items():
    print(f"  {key}: {value}")
print()

# Call FAQ handler
print("Calling exam_faq_query_main...")
print("-"*80)
result = exam_faq_query_main(payload, "exam_related_info")
print()

print("Result:")
print("-"*80)
print(f"initialClassification: {result.get('initialClassification')}")
print(f"classifiedAs: {result.get('classifiedAs')}")
print(f"openWhatsapp: {result.get('openWhatsapp')}")
print(f"responseType: {result.get('responseType')}")
print()

response = result.get('response', '')
if isinstance(response, dict):
    print("Response (dict):")
    print(f"  - text: {response.get('text', 'N/A')[:300]}...")
    print(f"  - queryType: {response.get('queryType', 'N/A')}")
    print(f"  - request_type: {response.get('request_type', 'N/A')}")
else:
    print(f"Response (string): {str(response)[:300]}...")

print()
print("="*80)
print("ANALYSIS:")
print("="*80)

if result.get('openWhatsapp'):
    print("❌ FAQ handler couldn't find an answer")
    print("   Response will show app download message")
else:
    print("✅ FAQ handler found an answer!")
    print("   Response will show the actual answer")

print("="*80)
