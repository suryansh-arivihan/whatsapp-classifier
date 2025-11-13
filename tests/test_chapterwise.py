"""Test chapterwise test query"""
import json
from app.services.classification_pipeline import classify_message

# Test query
test_message = "physics ke chapterwise test kaha milege ?"
metadata = {"user_id": "user123"}

print("="*80)
print("CHAPTERWISE TEST QUERY")
print("="*80)
print(f"\nQuery: {test_message}\n")

# Run classification
result = classify_message(test_message, metadata)

print("Classification Result:")
print("-"*80)
print(json.dumps(result, indent=2, ensure_ascii=False))
print("="*80)
