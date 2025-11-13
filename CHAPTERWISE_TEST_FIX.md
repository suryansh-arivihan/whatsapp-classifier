# Chapterwise Test Classification Fix

## Problem

When users ask **"physics ke chapterwise test kaha milege?"**, they were receiving the wrong response template:

### What they got (WRONG):
```
⏰ *परीक्षा में समय पर पेपर खत्म नहीं होता?*
*पढ़ तो लेते हो... par exam mein marks nahi aate?* 😟
...
```
This is the **test_full_length** template.

### What they should get (CORRECT):
```
📚 *अध्याय पूरा कर लिया?*
*लगता है सब समझ आ गया?* 🤔
👉 *तो फिर पक्का पता करने का एक ही तरीका है - टेस्ट दो!*
...
```
This is the **test_chapterwise** template.

---

## Root Cause

The **main classifier** had a blanket rule that ANY query mentioning "test" or "questions" should be classified as `exam_related_info`:

```python
# Old rule in main_classifier.py (lines 243-257)
**SPECIAL RULE - QUESTION REQUESTS:**
ANY request for questions, MCQs, or practice materials should ALWAYS be
classified as exam_related_info
- "test questions" → exam_related_info
```

This didn't account for the distinction between:
1. **Test ACCESS requests** (wanting to get/take tests from the platform) → should be `app_related`
2. **Test INFO questions** (asking about test patterns, content) → should be `exam_related_info`

### Old Flow (BROKEN):
```
Query: "physics ke chapterwise test kaha milege?"
  ↓
Main Classifier → exam_related_info (WRONG!)
  ↓
Exam Sub-Classifier → asking_test
  ↓
Exam Handler → Falls through to default/external API
  ↓
Result → Wrong template (test_full_length or generic message)
```

---

## Solution

Updated [main_classifier.py](app/services/main_classifier.py) to distinguish between test access and test information requests.

### Changes Made:

#### 1. Added Test Access to app_related section (lines 106-108)
```python
- **ALL REQUESTS FOR TESTS (accessing/getting tests)**
  (e.g., "Test chahiye", "Physics ka test do", "Chapterwise test kaha milege",
  "Mock test dena hai")
  - Keywords: "test chahiye", "test do", "test milega", "test kaha hai",
    "test dena hai", "mock test"
  - These are about ACCESSING/GETTING test content from the platform
```

#### 2. Added Exception Rule in exam_related_info section (lines 256-262)
```python
**EXCEPTION FOR TEST REQUESTS:**
HOWEVER, when someone is asking for TESTS (not questions about tests),
classify as app_related:
- "test chahiye" → app_related (wants to ACCESS test)
- "physics ka test do" → app_related (wants to GET test)
- "chapterwise test kaha milege" → app_related (wants to FIND test location)
- "mock test dena hai" → app_related (wants to TAKE test)
- BUT "test me kya questions aate hain" → exam_related_info (asking ABOUT test content)
```

#### 3. Updated CRITICAL DISTINCTION examples (lines 276-279)
```python
10. app_related: "physics ke chapterwise test kaha milege" (asking WHERE to ACCESS tests)
11. app_related: "test chahiye physics ka" (wants to GET test content)
12. app_related: "mock test dena hai" (wants to TAKE/ATTEMPT test)
13. exam_related_info: "test me kitne marks ka paper hota hai" (asking ABOUT test structure)
```

#### 4. Updated KEY INDICATORS (lines 140-143, 290-293)
```python
# app_related:
**IMPORTANT: ALL TEST ACCESS REQUESTS are classified as app_related
(e.g., "test chahiye", "test kaha milege", "mock test dena hai")**

# exam_related_info:
**IMPORTANT RULE:** ANY request to ACCESS/GET/TAKE TESTS should ALWAYS be
classified as app_related, NOT exam_related_info.
```

---

## New Flow (FIXED):

```
Query: "physics ke chapterwise test kaha milege?"
  ↓
Main Classifier → app_related ✅
  ↓
App Sub-Classifier → app_data_related ✅
  ↓
Content Classifier (simple_classify) → test_chapterwise ✅
  ↓
Content Response → CONTENT_RESPONSES['test_chapterwise']['hindi'] ✅
  ↓
Result → Correct chapterwise test template ✅
```

---

## Test Cases

| Query | Main Class | Sub Class | Content Type | Template |
|-------|-----------|-----------|--------------|----------|
| "physics ke chapterwise test kaha milege?" | `app_related` | `app_data_related` | `test_chapterwise` | test_chapterwise (Hindi) |
| "chapter 1 ka test do" | `app_related` | `app_data_related` | `test_chapterwise` | test_chapterwise |
| "full test dena hai physics ka" | `app_related` | `app_data_related` | `test_full_length` | test_full_length |
| "test me kya questions aate hain" | `exam_related_info` | `faq` | N/A | FAQ response |

---

## Keywords that Trigger app_related for Tests

✅ **Access/Get keywords:**
- "test chahiye"
- "test do"
- "test milega"
- "test kaha hai"
- "test kaha milege"

✅ **Action keywords:**
- "test dena hai"
- "test attempt karna hai"
- "mock test lena hai"

✅ **Type keywords:**
- "chapterwise test"
- "full test"
- "complete test"
- "mock test"

❌ **Information keywords (exam_related_info):**
- "test me kya aata hai"
- "test ka pattern kya hai"
- "test kitne marks ka hota hai"

---

## Verification

To verify the fix works:

1. Start the application:
   ```bash
   python -m uvicorn app.api.routes:app --host 0.0.0.0 --port 8080
   ```

2. Send test request:
   ```bash
   curl -X POST http://localhost:8080/classify \
     -H "Content-Type: application/json" \
     -d '{
       "message": "physics ke chapterwise test kaha milege?",
       "metadata": {"user_id": "test123"}
     }'
   ```

3. Expected response should contain:
   - `"classification": "app_related"`
   - Message starting with: `"📚 *अध्याय पूरा कर लिया?*"`

---

## Files Modified

1. **[app/services/main_classifier.py](app/services/main_classifier.py)**
   - Lines 106-108: Added test access to app_related
   - Lines 140: Added important rule for test access
   - Lines 142-143: Updated KEY INDICATOR
   - Lines 256-262: Added exception for test requests
   - Lines 276-279: Added examples
   - Lines 290: Added important rule
   - Lines 292-293: Updated KEY INDICATOR

---

## Additional Notes

- The **content_classifier.py** already had proper logic to distinguish between:
  - `test_chapterwise`: Chapter-specific or topic-specific tests
  - `test_full_length`: Full-length tests covering complete syllabus

- The **content_responses.py** already had the correct templates for both test types.

- The issue was ONLY in the **main_classifier.py** routing logic, which has now been fixed.

---

## Impact

This fix ensures that:
- ✅ All test access requests go through the app_related → content classification flow
- ✅ The correct template (chapterwise vs full_length) is determined by GPT based on the query
- ✅ Test information questions still go to exam_related_info for FAQ handling
- ✅ No breaking changes to other classification flows
