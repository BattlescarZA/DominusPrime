#!/usr/bin/env python3
"""
Replace user-facing "CoPaw" and "copaw" references with "DominusPrime" and "dominusprime".
Preserves external library class names like CoPawInMemoryMemory, ReMeCopaw.
"""

import re
from pathlib import Path

# Patterns to replace (user-facing only)
REPLACEMENTS = [
    # Command examples in help text
    (r'\bcopaw\s+(chats|channels|models|init|app|daemon|clean|uninstall|skills)', r'dominusprime \1'),
    
    # Descriptive text about CoPaw
    (r'\bCoPaw\s+is\s+a\s+', r'DominusPrime is a '),
    (r'\bCoPaw\s+instance\b', r'DominusPrime instance'),
    (r'\bCoPaw\s+environment\b', r'DominusPrime environment'),
    (r'\bCoPaw\s+data\b', r'DominusPrime data'),
    (r'\bCoPaw\s+version\b', r'DominusPrime version'),
    (r'\bCoPaw\s+Python\s+environment\b', r'DominusPrime Python environment'),
    (r'\bCoPaw\s+CLI\s+wrapper\b', r'DominusPrime CLI wrapper'),
    (r'\bCoPaw\s+PATH\s+', r'DominusPrime PATH '),
    (r'\bCoPaw\s+WORKING_DIR\b', r'DominusPrime WORKING_DIR'),
    (r'runs\s+CoPaw\b', r'runs DominusPrime'),
    (r'run\s+CoPaw\b', r'run DominusPrime'),
    (r'Remove\s+CoPaw\b', r'Remove DominusPrime'),
    (r'remove\s+the\s+CoPaw\b', r'remove the DominusPrime'),
    (r'Clear\s+CoPaw\b', r'Clear DominusPrime'),
    
    # Comments with user-facing "copaw"
    (r'# CoPaw\n', r'# DominusPrime\n'),
    (r'copaw-skills-hub', r'dominusprime-skills-hub'),
    
    # Fix console comment (but not the package path)
    (r'console will be output to copaw\'s', r'console will be output to dominusprime\'s'),
    (r'shipped dist lives in copaw package', r'shipped dist lives in dominusprime package'),
    (r'# Shipped dist lives in copaw package', r'# Shipped dist lives in dominusprime package'),
]

# Files to skip (contain only import statements or library references)
SKIP_FILES = {
    'rebrand_selective.py',
    'rebrand_user_facing.py',
}

# Preserve these exact patterns (external library classes)
PRESERVE_PATTERNS = [
    r'CoPawInMemoryMemory',
    r'ReMeCopaw',
    r'file_based_copaw',
    r'reme_copaw',
]

def should_skip_line(line: str) -> bool:
    """Check if line contains preserved patterns."""
    for pattern in PRESERVE_PATTERNS:
        if pattern in line:
            return True
    return False

def process_file(filepath: Path) -> tuple[int, list[str]]:
    """Process a single file and return (replacements_made, changed_lines)."""
    try:
        content = filepath.read_text(encoding='utf-8')
        original = content
        lines_changed = []
        
        # Process line by line to preserve library references
        lines = content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines, 1):
            new_line = line
            
            # Skip lines with preserved patterns
            if should_skip_line(line):
                new_lines.append(new_line)
                continue
            
            # Apply replacements
            for pattern, replacement in REPLACEMENTS:
                if re.search(pattern, new_line):
                    before = new_line
                    new_line = re.sub(pattern, replacement, new_line)
                    if before != new_line:
                        lines_changed.append(f"  Line {i}: {pattern} -> {replacement}")
            
            new_lines.append(new_line)
        
        content = '\n'.join(new_lines)
        
        if content != original:
            filepath.write_text(content, encoding='utf-8')
            return len(lines_changed), lines_changed
        
        return 0, []
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return 0, []

def main():
    """Process all Python files in src/dominusprime."""
    src_dir = Path('src/dominusprime')
    
    if not src_dir.exists():
        print(f"Error: {src_dir} not found")
        return
    
    total_files_changed = 0
    total_replacements = 0
    
    print("Replacing user-facing CoPaw/copaw references...")
    print("=" * 60)
    
    for py_file in src_dir.rglob('*.py'):
        if py_file.name in SKIP_FILES:
            continue
        
        count, changes = process_file(py_file)
        if count > 0:
            total_files_changed += 1
            total_replacements += count
            print(f"\n{py_file.relative_to('src/dominusprime')}:")
            for change in changes:
                print(change)
    
    print("\n" + "=" * 60)
    print(f"Summary: {total_replacements} replacements in {total_files_changed} files")
    print("\nPreserved library references:")
    for pattern in PRESERVE_PATTERNS:
        print(f"  - {pattern}")

if __name__ == '__main__':
    main()
