# Test Patterns by Language

## Python (pytest)

### File structure
```
tests/
├── conftest.py          # Shared fixtures
├── test_<module>.py     # One per source module
├── test_integration.py  # Cross-module tests
└── test_edge_cases.py   # Edge cases & error handling
```

### Naming
- Files: `test_<module>.py`
- Classes: `Test<ClassName>`
- Functions: `test_<method>_<scenario>`

### Template
```python
import pytest
from <module> import <function_or_class>

class TestClassName:
    """Tests for ClassName."""

    def test_normal_input(self):
        result = function(valid_input)
        assert result == expected

    def test_boundary_value(self):
        result = function(boundary_input)
        assert result == expected

    def test_empty_input(self):
        result = function("")
        assert result == expected_empty

    def test_none_input(self):
        with pytest.raises(TypeError):
            function(None)

    def test_invalid_type(self):
        with pytest.raises((TypeError, ValueError)):
            function(invalid_input)

    @pytest.mark.parametrize("input_val,expected", [
        (case1_input, case1_expected),
        (case2_input, case2_expected),
    ])
    def test_parametrized(self, input_val, expected):
        assert function(input_val) == expected
```

### Fixtures (conftest.py)
```python
import pytest

@pytest.fixture
def sample_data():
    return {"key": "value", "count": 42}

@pytest.fixture
def temp_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("test content")
    return f
```

---

## JavaScript/TypeScript (Jest)

### File structure
```
__tests__/
├── <module>.test.js
├── integration/
│   └── <feature>.test.js
└── helpers/
    └── setup.js
```

### Template
```javascript
const { functionName } = require('../src/module');

describe('functionName', () => {
  test('returns expected for valid input', () => {
    expect(functionName(validInput)).toBe(expected);
  });

  test('handles empty input', () => {
    expect(functionName('')).toBe(expectedEmpty);
  });

  test('handles null/undefined', () => {
    expect(() => functionName(null)).toThrow();
  });

  test('handles boundary values', () => {
    expect(functionName(Number.MAX_SAFE_INTEGER)).toBe(expected);
    expect(functionName(0)).toBe(expected);
    expect(functionName(-1)).toBe(expected);
  });

  test.each([
    [input1, expected1],
    [input2, expected2],
  ])('returns %s for input %s', (input, expected) => {
    expect(functionName(input)).toBe(expected);
  });
});
```

### Async tests
```javascript
test('async operation resolves', async () => {
  const result = await asyncFunction();
  expect(result).toBeDefined();
});

test('async operation rejects on error', async () => {
  await expect(asyncFunction(badInput)).rejects.toThrow('error message');
});
```

---

## Java (JUnit 5)

### File structure
```
src/test/java/com/example/
├── ClassNameTest.java
├── integration/
│   └── FeatureIntegrationTest.java
└── util/
    └── TestHelpers.java
```

### Template
```java
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import static org.junit.jupiter.api.Assertions.*;

class ClassNameTest {

    @Test
    @DisplayName("Normal input returns expected result")
    void testNormalInput() {
        assertEquals(expected, instance.method(validInput));
    }

    @Test
    @DisplayName("Null input throws NullPointerException")
    void testNullInput() {
        assertThrows(NullPointerException.class, () -> instance.method(null));
    }

    @Test
    @DisplayName("Empty input returns default")
    void testEmptyInput() {
        assertEquals(defaultValue, instance.method(""));
    }

    @ParameterizedTest
    @CsvSource({"input1, expected1", "input2, expected2"})
    void testParameterized(String input, String expected) {
        assertEquals(expected, instance.method(input));
    }
}
```

---

## Go (go test)

### File structure
```
module_test.go    # Same package, _test.go suffix
```

### Template
```go
package mypackage

import "testing"

func TestFunctionName_NormalInput(t *testing.T) {
    got := FunctionName(validInput)
    want := expected
    if got != want {
        t.Errorf("FunctionName(%v) = %v, want %v", validInput, got, want)
    }
}

func TestFunctionName_EdgeCases(t *testing.T) {
    tests := []struct {
        name  string
        input InputType
        want  OutputType
    }{
        {"empty input", emptyVal, defaultVal},
        {"boundary max", maxVal, expectedMax},
        {"negative", negVal, expectedNeg},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := FunctionName(tt.input)
            if got != tt.want {
                t.Errorf("got %v, want %v", got, tt.want)
            }
        })
    }
}
```

---

## Test Categories Checklist

### Unit Tests
- [ ] Each public function has at least one test
- [ ] Each class method has at least one test
- [ ] Return values verified
- [ ] Side effects verified

### Edge Case Tests
- [ ] Empty string / empty list / empty map
- [ ] Null / None / nil / undefined
- [ ] Zero, negative, MAX_INT, MIN_INT
- [ ] Single element collections
- [ ] Very large inputs
- [ ] Unicode / special characters
- [ ] Concurrent access (if applicable)

### Error Handling Tests
- [ ] Invalid input types
- [ ] Out of range values
- [ ] Missing required fields
- [ ] Malformed data
- [ ] Network/IO failures (mocked)
- [ ] Permission denied scenarios

### Integration Tests
- [ ] Module A → Module B interaction
- [ ] Database operations (if applicable)
- [ ] API endpoint responses (if applicable)
- [ ] File I/O operations
- [ ] External service calls (mocked)
