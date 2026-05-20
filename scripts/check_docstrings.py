#!/usr/bin/env python3
"""Check that functions with meaningful params have Google-style docstring sections.

Enforced rules:
- Functions with user-facing params must have ``Args:``
- Functions with non-trivial return values must have ``Returns:``

Skipped (framework patterns):
- FastAPI params: self, cls, request, call_next, db, exc, api_key, app
- Endpoint/middleware returns (Response, JSONResponse, TemplateResponse)
- Private functions (_prefix), dunder methods (__init__ etc.)

Exit code 0 = all checks passed, 1 = violations found.
"""

import ast
import sys
from pathlib import Path

# FastAPI/framework params that don't need Args documentation
FRAMEWORK_PARAMS = frozenset({
    "self", "cls", "request", "call_next", "db", "exc",
    "api_key", "app", "args",
})

# These sections count as Google-style
SECTION_ARGS = "Args:"
SECTION_RETURNS = "Returns:"
SECTION_YIELDS = "Yields:"
SECTION_ATTRIBUTES = "Attributes:"


def has_return_value(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if function has a return statement with a value."""
    for child in ast.walk(node):
        if isinstance(child, ast.Return) and child.value is not None:
            return True
    return False


def get_meaningful_params(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Get param names excluding framework-injected params."""
    return [arg.arg for arg in node.args.args if arg.arg not in FRAMEWORK_PARAMS]


def check_file(filepath: Path) -> list[str]:
    """Check a single Python file for docstring violations.

    Args:
        filepath: Path to the Python file.

    Returns:
        List of violation messages (empty if clean).
    """
    try:
        source = filepath.read_text()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return []

    violations = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        name = node.name

        # Skip private functions (single underscore, not dunder)
        if name.startswith("_") and not name.startswith("__"):
            continue

        doc = ast.get_docstring(node)
        if doc is None:
            # ruff D rules handle missing docstrings
            continue

        meaningful_params = get_meaningful_params(node)
        has_args = SECTION_ARGS in doc
        has_returns = SECTION_RETURNS in doc or SECTION_YIELDS in doc
        has_attributes = SECTION_ATTRIBUTES in doc
        returns_value = has_return_value(node)

        loc = f"{filepath.relative_to(Path('src/phi_gateway'))}:{node.lineno} {name}()"

        # Rule 1: Functions with meaningful params need Args: or Attributes:
        if meaningful_params and not has_args and not has_attributes:
            if name == "__init__":
                continue  # class Attributes: covers __init__ params
            violations.append(f"  {loc} — params {meaningful_params} missing Args:")

        # Rule 2: Functions with return values need Returns:
        # Only enforce if the function already has Args: (business logic).
        # Framework handlers (endpoints, middleware) skip naturally because
        # they have no Args: section.
        if returns_value and has_args and not has_returns and not has_attributes:
            violations.append(f"  {loc} — has Args: but missing Returns:")

    return violations


def main() -> None:
    """Run docstring checks on all source files."""
    src_dir = Path("src/phi_gateway")
    if not src_dir.exists():
        print(f"ERROR: {src_dir} not found. Run from project root.", file=sys.stderr)
        sys.exit(1)

    all_violations = []
    files_checked = 0

    for filepath in sorted(src_dir.rglob("*.py")):
        files_checked += 1
        violations = check_file(filepath)
        all_violations.extend(violations)

    if all_violations:
        print(f"Google-style docstring violations ({len(all_violations)}):")
        for v in all_violations:
            print(v)
        print(f"\nChecked {files_checked} files. Add Args:/Returns: sections to fix.")
        sys.exit(1)
    else:
        print(f"All {files_checked} files passed Google-style docstring checks.")
        sys.exit(0)


if __name__ == "__main__":
    main()
