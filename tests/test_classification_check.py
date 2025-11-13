"""
Check what classification and sub-classification the query is getting.
"""
from app.services.main_classifier import initial_main_classifier
from app.services.exam_classifier import exam_related_main_classifier

TEST_QUERY = "physics me important questions chahiye h"

print("="*80)
print("CLASSIFICATION CHECK")
print("="*80)
print(f"\nQuery: {TEST_QUERY}\n")

# Step 1: Main classification
print("Step 1: Main Classification")
print("-"*80)
main_classification = initial_main_classifier(TEST_QUERY)
print(f"Result: {main_classification}")
print()

# Step 2: If exam_related, get sub-classification
if main_classification == "exam_related_info":
    print("Step 2: Exam Sub-Classification")
    print("-"*80)
    sub_classification = exam_related_main_classifier(TEST_QUERY)
    print(f"Result: {sub_classification}")
    print()

    print("="*80)
    print("ANALYSIS:")
    print("="*80)
    print(f"✓ Main: {main_classification}")
    print(f"✓ Sub: {sub_classification}")
    print()

    if sub_classification == "asking_important_question":
        print("✅ Correct! This should trigger the important_questions template")
    else:
        print(f"❌ Wrong sub-classification!")
        print(f"   Expected: asking_important_question")
        print(f"   Got: {sub_classification}")
        print()
        print("SOLUTION: Update exam_classifier to detect 'important questions' queries")
else:
    print("="*80)
    print("ANALYSIS:")
    print("="*80)
    print(f"Main classification: {main_classification}")
    print(f"❌ This query is not classified as exam_related_info!")
    print()
    print("SOLUTION: Either:")
    print("  1. Update main_classifier to classify this as exam_related_info")
    print("  2. OR add the logic to the current handler")

print("="*80)
