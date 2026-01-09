---
name: question-answering
description: Answer questions accurately and concisely based on knowledge and context. Use when the user asks questions, requests information, or needs clarification on any topic.
license: Apache-2.0
metadata:
  author: paracle
  version: "1.0.0"
  category: communication
  level: intermediate
  display_name: "Question Answering"
  tags:
    - qa
    - conversation
    - knowledge
    - information
  capabilities:
    - factual_responses
    - context_understanding
    - clarification
    - follow_up_questions
---

# Question Answering Skill

## When to use this skill

Use this skill when:
- User asks direct questions requiring factual answers
- Clarification is needed on concepts or topics
- Information lookup or knowledge retrieval is required
- Follow-up questions arise during conversation

## How it works

This skill enables agents to provide accurate, well-structured answers by:

1. **Understanding the question** - Parse intent and identify key information needs
2. **Retrieving knowledge** - Access relevant information from context or knowledge base
3. **Formulating response** - Structure answer clearly and concisely
4. **Validating accuracy** - Ensure factual correctness when possible

## Best practices

### 1. Be concise and direct

```
❌ Bad: "Well, that's an interesting question. Let me think about this. You know, there are many factors to consider..."

✓ Good: "The answer is X because Y."
```

### 2. Provide context when needed

```
❌ Bad: "42"

✓ Good: "42 is the answer to life, the universe, and everything according to Douglas Adams' 'The Hitchhiker's Guide to the Galaxy'"
```

### 3. Admit uncertainty

```
❌ Bad: [Making up information]

✓ Good: "I don't have enough information to answer that accurately. Could you provide more context?"
```

### 4. Structure complex answers

For multi-part questions:

1. Break down the question into components
2. Answer each part clearly
3. Summarize key points

Example:

**Question**: "What is Python and why is it popular?"

**Answer**:
- **What**: Python is a high-level, interpreted programming language
- **Why popular**:
  - Easy to learn and read
  - Versatile (web, data science, automation)
  - Large ecosystem of libraries
  - Strong community support

## Examples

### Example 1: Factual question

**Q**: "What is the capital of France?"
**A**: "Paris"

### Example 2: Conceptual question

**Q**: "What is machine learning?"
**A**: "Machine learning is a subset of AI where systems learn from data to improve performance without explicit programming. It involves training algorithms on datasets to recognize patterns and make predictions."

### Example 3: How-to question

**Q**: "How do I reverse a string in Python?"
**A**:
```python
# Method 1: Slicing (most Pythonic)
text = "hello"
reversed_text = text[::-1]  # "olleh"

# Method 2: reversed() function
reversed_text = ''.join(reversed(text))

# Method 3: Loop (explicit)
reversed_text = ''
for char in text:
    reversed_text = char + reversed_text
```

### Example 4: Comparison question

**Q**: "What's the difference between lists and tuples in Python?"
**A**:

| Feature     | List                 | Tuple                     |
| ----------- | -------------------- | ------------------------- |
| Mutability  | Mutable (can change) | Immutable (cannot change) |
| Syntax      | `[1, 2, 3]`          | `(1, 2, 3)`               |
| Performance | Slower               | Faster                    |
| Use case    | Dynamic data         | Fixed data                |

## Common patterns

### Pattern 1: Definition questions

Format: "**Term** is [definition]. It [purpose/context]."

### Pattern 2: Process questions

Format:
1. Step 1: [action]
2. Step 2: [action]
3. Result: [outcome]

### Pattern 3: Comparison questions

Format: Use tables or bullet points to compare side-by-side

### Pattern 4: Troubleshooting questions

Format:
- **Problem**: [issue]
- **Cause**: [reason]
- **Solution**: [fix]

## When to ask for clarification

Ask for more details when:
- Question is ambiguous or has multiple interpretations
- Missing critical context to provide accurate answer
- User terminology is unclear
- Scope of question is too broad

Example responses:
- "Could you clarify what you mean by [term]?"
- "Are you asking about [option A] or [option B]?"
- "What's your use case? This will help me provide a more relevant answer."

## Quality checks

Before responding, ensure:
- ✓ Question is fully understood
- ✓ Answer is accurate and factual
- ✓ Response is appropriate length (not too verbose)
- ✓ Examples provided when helpful
- ✓ Sources cited if making specific claims

## Limitations

This skill:
- Does not access real-time information unless tools are available
- Cannot provide opinions (only factual information)
- Cannot guarantee 100% accuracy on all topics
- Works best with clear, specific questions

## Related skills

- **text-summarization**: For condensing long answers
- **code-generation**: For coding-related questions
- **data-analysis**: For data-driven questions
