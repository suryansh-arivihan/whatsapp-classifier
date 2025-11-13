"""
Complete FAQ Flow Test
Tests the entire classification and response flow for FAQ queries
"""
from app.services.main_classifier import initial_main_classifier
from app.services.exam_classifier import exam_related_main_classifier
from app.services.exam_faq_query import exam_faq_query_main

# Test query about marks/weightage
TEST_QUERY = "physics me sabse jyada number ka kis chapter se aata h"

print("=" * 80)
print("COMPLETE FAQ FLOW TEST")
print("=" * 80)
print(f"\nQuery: {TEST_QUERY}\n")

# Step 1: Main Classification
print("Step 1: Main Classification")
print("-" * 80)
main_classification = initial_main_classifier(TEST_QUERY)
print(f"Result: {main_classification}")
print()

# Step 2: Exam Sub-Classification
if main_classification == "exam_related_info":
    print("Step 2: Exam Sub-Classification")
    print("-" * 80)
    sub_classification = exam_related_main_classifier(TEST_QUERY)
    print(f"Result: {sub_classification}")
    print()

    # Step 3: FAQ Handler Processing
    if sub_classification == "faq":
        print("Step 3: FAQ Handler Processing")
        print("-" * 80)

        # Prepare payload
        faq_payload = {
            "userQuery": TEST_QUERY,
            "subject": "Physics",
            "language": "hinglish",
            "requestType": "text"
        }

        # Call FAQ handler
        faq_result = exam_faq_query_main(faq_payload, "exam_related_info")

        print(f"Status: {faq_result.get('classifiedAs')}")
        print(f"OpenWhatsApp: {faq_result.get('openWhatsapp')}")

        response = faq_result.get('response', '')
        if isinstance(response, dict):
            answer_text = response.get('text', 'N/A')
            print(f"\nAnswer Preview: {answer_text[:200]}...")
        else:
            print(f"\nResponse: {str(response)[:200]}...")

        print()
        print("=" * 80)
        print("FINAL RESULT:")
        print("=" * 80)

        if faq_result.get('openWhatsapp'):
            print("❌ FAQ couldn't answer → Will show app download message")
        else:
            print("✅ FAQ answered successfully!")
            print("\n📋 Complete Flow:")
            print(f"   1. Main Classification: {main_classification}")
            print(f"   2. Sub-Classification: {sub_classification}")
            print(f"   3. Handler: exam_faq_query_main (LOCAL)")
            print(f"   4. Result: Answer provided from FAQ database")
            print()
            if isinstance(response, dict):
                print(f"   Answer Format: HTML formatted response")
                print(f"   Query Type: {response.get('queryType')}")
                print(f"   Request Type: {response.get('request_type')}")
    else:
        print(f"❌ Expected sub-classification: faq")
        print(f"   Got: {sub_classification}")
else:
    print(f"❌ Expected main classification: exam_related_info")
    print(f"   Got: {main_classification}")

print("=" * 80)
