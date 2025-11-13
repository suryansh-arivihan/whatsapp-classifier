# Test Classification Quick Reference Guide

## When users ask about TESTS, how do we classify?

### Rule 1: Check the PRIMARY INTENT

**Is the user trying to ACCESS/GET/TAKE a test?** → `app_related`
**Is the user asking INFORMATION about tests?** → `exam_related_info`

---

## Classification Decision Tree

```
User mentions "test" in query
    ↓
    ├─ Contains access keywords?
    │  ("chahiye", "do", "milega", "kaha hai", "dena hai")
    │  ↓
    │  YES → app_related
    │      ↓
    │      app_data_related
    │      ↓
    │      Content Classification:
    │      ├─ "chapterwise" / specific chapter → test_chapterwise
    │      └─ "full" / "complete" / no chapter → test_full_length
    │
    └─ Contains information keywords?
       ("kya aata hai", "pattern kya hai", "kitne marks")
       ↓
       YES → exam_related_info
           ↓
           faq or asking_test sub-classification
```

---

## Examples with Classification

### ✅ app_related (Test Access)

| Query | Why app_related? | Content Type |
|-------|------------------|--------------|
| "physics ke chapterwise test kaha milege?" | Asking WHERE to get → access question | test_chapterwise |
| "test chahiye chemistry ka" | Wants to GET test → access request | test_full_length |
| "chapter 1 ka test do" | Wants test for chapter → access request | test_chapterwise |
| "mock test dena hai" | Wants to TAKE test → access request | test_full_length |
| "electric charge ka test" | Wants specific chapter test → access | test_chapterwise |
| "physics ka full test chahiye" | Wants complete test → access request | test_full_length |

### ❌ exam_related_info (Test Information)

| Query | Why exam_related_info? | Sub Type |
|-------|------------------------|----------|
| "test me kya questions aate hain" | Asking ABOUT test content → information | faq |
| "test ka pattern kya hai" | Asking ABOUT test format → information | faq |
| "test kitne marks ka hota hai" | Asking ABOUT test structure → information | faq |
| "test me kitne sections hote hain" | Asking ABOUT test sections → information | faq |

---

## Access Keywords (→ app_related)

| Keyword | Example | Meaning |
|---------|---------|---------|
| chahiye | "test chahiye" | want/need |
| do | "test do" | give me |
| milega | "test milega?" | will I get? |
| kaha hai | "test kaha hai" | where is? |
| kaha milege | "test kaha milege" | where will I find? |
| dena hai | "test dena hai" | want to take |
| lena hai | "test lena hai" | want to take |
| attempt | "test attempt karna hai" | want to attempt |

## Information Keywords (→ exam_related_info)

| Keyword | Example | Meaning |
|---------|---------|---------|
| kya aata hai | "test me kya aata hai" | what comes in |
| pattern kya hai | "test ka pattern kya hai" | what's the pattern |
| kitne marks | "test kitne marks ka hai" | how many marks |
| kaise hota hai | "test kaise hota hai" | how does it work |
| kitne questions | "test me kitne questions" | how many questions |

---

## Content Type Classification (within app_related)

After main classification as `app_related` → `app_data_related`, the **simple_classify()** function determines:

### test_chapterwise
- User mentions specific chapter: "chapter 1", "chapter 2"
- User mentions specific topic: "electric charge", "optics"
- User mentions "chapterwise": "chapterwise test"
- Keywords: "chapter ka test", "topic test", "chapterwise"

### test_full_length
- User mentions "full": "full test"
- User mentions "complete": "complete test"
- User mentions "mock": "mock test"
- General subject-level request: "physics ka test" (without chapter)
- Keywords: "full test", "complete test", "mock test"

---

## Response Templates

### test_chapterwise (Hindi)
```
📚 *अध्याय पूरा कर लिया?*
*लगता है सब समझ आ गया?* 🤔
👉 *तो फिर पक्का पता करने का एक ही तरीका है - टेस्ट दो!*
...
```

### test_full_length (Hindi)
```
⏰ *परीक्षा में समय पर पेपर खत्म नहीं होता?*
*पढ़ तो लेते हो... par exam mein marks nahi aate?* 😟
...
```

---

## Common Mistakes to Avoid

| ❌ Wrong | ✅ Correct | Reason |
|----------|-----------|---------|
| "test chahiye" → exam_related_info | "test chahiye" → app_related | User wants to ACCESS test, not info about it |
| "chapterwise test kaha milege" → exam_related_info | "chapterwise test kaha milege" → app_related | "kaha milege" = WHERE to get = access question |
| "test me kya aata hai" → app_related | "test me kya aata hai" → exam_related_info | Asking ABOUT test content, not accessing test |

---

## Implementation Files

1. **[app/services/main_classifier.py](app/services/main_classifier.py)**
   - Main routing logic (app_related vs exam_related_info)

2. **[app/services/app_related_classifier.py](app/services/app_related_classifier.py)**
   - Sub-classification (app_data_related, screen_data_related, subscription)

3. **[app/services/content_classifier.py](app/services/content_classifier.py)**
   - Content type classification (test_chapterwise vs test_full_length)

4. **[app/services/content_responses.py](app/services/content_responses.py)**
   - Response templates for each content type

---

## Testing

To test a query:

```python
# Example test
query = "physics ke chapterwise test kaha milege?"

# Expected flow:
# 1. Main: app_related
# 2. App Sub: app_data_related
# 3. Content: test_chapterwise
# 4. Response: CONTENT_RESPONSES['test_chapterwise']['hindi']
```

---

## Summary

🎯 **Key Principle**:
- If user wants to ACCESS/GET/TAKE test → **app_related**
- If user wants INFO ABOUT test → **exam_related_info**

🔑 **Quick Check**:
- Can we answer by giving them a test? → **app_related**
- Do we need to explain something about tests? → **exam_related_info**
