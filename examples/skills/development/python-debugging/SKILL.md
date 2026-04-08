---
name: python-debugging
description: Comprehensive guide for debugging Python applications including using pdb, logging, and common troubleshooting patterns
platforms: [linux, macos, windows]
required_tools: [execute_shell_command, read_file, write_file]
tags: [python, debugging, troubleshooting, development]
author: DominusPrime
version: 1.0.0
---

# Python Debugging Skill

## Overview

This skill provides a systematic approach to debugging Python applications, from simple syntax errors to complex runtime issues.

## When to Use

- Python script crashes or raises exceptions
- Unexpected behavior or incorrect output
- Need to trace execution flow
- Performance issues or infinite loops
- Import errors or module not found issues

## Prerequisites

- Python installed on the system
- Access to the Python source code
- Basic understanding of Python syntax

## Debugging Steps

### 1. Read Error Messages Carefully

Error messages contain valuable information:
- **Exception type**: What went wrong (NameError, TypeError, etc.)
- **Error message**: Specific details about the error
- **Traceback**: Where the error occurred (file, line number)

```python
# Example error:
# Traceback (most recent call last):
#   File "script.py", line 42, in main
#     result = calculate(x, y)
# TypeError: calculate() missing 1 required positional argument: 'y'
```

### 2. Use Print Debugging

Add print statements to trace execution:

```python
def calculate(x, y):
    print(f"DEBUG: calculate called with x={x}, y={y}")
    result = x + y
    print(f"DEBUG: result={result}")
    return result
```

### 3. Use the Python Debugger (pdb)

Insert breakpoints in your code:

```python
import pdb

def problematic_function(data):
    pdb.set_trace()  # Execution will pause here
    # You can now inspect variables, step through code
    result = process(data)
    return result
```

**Common pdb commands:**
- `n` (next): Execute current line
- `s` (step): Step into function
- `c` (continue): Continue execution
- `l` (list): Show source code
- `p variable`: Print variable value
- `pp variable`: Pretty-print variable
- `w` (where): Show stack trace
- `q` (quit): Exit debugger

### 4. Use Logging Instead of Print

For production code, use the logging module:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def my_function(x):
    logger.debug(f"Processing x={x}")
    logger.info("Function completed successfully")
    logger.warning("Potential issue detected")
    logger.error("Error occurred")
```

### 5. Run with Python Debugger Mode

Run script directly in debugger:

```bash
python -m pdb script.py
```

Or with post-mortem debugging:

```bash
python -i script.py  # Drops to interactive shell on crash
```

### 6. Common Issues and Solutions

**Import Errors:**
- Check PYTHONPATH
- Verify module installation: `pip list | grep module_name`
- Check for circular imports

**AttributeError:**
- Verify object type: `print(type(obj))`
- Check available attributes: `print(dir(obj))`

**IndentationError:**
- Use consistent tabs/spaces (prefer 4 spaces)
- Check mixed indentation

**Performance Issues:**
- Use `cProfile` for profiling: `python -m cProfile script.py`
- Check for infinite loops
- Look for unnecessary nested loops

### 7. Interactive Debugging

Use Python's interactive mode for quick tests:

```bash
python
>>> import my_module
>>> my_module.my_function(test_data)
>>> # Test and inspect interactively
```

## Advanced Techniques

### Exception Handling

```python
try:
    risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    # exc_info=True includes full traceback
```

### Context Managers for Debugging

```python
import contextlib
import time

@contextlib.contextmanager
def timer(name):
    start = time.time()
    yield
    print(f"{name} took {time.time() - start:.2f}s")

with timer("my_operation"):
    expensive_function()
```

### Remote Debugging

For debugging running processes, use `pdb` remote:

```python
import pdb
import sys

# Remote debugging setup
pdb.Pdb(stdin=sys.stdin, stdout=sys.stdout).set_trace()
```

## Tips and Best Practices

1. **Isolate the problem**: Create minimal reproducible example
2. **Check assumptions**: Verify variable types and values
3. **Read documentation**: Check function signatures and expected behavior
4. **Use version control**: Compare with last working version
5. **Rubber duck debugging**: Explain the problem out loud
6. **Take breaks**: Fresh eyes often spot issues faster

## Tool Integration

### Using DominusPrime Tools

```python
# Read the problematic file
await read_file(path="script.py")

# Check Python installation
await execute_shell_command(command="python --version")

# Run with debugger
await execute_shell_command(command="python -m pdb script.py")

# Install debugging tools
await execute_shell_command(command="pip install ipdb pudb")
```

## References

See the `references/` directory for:
- `pdb-quick-reference.md`: Complete pdb command reference
- `common-errors.md`: Database of common Python errors
- `debugging-checklist.md`: Step-by-step debugging checklist

## Related Skills

- `python-profiling`: Performance optimization
- `python-testing`: Unit testing and TDD
- `log-analysis`: Analyzing application logs
