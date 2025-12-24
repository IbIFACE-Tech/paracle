---
name: code-generation
description: Generate high-quality code in various programming languages following best practices. Use when the user asks to write, create, or generate code, functions, classes, or scripts.
license: Apache-2.0
compatibility: Requires code_executor and file_system tools for testing and saving generated code
metadata:
  author: paracle
  version: "1.0.0"
  category: creation
  level: advanced
  display_name: "Code Generation"
  tags:
    - coding
    - programming
    - development
    - software
  capabilities:
    - multi_language_support
    - best_practices
    - documentation
    - error_handling
    - testing
  requirements:
    - skill_name: question-answering
      min_level: basic
allowed-tools: Read Write Bash(python:*) Bash(node:*) Bash(git:*)
---

# Code Generation Skill

## When to use this skill

Use this skill when:
- User requests code implementation
- Creating functions, classes, or modules
- Writing scripts or utilities
- Implementing algorithms
- Generating boilerplate code
- Creating test cases

## Supported languages

- **Python** 3.8+ (primary)
- **JavaScript/TypeScript** (ES6+, Node.js)
- **Java** 11+
- **C#** (.NET 6+)
- **Go** 1.18+
- **Rust** (latest stable)
- **SQL** (PostgreSQL, MySQL, SQLite)
- **Shell** (Bash, PowerShell)

## Code generation principles

### 1. Write clean, readable code

```python
# ❌ Bad: Unclear, no documentation
def f(x,y):return x if x>y else y

# ✓ Good: Clear, documented
def get_maximum(a: int, b: int) -> int:
    """Return the maximum of two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        The larger of a and b
    """
    return a if a > b else b
```

### 2. Follow language conventions

- **Python**: PEP 8, type hints, docstrings
- **JavaScript**: ESLint, JSDoc comments
- **Java**: Oracle style guide, JavaDoc
- **C#**: Microsoft conventions, XML docs

### 3. Include error handling

```python
def read_file(path: str) -> str:
    """Read file contents safely."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise ValueError(f"File not found: {path}")
    except PermissionError:
        raise ValueError(f"Permission denied: {path}")
    except Exception as e:
        raise ValueError(f"Error reading file: {e}")
```

### 4. Write testable code

```python
# Function with single responsibility
def validate_email(email: str) -> bool:
    """Validate email format."""
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

# Easy to test
def test_validate_email():
    assert validate_email("user@example.com") == True
    assert validate_email("invalid") == False
```

## Code generation workflow

### Step 1: Understand requirements

Ask clarifying questions if needed:
- What is the purpose of this code?
- What are the inputs and expected outputs?
- Are there performance constraints?
- What error cases should be handled?

### Step 2: Design the solution

- Identify necessary functions/classes
- Determine data structures
- Plan error handling strategy
- Consider edge cases

### Step 3: Generate code

- Write clean, documented code
- Follow best practices
- Include type hints/annotations
- Add error handling

### Step 4: Add tests

- Write unit tests for main functionality
- Cover edge cases
- Include negative test cases

### Step 5: Document usage

- Provide usage examples
- Explain parameters and return values
- Note any dependencies

## Examples

### Example 1: Python data processing

```python
from typing import List, Dict, Any
import json

def filter_users_by_age(
    users: List[Dict[str, Any]],
    min_age: int,
    max_age: int
) -> List[Dict[str, Any]]:
    """Filter users by age range.

    Args:
        users: List of user dictionaries with 'age' field
        min_age: Minimum age (inclusive)
        max_age: Maximum age (inclusive)

    Returns:
        Filtered list of users within age range

    Raises:
        ValueError: If min_age > max_age

    Example:
        >>> users = [{'name': 'Alice', 'age': 25}, {'name': 'Bob', 'age': 35}]
        >>> filter_users_by_age(users, 20, 30)
        [{'name': 'Alice', 'age': 25}]
    """
    if min_age > max_age:
        raise ValueError(f"min_age ({min_age}) cannot exceed max_age ({max_age})")

    return [
        user for user in users
        if 'age' in user and min_age <= user['age'] <= max_age
    ]

# Tests
def test_filter_users_by_age():
    users = [
        {'name': 'Alice', 'age': 25},
        {'name': 'Bob', 'age': 35},
        {'name': 'Charlie', 'age': 45},
    ]

    result = filter_users_by_age(users, 20, 40)
    assert len(result) == 2
    assert result[0]['name'] == 'Alice'
    assert result[1]['name'] == 'Bob'

    # Edge case: empty list
    assert filter_users_by_age([], 20, 40) == []

    # Edge case: invalid range
    try:
        filter_users_by_age(users, 40, 20)
        assert False, "Should raise ValueError"
    except ValueError:
        pass

if __name__ == "__main__":
    test_filter_users_by_age()
    print("All tests passed!")
```

### Example 2: JavaScript API client

```javascript
/**
 * HTTP client for REST API interactions
 */
class ApiClient {
  /**
   * @param {string} baseUrl - Base URL for API
   * @param {string} apiKey - API authentication key
   */
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.apiKey = apiKey;
  }

  /**
   * Make GET request
   * @param {string} endpoint - API endpoint
   * @returns {Promise<any>} Response data
   */
  async get(endpoint) {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`API request failed: ${error.message}`);
    }
  }

  /**
   * Make POST request
   * @param {string} endpoint - API endpoint
   * @param {object} data - Request payload
   * @returns {Promise<any>} Response data
   */
  async post(endpoint, data) {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`API request failed: ${error.message}`);
    }
  }
}

// Usage example
const client = new ApiClient('https://api.example.com', 'your-api-key');

// GET request
const users = await client.get('/users');
console.log(users);

// POST request
const newUser = await client.post('/users', {
  name: 'John Doe',
  email: 'john@example.com'
});
console.log(newUser);
```

### Example 3: SQL query generation

```sql
-- Create users table with proper constraints
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    -- Constraints
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'),
    CONSTRAINT username_length CHECK (LENGTH(username) >= 3)
);

-- Create index for faster lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- Insert user with validation
INSERT INTO users (username, email, password_hash)
VALUES ($1, $2, $3)
ON CONFLICT (email) DO NOTHING
RETURNING id, username, email, created_at;

-- Query active users with pagination
SELECT
    id,
    username,
    email,
    created_at,
    updated_at
FROM users
WHERE is_active = TRUE
ORDER BY created_at DESC
LIMIT $1 OFFSET $2;

-- Update user with timestamp
UPDATE users
SET
    username = $1,
    email = $2,
    updated_at = CURRENT_TIMESTAMP
WHERE id = $3 AND is_active = TRUE
RETURNING id, username, email, updated_at;
```

## Best practices checklist

Before delivering code, verify:

- [ ] **Functionality**: Code works as expected
- [ ] **Documentation**: Docstrings/comments explain purpose
- [ ] **Type hints**: Types specified (Python, TypeScript)
- [ ] **Error handling**: Exceptions caught and handled
- [ ] **Edge cases**: Null/empty/boundary conditions covered
- [ ] **Tests**: Unit tests provided
- [ ] **Naming**: Variables/functions named clearly
- [ ] **Formatting**: Code follows style guide
- [ ] **Dependencies**: External libraries documented
- [ ] **Security**: No hardcoded secrets, SQL injection prevention

## Code patterns

### Singleton pattern (Python)

```python
class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.connection = cls._create_connection()
        return cls._instance

    @staticmethod
    def _create_connection():
        # Create database connection
        pass
```

### Builder pattern (JavaScript)

```javascript
class QueryBuilder {
  constructor() {
    this.query = { select: [], where: [], orderBy: [] };
  }

  select(...fields) {
    this.query.select.push(...fields);
    return this;
  }

  where(condition) {
    this.query.where.push(condition);
    return this;
  }

  orderBy(field, direction = 'ASC') {
    this.query.orderBy.push({ field, direction });
    return this;
  }

  build() {
    return this.query;
  }
}

// Usage
const query = new QueryBuilder()
  .select('id', 'name')
  .where('age > 18')
  .orderBy('name')
  .build();
```

## Performance considerations

1. **Algorithm complexity**: Prefer O(n) over O(n²)
2. **Memory usage**: Avoid unnecessary copies
3. **I/O operations**: Use async/await, batch operations
4. **Caching**: Cache expensive computations
5. **Database**: Use indexes, avoid N+1 queries

## Security considerations

1. **Input validation**: Sanitize all user inputs
2. **SQL injection**: Use parameterized queries
3. **XSS prevention**: Escape output in HTML contexts
4. **Authentication**: Never hardcode credentials
5. **Secrets**: Use environment variables
6. **Dependencies**: Keep libraries up to date

## Related skills

- **code-review**: For analyzing and improving generated code
- **debugging**: For fixing issues in generated code
- **api-integration**: For creating API clients
- **data-analysis**: For data processing code

## References

- [Python PEP 8](https://peps.python.org/pep-0008/)
- [JavaScript Style Guide](https://github.com/airbnb/javascript)
- [Clean Code Principles](https://github.com/ryanmcdermott/clean-code-javascript)
