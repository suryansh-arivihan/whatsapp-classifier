"""Debug chapterwise test query flow"""
import sys
import os

# Simulate direct classification
query = "physics ke chapterwise test kaha milege ?"

print("="*80)
print("DEBUG: CHAPTERWISE TEST QUERY")
print("="*80)
print(f"\nQuery: {query}\n")

# Test 1: Check main classification logic
print("\n" + "="*80)
print("STEP 1: Main Classification")
print("="*80)
print("\nExpected: app_related (because asking WHERE to get tests - kaha milege)")
print("Reasoning: User is asking about HOW TO ACCESS content from the platform")
print("Keywords: 'kaha milege' indicates platform/app access question")

# Test 2: Check app sub-classification
print("\n" + "="*80)
print("STEP 2: App Sub-Classification")
print("="*80)
print("\nExpected: app_data_related")
print("Reasoning: User wants to ACCESS specific content (test)")
print("NOT screen_data_related because not asking 'kaise' (how to use)")
print("NOT subscription_data_related because not about pricing/payment")

# Test 3: Check content type classification
print("\n" + "="*80)
print("STEP 3: Content Type Classification")
print("="*80)
print("\nExpected: test_chapterwise")
print("Reasoning: Query explicitly mentions 'chapterwise test'")
print("Should match rule: 'Mentions specific chapter, topic, or chapterwise'")
print("Keywords: 'chapterwise test'")

# Test 4: What response should be returned
print("\n" + "="*80)
print("STEP 4: Expected Response")
print("="*80)
print("\nShould return: CONTENT_RESPONSES['test_chapterwise']['hindi']")
print("\nExpected message preview:")
print("📚 *अध्याय पूरा कर लिया?*")
print("*लगता है सब समझ आ गया?* 🤔")
print("...")

# Actual result you're getting
print("\n" + "="*80)
print("ACTUAL RESULT YOU'RE GETTING")
print("="*80)
print("\nYou're getting: test_full_length template")
print("Message: ⏰ *परीक्षा में समय पर पेपर खत्म नहीं होता?*")
print("\nPossible causes:")
print("1. Main classifier might be sending to exam_related_info instead of app_related")
print("2. Content classifier (simple_classify) might be misclassifying as test_full_length")
print("3. app_related_classifier might be routing incorrectly")

print("\n" + "="*80)
print("DIAGNOSIS NEEDED")
print("="*80)
print("\nTo diagnose, we need to check:")
print("1. What does initial_main_classifier return?")
print("2. If app_related, what does app_related_classifier_main return?")
print("3. If app_data_related, what does simple_classify return?")
print("4. What template is being used?")

print("\nLet's test the content classifier directly...")
print("="*80)

# Test content classifier
try:
    from app.services.content_classifier import simple_classify

    print("\nTesting simple_classify directly:")
    test_queries = [
        "physics ke chapterwise test kaha milege?",
        "physics ke chapter test chahiye",
        "chapterwise test do physics ka",
        "chapter 1 ka test chahiye",
        "physics ka full test chahiye",
        "complete test dena hai physics ka"
    ]

    for test_query in test_queries:
        try:
            result = simple_classify(test_query)
            print(f"\n  Query: {test_query}")
            print(f"  Result: {result}")
        except Exception as e:
            print(f"\n  Query: {test_query}")
            print(f"  Error: {e}")

except Exception as e:
    print(f"\nCannot test simple_classify: {e}")
    print("\nThis might be a pydantic version issue.")

print("\n" + "="*80)
