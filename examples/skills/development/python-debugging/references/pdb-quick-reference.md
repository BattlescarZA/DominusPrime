# PDB Quick Reference

## Starting the Debugger

```python
import pdb

# Set breakpoint
pdb.set_trace()

# Post-mortem debugging
try:
    problematic_code()
except:
    import pdb
    pdb.post_mortem()
```

## Navigation Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `next` | `n` | Execute current line, step over functions |
| `step` | `s` | Execute current line, step into functions |
| `continue` | `c` | Continue execution until next breakpoint |
| `return` | `r` | Continue until current function returns |
| `until` | `unt` | Continue until line greater than current |
| `jump` | `j` | Jump to specified line number |

## Inspection Commands

| Command | Description |
|---------|-------------|
| `list` or `l` | Show source code around current line |
| `ll` | Show full source of current function |
| `where` or `w` | Show stack trace |
| `up` or `u` | Move up one stack frame |
| `down` or `d` | Move down one stack frame |
| `args` or `a` | Print arguments of current function |
| `p expression` | Print expression value |
| `pp expression` | Pretty-print expression value |
| `whatis variable` | Print type of variable |
| `source object` | Show source code for object |

## Breakpoint Commands

| Command | Description |
|---------|-------------|
| `break` or `b` | Set breakpoint |
| `b 42` | Set breakpoint at line 42 |
| `b module.function` | Set breakpoint at function |
| `b 42, condition` | Conditional breakpoint |
| `tbreak` | Temporary breakpoint (removed after hit) |
| `clear` | Clear all breakpoints |
| `disable` | Disable breakpoint |
| `enable` | Enable breakpoint |
| `ignore bpnum count` | Ignore breakpoint N times |
| `condition bpnum condition` | Add condition to breakpoint |

## Execution Commands

| Command | Description |
|---------|-------------|
| `run` or `restart` | Restart program |
| `quit` or `q` | Quit debugger |
| `!statement` | Execute Python statement |
| `interact` | Start interactive interpreter |

## Display and Aliases

| Command | Description |
|---------|-------------|
| `display expression` | Auto-display expression on every step |
| `undisplay` | Remove display expression |
| `alias name command` | Create command alias |
| `unalias name` | Remove alias |

## Tips

1. **Use `!` prefix**: Execute Python statements with `!x = 5`
2. **Tab completion**: Works in pdb for variable names
3. **`help` command**: Type `help` or `help command` for details
4. **Sticky mode**: Use `sticky` in pdb++ for better UI
5. **IPython integration**: Use `ipdb` for IPython features

## Advanced Usage

### Conditional Breakpoints

```python
# Break when x > 100
b 42, x > 100

# Break when condition is met
b module.function, len(data) > 1000
```

### Commands on Breakpoint

```python
# Execute commands when breakpoint hits
b 42
commands
p x
p y
c
end
```

### Remote Debugging

```python
import pdb
import sys

# Allow remote debugging
pdb.Pdb(stdin=sys.stdin, stdout=sys.stdout).set_trace()
```

## Alternative Debuggers

- **ipdb**: IPython debugger with better features
- **pudb**: Full-screen console debugger
- **web-pdb**: Web-based debugger
- **pdb++**: Enhanced pdb with syntax highlighting
