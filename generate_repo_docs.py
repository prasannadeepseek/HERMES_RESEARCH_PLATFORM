#!/usr/bin/env python3
"""
Generate repo_structure.json and docs_bundle.txt for the Hermes research platform.
"""

import os
import json
import re
import ast
from typing import Dict, List, Any, Tuple

# Directories to exclude from scanning
EXCLUDE_DIRS = {
    '.git', '__pycache__', 'node_modules', 'dist', '.claude',
    '.idea', '.vscode', 'build', 'eggs', '.eggs', 'parts', 'bin',
    'var', 'sdist', 'develop-eggs', '.installed.cfg', 'lib', 'lib64',
    '.venv', 'venv', 'env', '.env', '.qodo',  # virtual environments and IDE-specific
    'temp_repos'  # optional: exclude temp_repos if not needed
}

# File extensions we care about for code analysis
CODE_EXTENSIONS = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.java': 'java',
    '.cpp': 'cpp',
    '.c': 'c',
    '.h': 'c',
    '.cs': 'csharp',
    '.go': 'go',
    '.rb': 'ruby',
    '.php': 'php',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.rs': 'rust',
}

def should_exclude_dir(dirpath: str) -> bool:
    """Check if directory should be excluded based on its name."""
    parts = dirpath.split(os.sep)
    return any(part in EXCLUDE_DIRS for part in parts)

def get_python_classes_functions(filepath: str) -> Tuple[List[Dict], List[Dict]]:
    """Extract class and function definitions from a Python file using ast."""
    classes = []
    functions = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Get class name and methods
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                classes.append({
                    'file': filepath,
                    'name': node.name,
                    'methods': methods,
                    'line_number': node.lineno
                })
            elif isinstance(node, ast.FunctionDef):
                # Get function signature (simplified)
                # We'll reconstruct the signature from args
                args = []
                for arg in node.args.args:
                    args.append(arg.arg)
                # Handle defaults? skip for simplicity
                args_str = ', '.join(args)
                signature = f"def {node.name}({args_str}):"
                functions.append({
                    'file': filepath,
                    'name': node.name,
                    'signature': signature,
                    'line_number': node.lineno
                })
    except Exception as e:
        print(f"Warning: Could not parse {filepath}: {e}")
    return classes, functions

def get_generic_classes_functions(filepath: str, ext: str) -> Tuple[List[Dict], List[Dict]]:
    """Extract class and function signatures using regex for non-Python files."""
    classes = []
    functions = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}")
        return classes, functions

    # Regex patterns (simplistic)
    if ext in ['.js', '.ts']:
        # Class: class MyClass { ... } or class MyClass extends Base {...}
        class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:extends\s+[^{]*)?\s*\{'
        # Function: function myFunc(...) { ... } or const myFunc = (...) => {...} or myFunc(...) {...}
        # We'll capture named functions and maybe arrow functions assigned to const/let/var
        func_pattern = r'function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)'
        # Also match const/let/var arrow functions: const myFunc = (...) => {...}
        # We'll do a simpler approach: look for = (params) =>
        # But for brevity, we'll just do function keyword.
    elif ext == '.java':
        class_pattern = r'(?:public|private|protected)?\s*class\s+([A-Za-z_][A-Za-z0-9_]*)'
        func_pattern = r'(?:public|private|protected|static|\s)+[\w\<\>\[\]]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{'
    elif ext in ['.cpp', '.c', '.h']:
        class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)'
        func_pattern = r'(\w+\s+)+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{'
    elif ext == '.cs':
        class_pattern = r'(?:public|private|internal)?\s*class\s+([A-Za-z_][A-Za-z0-9_]*)'
        func_pattern = r'(?:public|private|protected|internal|static|\s)+[\w\<\>\[\]]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{'
    elif ext == '.go':
        class_pattern = r'type\s+([A-Za-z_][A-Za-z0-9_]*)\s*struct'
        func_pattern = r'func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)'
    elif ext == '.rb':
        class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)'
        func_pattern = r'def\s+([A-Za-z_][A-Za-z0-9_]*)'
    elif ext == '.php':
        class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)'
        func_pattern = r'function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)'
    elif ext == '.swift':
        class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)'
        func_pattern = r'func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)'
    elif ext == '.kt':
        class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)'
        func_pattern = r'fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)'
    elif ext == '.rs':
        class_pattern = r'struct\s+([A-Za-z_][A-Za-z0-9_]*)|enum\s+([A-Za-z_][A-Za-z0-9_]*)|trait\s+([A-Za-z_][A-Za-z0-9_]*)'
        func_pattern = r'fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)'
    else:
        # Unknown extension, skip
        return classes, functions

    # Find classes
    for match in re.finditer(class_pattern, content, re.MULTILINE):
        # For rust, we have multiple groups; adjust
        if ext == '.rs':
            # match.group(1) struct, group(2) enum, group(3) trait
            name = match.group(1) or match.group(2) or match.group(3)
        else:
            name = match.group(1)
        classes.append({
            'file': filepath,
            'name': name,
            'line_number': content[:match.start()].count('\n') + 1
        })

    # Find functions
    for match in re.finditer(func_pattern, content, re.MULTILINE):
        if ext == '.rs':
            name = match.group(1)
        else:
            # Some patterns have multiple groups; assume last captured group is the function name
            # We'll just take the last group
            groups = match.groups()
            name = groups[-1] if groups else ''
        if name:
            # Reconstruct signature approximated
            signature = match.group(0)
            functions.append({
                'file': filepath,
                'name': name,
                'signature': signature.strip(),
                'line_number': content[:match.start()].count('\n') + 1
            })

    return classes, functions

def scan_repo(root_dir: str) -> Dict[str, Any]:
    """Walk the repo and collect structure."""
    all_dirs = set()
    all_classes = []
    all_functions = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Modify dirnames in-place to skip excluded dirs
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        if should_exclude_dir(dirpath):
            # Skip this dir entirely (should already be filtered by dirnames)
            continue

        # Add directory relative to root
        rel_dir = os.path.relpath(dirpath, root_dir)
        if rel_dir != '.':
            all_dirs.add(rel_dir)

        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            ext = os.path.splitext(filename)[1].lower()

            if ext == '.py':
                classes, functions = get_python_classes_functions(filepath)
            elif ext in CODE_EXTENSIONS:
                classes, functions = get_generic_classes_functions(filepath, ext)
            else:
                # Not a code file we care about for class/function extraction
                continue

            all_classes.extend(classes)
            all_functions.extend(functions)

    # Convert sets to sorted lists for consistent output
    result = {
        'directories': sorted(list(all_dirs)),
        'classes': all_classes,
        'functions': all_functions
    }
    return result

def collect_markdown_files(root_dir: str) -> List[Tuple[str, str]]:
    """Find all .md files, return list of (rel_path, content)."""
    md_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        if should_exclude_dir(dirpath):
            continue
        for filename in filenames:
            if filename.lower().endswith('.md'):
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    rel_path = os.path.relpath(filepath, root_dir)
                    md_files.append((rel_path, content))
                except Exception as e:
                    print(f"Warning: Could not read {filepath}: {e}")
    return md_files

def collect_code_files(root_dir: str) -> List[Tuple[str, str]]:
    """Find all code files (based on CODE_EXTENSIONS), return list of (rel_path, content)."""
    code_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        if should_exclude_dir(dirpath):
            continue
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in CODE_EXTENSIONS:
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    rel_path = os.path.relpath(filepath, root_dir)
                    code_files.append((rel_path, content))
                except Exception as e:
                    print(f"Warning: Could not read {filepath}: {e}")
    return code_files

def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    print(f"Scanning repository at {repo_root}")

    # Generate repo_structure.json
    structure = scan_repo(repo_root)
    struct_path = os.path.join(repo_root, 'repo_structure.json')
    with open(struct_path, 'w', encoding='utf-8') as f:
        json.dump(structure, f, indent=2)
    print(f"Written {struct_path}")

    # Generate docs_bundle.txt
    md_files = collect_markdown_files(repo_root)
    docs_path = os.path.join(repo_root, 'docs_bundle.txt')
    with open(docs_path, 'w', encoding='utf-8') as f:
        for rel_path, content in md_files:
            f.write(f"=== {rel_path} ===\n")
            f.write(content)
            f.write("\n\n")
    print(f"Written {docs_path} with {len(md_files)} markdown files")

    # Generate consolidated_code.py (or .txt) containing all source code
    code_files = collect_code_files(repo_root)
    code_path = os.path.join(repo_root, 'consolidated_code.txt')
    with open(code_path, 'w', encoding='utf-8') as f:
        for rel_path, content in code_files:
            f.write(f"# File: {rel_path}\n")
            f.write(content)
            f.write("\n\n")
    print(f"Written {code_path} with {len(code_files)} code files")

if __name__ == '__main__':
    main()