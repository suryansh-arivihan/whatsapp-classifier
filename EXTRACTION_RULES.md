# Message Extraction Rules - Simple Format

## Goal
Transform this:
```json
{
  "classification": "...",
  "sub_classification": "...",
  "subject": "...",
  "language": "...",
  "response_data": {
    "status": "success",
    "data": { /* nested structure */ },
    "message": "..."
  },
  "processing_time_ms": 1234,
  "timestamp": "..."
}
```

Into this:
```json
{
  "status": "success",
  "message": "The actual text for the user"
}
```

---

## Extraction Rules by Handler

### 1. Guidance Handler (`guidance_based`)

**Path**: `response_data.data.response.text`

**Example Input**:
```json
{
  "response_data": {
    "status": "success",
    "data": {
      "classifiedAs": "guidance_based",
      "response": {
        "text": "<h2>How to Study Physics</h2><p>Here's how...</p>",
        "queryType": "guidance_related",
        "openWhatsapp": false
      },
      "openWhatsapp": false
    }
  }
}
```

**Output**:
```json
{
  "status": "success",
  "message": "<h2>How to Study Physics</h2><p>Here's how...</p>"
}
```

**Extraction Code**:
```python
message = response_data['data']['response']['text']
```

---

### 2. App Handler (`app_related`)

**Path**: `response_data.data.response` (direct string)

**Example Input**:
```json
{
  "response_data": {
    "status": "success",
    "data": {
      "classifiedAs": "app_related",
      "contentType": "lecture",
      "response": "❌ *Lecture mein neend aa jati h?*\n\n✅ *Ab lectures BORING nahi rahenge!*",
      "openWhatsapp": true
    }
  }
}
```

**Output**:
```json
{
  "status": "success",
  "message": "❌ *Lecture mein neend aa jati h?*\n\n✅ *Ab lectures BORING nahi rahenge!*"
}
```

**Extraction Code**:
```python
message = response_data['data']['response']
```

---

### 3. Exam Handler (`exam_related_info`)

**Path**: Check multiple locations in priority order:
1. `response_data.data.formatted_response` (if GPT formatting was applied)
2. `response_data.data.response.text` (if plain text)
3. `response_data.data.response` (if alternatives/questions)

**Example Input (formatted)**:
```json
{
  "response_data": {
    "status": "success",
    "data": {
      "classifiedAs": "no_questions_found",
      "response": {
        "alternatives": ["Try practice papers", "Check online resources"]
      },
      "formatted_response": "Here are some alternatives:\n\n1. Try practice papers...",
      "has_formatted_response": true
    }
  }
}
```

**Output**:
```json
{
  "status": "success",
  "message": "Here are some alternatives:\n\n1. Try practice papers..."
}
```

**Extraction Code**:
```python
data = response_data['data']
if data.get('formatted_response'):
    message = data['formatted_response']
elif isinstance(data.get('response'), dict) and 'text' in data['response']:
    message = data['response']['text']
else:
    # Need to format alternatives/questions
    message = format_response(data['response'])
```

---

### 4. Subject Handler (`subject_related`)

**Path**: `response_data.data.response.text`

**Example Input**:
```json
{
  "response_data": {
    "status": "success",
    "data": {
      "classifiedAs": "subject_related",
      "response": {
        "text": "Newton's First Law states that an object at rest stays at rest..."
      },
      "openWhatsapp": false
    }
  }
}
```

**Output**:
```json
{
  "status": "success",
  "message": "Newton's First Law states that an object at rest stays at rest..."
}
```

**Extraction Code**:
```python
message = response_data['data']['response']['text']
```

---

### 5. Conversation Handler (`conversation_based`)

**Path**: `response_data.data.response` (direct string)

**Example Input**:
```json
{
  "response_data": {
    "status": "success",
    "data": {
      "classifiedAs": "conversation_based",
      "response": "Hi! Welcome to Arivihan. How may I help you?",
      "openWhatsapp": false
    }
  }
}
```

**Output**:
```json
{
  "status": "success",
  "message": "Hi! Welcome to Arivihan. How may I help you?"
}
```

**Extraction Code**:
```python
message = response_data['data']['response']
```

---

### 6. Complaint Handler (`complaint`)

**Path**: `response_data.data.text`

**Example Input**:
```json
{
  "response_data": {
    "status": "success",
    "data": {
      "type": "complaint",
      "text": "We sincerely apologize for the inconvenience...",
      "ticket_created": false
    }
  }
}
```

**Output**:
```json
{
  "status": "success",
  "message": "We sincerely apologize for the inconvenience..."
}
```

**Extraction Code**:
```python
message = response_data['data']['text']
```

---

## Error Handling

**When `status` is `error`**:

**Input**:
```json
{
  "response_data": {
    "status": "error",
    "message": "Handler failed: Connection timeout"
  }
}
```

**Output**:
```json
{
  "status": "error",
  "message": "Handler failed: Connection timeout"
}
```

**Extraction Code**:
```python
if response_data.get('status') == 'error':
    message = response_data.get('message', 'An error occurred')
```

---

## Complete Extraction Function

```python
def extract_user_message(response_data: dict, classification: str) -> str:
    """
    Extract the user-facing message from response_data.

    Args:
        response_data: The response_data dict from handlers
        classification: The main classification type

    Returns:
        str: The extracted message for the user
    """
    if not response_data or 'data' not in response_data:
        return "Unable to generate response"

    data = response_data['data']

    # Handler-specific extraction
    if classification == 'guidance_based':
        # Path: data.response.text
        return data.get('response', {}).get('text', 'No guidance available')

    elif classification == 'app_related':
        # Path: data.response (direct string)
        return data.get('response', 'No content available')

    elif classification == 'exam_related_info':
        # Priority: formatted_response > response.text > response (formatted)
        if 'formatted_response' in data and data['formatted_response']:
            return data['formatted_response']

        response = data.get('response', {})
        if isinstance(response, dict) and 'text' in response:
            return response['text']

        # Need to format alternatives/questions
        return format_exam_response(response)

    elif classification == 'subject_related':
        # Path: data.response.text
        return data.get('response', {}).get('text', 'No answer available')

    elif classification == 'conversation_based':
        # Path: data.response (direct string)
        return data.get('response', 'Hello! How can I help you?')

    elif classification == 'complaint':
        # Path: data.text
        return data.get('text', 'Thank you for your feedback')

    # Fallback
    return str(data.get('response', 'Response generated'))


def format_exam_response(response: any) -> str:
    """Format exam response alternatives or questions."""
    if isinstance(response, dict):
        if 'alternatives' in response:
            alts = response['alternatives']
            return "Here are some suggestions:\n\n" + "\n".join(f"• {alt}" for alt in alts)

        if 'questions' in response:
            # Format questions nicely
            questions = response['questions']
            formatted = []
            for i, q in enumerate(questions, 1):
                formatted.append(f"Q{i}: {q.get('question', '')}")
            return "\n\n".join(formatted)

    return str(response)
```

---

## Testing Each Handler

Run the test script to verify:
```bash
python test_responses_observation.py
```

This will test all 6 handlers and show what message would be extracted for each.

---

## Implementation Location

**Recommended**: Add transformation in [app/api/routes.py](app/api/routes.py) after line 87:

```python
# Execute classification pipeline
response = await classify_message(request.message)

# Transform to simple format
simple_response = transform_to_simple_format(response)

logger.info(f"[API] Simplified response: {simple_response}")
return simple_response
```

Where `transform_to_simple_format()` uses the extraction logic above.
