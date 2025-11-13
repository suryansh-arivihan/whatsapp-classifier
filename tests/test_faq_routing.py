"""
Test script to verify FAQ routing to local exam_faq_query handler
"""
import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.handlers.exam_handler import exam_handler

async def test_faq_routing():
    """Test that FAQ queries are routed to local handler"""

    # Test query
    query = "phsyics me sabse jyada number ka kis chapter se aata h"

    # Classification data simulating FAQ sub-classification
    classification_data = {
        "classification": "exam_related_info",
        "sub_classification": "faq",
        "subject": "Physics",
        "language": "Hinglish",
    }

    print("=" * 60)
    print("Testing FAQ Routing to Local Handler")
    print("=" * 60)
    print(f"\nQuery: {query}")
    print(f"Sub-classification: {classification_data['sub_classification']}")
    print(f"Subject: {classification_data['subject']}")
    print(f"Language: {classification_data['language']}")
    print("\n" + "-" * 60)

    try:
        # Call the handler
        result = await exam_handler.handle(query, classification_data)

        print("\nResult Status:", result.get("status"))
        print("Message:", result.get("message"))

        data = result.get("data", {})
        print("\nData:")
        print(f"  - classifiedAs: {data.get('classifiedAs')}")
        print(f"  - sub_classification: {data.get('sub_classification')}")
        print(f"  - source: {data.get('source')}")
        print(f"  - openWhatsapp: {data.get('openWhatsapp')}")
        print(f"  - responseType: {data.get('responseType')}")

        response = data.get("response", "")
        if isinstance(response, dict):
            print(f"\nResponse Type: dict")
            print(f"  - text: {response.get('text', 'N/A')[:200]}...")
            print(f"  - queryType: {response.get('queryType', 'N/A')}")
        else:
            print(f"\nResponse Text: {str(response)[:200]}...")

        metadata = result.get("metadata", {})
        print(f"\nMetadata:")
        print(f"  - subject: {metadata.get('subject')}")
        print(f"  - language: {metadata.get('language')}")
        print(f"  - source: {metadata.get('source')}")

        print("\n" + "=" * 60)
        print("✓ Test completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_faq_routing())
