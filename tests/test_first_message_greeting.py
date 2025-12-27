"""
Test to verify that greetings are skipped when first_message is True
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.conversation_processor import conversation_main

print("="*80)
print("FIRST MESSAGE GREETING TEST")
print("="*80)

# Test 1: First message (should NOT send greeting)
print("\nTest 1: First Message (should NOT send greeting)")
print("-"*80)

payload_first = {
    "message": "hi",
    "userQuery": "hi",
    "requestType": "text",
    "subject": None,
    "language": "english"
}

print(f"Query: {payload_first['message']}")
print(f"first_message flag: True")
print("\nCalling conversation_main with first_message=True...")

result_first = conversation_main(payload_first, "conversation_based", first_message=True)

print("\nResult:")
print(f"  Response: {result_first.get('response', '')[:500]}")
print(f"  openWhatsapp: {result_first.get('openWhatsapp')}")
print()

# Test 2: Returning user (should send greeting)
print("\nTest 2: Returning User (should send greeting)")
print("-"*80)

payload_returning = {
    "message": "hello",
    "userQuery": "hello",
    "requestType": "text",
    "subject": None,
    "language": "english"
}

print(f"Query: {payload_returning['message']}")
print(f"first_message flag: False")
print("\nCalling conversation_main with first_message=False...")

result_returning = conversation_main(payload_returning, "conversation_based", first_message=False)

print("\nResult:")
print(f"  Response: {result_returning.get('response', '')[:500]}")
print(f"  openWhatsapp: {result_returning.get('openWhatsapp')}")
print()

print("="*80)
print("ANALYSIS:")
print("="*80)

# Analyze first message response
print("\n1. First Message Response:")
if result_first.get('response'):
    response_text = result_first.get('response', '').lower()
    has_greeting = any(keyword in response_text for keyword in ['namaste', 'ritesh sir', 'arivihan', 'main board exam'])

    if not has_greeting or len(response_text) < 50:
        print("   ✅ CORRECT: No greeting sent for first message")
    else:
        print("   ❌ INCORRECT: Greeting was sent for first message")
        print(f"   Response: {result_first.get('response', '')[:200]}...")
else:
    print("   ⚠️  No response generated")

# Analyze returning user response
print("\n2. Returning User Response:")
if result_returning.get('response'):
    response_text = result_returning.get('response', '').lower()
    has_greeting = any(keyword in response_text for keyword in ['namaste', 'hello', 'beta', 'kaise ho', 'ritesh'])

    if has_greeting:
        print("   ✅ CORRECT: Greeting sent for returning user")
    else:
        print("   ⚠️  WARNING: Expected greeting for returning user")
        print(f"   Response: {result_returning.get('response', '')[:200]}...")
else:
    print("   ⚠️  No response generated")

print("\n" + "="*80)
