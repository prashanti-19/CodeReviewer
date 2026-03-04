import os
import sys
import uuid
import json
import subprocess
import tempfile
import shutil
import logging
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Code Quality Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs = {}

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
    ".rb", ".php", ".cs", ".cpp", ".c", ".h", ".html",
    ".css", ".scss", ".json", ".yaml", ".yml", ".sh"
}


def extract_snippet(filepath: str, line_start: int, line_end: int, context: int = 2) -> str:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        start = max(0, line_start - context - 1)
        end = min(len(lines), line_end + context)
        return "".join(lines[start:end])
    except Exception:
        return ""


def write_semgrep_rules(rules_dir: str):
    """Write built-in rules to a local folder — no internet needed."""

    rules = [
        {
            "id": "hardcoded-password",
            "pattern": '$X = "$Y"',
            "message": "Possible hardcoded credential. Avoid storing passwords or secrets directly in source code.",
            "severity": "ERROR",
            "category": "security",
            "languages": ["python", "javascript", "typescript"],
            "filter_regex": r"(?i)(password|passwd|secret|api_key|apikey|token|auth|credential|private_key)",
        },
        {
            "id": "sql-injection",
            "pattern": "... + $X + ...",
            "message": "Possible SQL injection via string concatenation. Use parameterized queries instead.",
            "severity": "ERROR",
            "category": "security",
            "languages": ["python", "javascript"],
            "filter_regex": r"(?i)(select|insert|update|delete|where|from)\s",
        },
        {
            "id": "eval-usage",
            "pattern": "eval($X)",
            "message": "Use of eval() is dangerous and can lead to code injection vulnerabilities.",
            "severity": "ERROR",
            "category": "security",
            "languages": ["python", "javascript", "typescript"],
        },
        {
            "id": "os-system-injection",
            "pattern": "os.system($X)",
            "message": "os.system() with dynamic input can lead to command injection. Use subprocess with a list of arguments instead.",
            "severity": "ERROR",
            "category": "security",
            "languages": ["python"],
        },
        {
            "id": "subprocess-shell-true",
            "pattern": "subprocess.call($X, shell=True)",
            "message": "subprocess with shell=True is vulnerable to shell injection. Pass arguments as a list instead.",
            "severity": "ERROR",
            "category": "security",
            "languages": ["python"],
        },
        {
            "id": "innerHTML-xss",
            "pattern": "$X.innerHTML = $Y",
            "message": "Assigning to innerHTML with dynamic content can lead to XSS vulnerabilities. Use textContent or sanitize input.",
            "severity": "ERROR",
            "category": "security",
            "languages": ["javascript", "typescript"],
        },
        {
            "id": "console-log-leak",
            "pattern": "console.log($X)",
            "message": "console.log() left in production code can leak sensitive information. Remove before deploying.",
            "severity": "WARNING",
            "category": "code-smell",
            "languages": ["javascript", "typescript"],
        },
        {
            "id": "print-statement",
            "pattern": "print($X)",
            "message": "print() statements should be replaced with proper logging in production code.",
            "severity": "WARNING",
            "category": "code-smell",
            "languages": ["python"],
        },
        {
            "id": "bare-except",
            "pattern": "try:\n    ...\nexcept:\n    ...",
            "message": "Bare except clause catches all exceptions including system exits. Catch specific exceptions instead.",
            "severity": "WARNING",
            "category": "maintainability",
            "languages": ["python"],
        },
        {
            "id": "open-without-context",
            "pattern": "$F = open($X)",
            "message": "File opened without a context manager. Use 'with open(...)' to ensure the file is properly closed.",
            "severity": "WARNING",
            "category": "maintainability",
            "languages": ["python"],
        },
    ]

    # Write as individual YAML rule files
    for rule in rules:
        langs = rule.get("languages", ["python"])
        lang_str = "\n    - ".join(langs)
        category = rule.get("category", "code-smell")

        yaml_content = f"""rules:
  - id: {rule['id']}
    pattern: |
      {rule['pattern']}
    message: "{rule['message']}"
    severity: {rule['severity']}
    languages:
      - {lang_str}
    metadata:
      category: {category}
"""
        rule_file = os.path.join(rules_dir, f"{rule['id']}.yaml")
        with open(rule_file, "w") as f:
            f.write(yaml_content)


def run_analysis(file_paths: list, base_dir: str) -> list:
    """Run analysis using local built-in rules."""
    findings = []

    # Write rules to a temp folder
    rules_dir = os.path.join(base_dir, "_rules")
    os.makedirs(rules_dir, exist_ok=True)
    write_semgrep_rules(rules_dir)

    semgrep_cmd = [sys.executable, "-m", "semgrep"]

    try:
        cmd = semgrep_cmd + [
            f"--config={rules_dir}",
            "--json",
            "--no-git-ignore",
            "--quiet",
        ] + file_paths

        logger.info(f"Running semgrep with local rules on {len(file_paths)} files")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            cwd=base_dir,
        )

        logger.info(f"Semgrep stdout length: {len(result.stdout)}")
        if result.stderr:
            logger.warning(f"Semgrep stderr: {result.stderr[:300]}")

        # Run per-file analysis
        for fp in file_paths:
            ext = os.path.splitext(fp)[1].lower()
            logger.info(f"Analyzing file: {fp} (ext: {ext})")
            if ext == ".py":
                py_findings = analyze_python_ast(fp, base_dir)
                logger.info(f"  Python findings: {len(py_findings)}")
                findings.extend(py_findings)
            elif ext in (".js", ".ts", ".jsx", ".tsx"):
                js_findings = analyze_js_patterns(fp, base_dir)
                logger.info(f"  JS findings: {len(js_findings)}")
                findings.extend(js_findings)
            elif ext in (".cpp", ".c", ".h", ".cc", ".cxx"):
                cpp_findings = analyze_cpp_patterns(fp, base_dir)
                logger.info(f"  C/C++ findings: {len(cpp_findings)}")
                findings.extend(cpp_findings)
            elif ext in (".java",):
                java_findings = analyze_java_patterns(fp, base_dir)
                logger.info(f"  Java findings: {len(java_findings)}")
                findings.extend(java_findings)

        if result.stdout.strip():
            raw = json.loads(result.stdout)
            results = raw.get("results", [])
            logger.info(f"Semgrep found {len(results)} results")

            for r in results:
                check_id = r.get("check_id", "")
                meta = r.get("extra", {}).get("metadata", {})
                severity_raw = r.get("extra", {}).get("severity", "WARNING").upper()
                severity_map = {"ERROR": "critical", "WARNING": "high", "INFO": "medium", "NOTE": "low"}
                severity = severity_map.get(severity_raw, "medium")

                category = meta.get("category", "code-smell")

                filepath = r.get("path", "")
                line_start = r.get("start", {}).get("line", 1)
                line_end = r.get("end", {}).get("line", line_start)
                snippet = r.get("extra", {}).get("lines", "") or extract_snippet(filepath, line_start, line_end)
                rel_path = os.path.relpath(filepath, base_dir) if filepath else filepath
                rule_name = check_id.split(".")[-1].replace("-", " ").replace("_", " ").title()

                findings.append({
                    "id": str(uuid.uuid4()),
                    "file": rel_path,
                    "line_start": line_start,
                    "line_end": line_end,
                    "category": category,
                    "severity": severity,
                    "rule": check_id,
                    "title": rule_name,
                    "description": r.get("extra", {}).get("message", "No description available."),
                    "snippet": snippet,
                })

    except subprocess.TimeoutExpired:
        logger.warning("Semgrep timed out")
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error: {e}")
    except Exception as e:
        logger.error(f"Semgrep error: {e}")

    logger.info(f"Total findings: {len(findings)}")
    return findings


def analyze_python_ast(filepath: str, base_dir: str) -> list:
    """Pure Python analysis using AST — no external tools needed."""
    import ast
    import re
    findings = []

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
            lines = source.splitlines()

        rel_path = os.path.relpath(filepath, base_dir)

        # Check for hardcoded secrets via regex
        secret_patterns = [
            (r'(?i)(password|passwd|secret|api_key|apikey|token|auth_key|private_key)\s*=\s*["\']{1}[^"\']{4,}["\']{1}', "Hardcoded Secret", "Sensitive value hardcoded in source. Move to environment variables.", "security", "critical"),
            (r'eval\s*\(', "Dangerous eval()", "eval() executes arbitrary code and is a security risk.", "security", "critical"),
            (r'["\'](\s*)(SELECT|INSERT|UPDATE|DELETE|WHERE|FROM).{0,60}["\'](\s*)\+|\+(\s*)["\']{1}.{0,20}(SELECT|INSERT|UPDATE|DELETE|WHERE)', "SQL Injection", "SQL query built by string concatenation. An attacker can inject arbitrary SQL. Use parameterized queries (cursor.execute(query, params)) instead.", "security", "critical"),
            (r'hashlib\.md5\s*\(', "Weak Hashing (MD5)", "MD5 is cryptographically broken and easily cracked with rainbow tables. For passwords use bcrypt or argon2. For checksums use SHA-256.", "security", "high"),
            (r'hashlib\.sha1\s*\(', "Weak Hashing (SHA1)", "SHA1 is considered weak for security. Use SHA-256 or stronger, or bcrypt/argon2 for passwords.", "security", "high"),
            (r'os\.system\s*\(', "OS Command Execution", "os.system() with dynamic input can allow command injection. Use subprocess with a list of arguments instead.", "security", "high"),
            (r'shell\s*=\s*True', "Shell Injection Risk", "subprocess with shell=True is vulnerable to shell injection. Pass arguments as a list.", "security", "high"),
            (r'self\.\w*(?:db|conn|connection|cursor)\s*=\s*\w+\.connect\(', "Unclosed Resource in __init__", "Database/resource connection opened in __init__ but likely never explicitly closed. Implement a close() method or use a context manager to prevent resource leaks.", "maintainability", "high"),
            (r'except\s*:', "Bare Except Clause", "Bare except catches all exceptions including SystemExit. Specify the exception type.", "maintainability", "medium"),
            (r'(?<!with )(?<!with\t)\bopen\s*\(', "File Not Closed Safely", "File opened without context manager. Use 'with open(...)' to ensure it is properly closed.", "maintainability", "medium"),
            (r'sqlite3\.connect\s*\(["\']{1}[^\"]+["\']{1}\)', "Hardcoded Database Path", "Database path is hardcoded. Use an environment variable (os.environ.get) so you can switch between test and production databases.", "maintainability", "medium"),
            (r'\bprint\s*\(', "Print Statement", "Remove print() statements before production. Use the logging module instead.", "code-smell", "low"),
            (r'#\s*(TODO|FIXME|HACK|XXX)', "Unresolved TODO/FIXME", "Unresolved TODO or FIXME comment found. Address before shipping.", "maintainability", "low"),
            (r'(?<!\w)([3-9][0-9]+)(?!\w)', "Magic Number", "Magic number found. Consider using a named constant for clarity.", "readability", "low"),
            (r'\w+\[\s*[2-9]\s*\]', "Magic Index Access", "Accessing a sequence by a raw numeric index like [2] or [4] is unclear. Use a named variable, dictionary, or namedtuple to make the intent obvious.", "readability", "medium"),
        ]

        for pattern, title, description, category, severity in secret_patterns:
            for i, line in enumerate(lines, 1):
                # Skip comment lines
                stripped = line.strip()
                if stripped.startswith('#'):
                    continue
                if re.search(pattern, line):
                    findings.append({
                        "id": str(uuid.uuid4()),
                        "file": rel_path,
                        "line_start": i,
                        "line_end": i,
                        "category": category,
                        "severity": severity,
                        "rule": f"custom.{title.lower().replace(' ', '-')}",
                        "title": title,
                        "description": description,
                        "snippet": extract_snippet(filepath, i, i),
                    })

        # AST-based checks
        try:
            tree = ast.parse(source)

            # Collect function bodies for duplicate detection
            func_bodies = {}

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_lines = (node.end_lineno or node.lineno) - node.lineno

                    # Long functions
                    if func_lines > 30:
                        findings.append({
                            "id": str(uuid.uuid4()),
                            "file": rel_path,
                            "line_start": node.lineno,
                            "line_end": node.end_lineno or node.lineno,
                            "category": "maintainability",
                            "severity": "medium",
                            "rule": "custom.long-function",
                            "title": "Long Function",
                            "description": f"Function '{node.name}' is {func_lines} lines long. Consider breaking it into smaller functions.",
                            "snippet": extract_snippet(filepath, node.lineno, node.lineno + 3),
                        })

                    # Too many arguments
                    if len(node.args.args) > 5:
                        findings.append({
                            "id": str(uuid.uuid4()),
                            "file": rel_path,
                            "line_start": node.lineno,
                            "line_end": node.lineno,
                            "category": "readability",
                            "severity": "medium",
                            "rule": "custom.too-many-arguments",
                            "title": "Too Many Arguments",
                            "description": f"Function '{node.name}' has {len(node.args.args)} parameters. Consider using a config object or breaking it up.",
                            "snippet": extract_snippet(filepath, node.lineno, node.lineno),
                        })

                    # Async function with no try/except (no error handling)
                    if isinstance(node, ast.AsyncFunctionDef):
                        has_try = any(isinstance(n, ast.Try) for n in ast.walk(node))
                        if not has_try:
                            findings.append({
                                "id": str(uuid.uuid4()),
                                "file": rel_path,
                                "line_start": node.lineno,
                                "line_end": node.end_lineno or node.lineno,
                                "category": "maintainability",
                                "severity": "medium",
                                "rule": "custom.async-no-error-handling",
                                "title": "Async Function Without Error Handling",
                                "description": f"Async function '{node.name}' has no try/except block. Unhandled promise rejections can crash your application.",
                                "snippet": extract_snippet(filepath, node.lineno, node.lineno + 3),
                            })

                    # Naming convention checks (PEP 8)
                    if isinstance(node, ast.FunctionDef):
                        # Function names should be snake_case
                        if re.search(r'[A-Z]', node.name) and not node.name.startswith('__'):
                            findings.append({
                                "id": str(uuid.uuid4()),
                                "file": rel_path,
                                "line_start": node.lineno,
                                "line_end": node.lineno,
                                "category": "readability",
                                "severity": "low",
                                "rule": "custom.naming-convention",
                                "title": "Non-Standard Function Name",
                                "description": f"Function '{node.name}' uses PascalCase or camelCase. PEP 8 recommends snake_case for function names (e.g. '{re.sub(r'(?<!^)(?=[A-Z])', '_', node.name).lower()}').",
                                "snippet": extract_snippet(filepath, node.lineno, node.lineno),
                            })

                    # Class names should be PascalCase
                    if isinstance(node, ast.ClassDef):
                        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                            findings.append({
                                "id": str(uuid.uuid4()),
                                "file": rel_path,
                                "line_start": node.lineno,
                                "line_end": node.lineno,
                                "category": "readability",
                                "severity": "low",
                                "rule": "custom.class-naming-convention",
                                "title": "Non-Standard Class Name",
                                "description": f"Class '{node.name}' does not follow PEP 8. Class names should use PascalCase (e.g. '{node.name.replace('_', ' ').title().replace(' ', '')}').",
                                "snippet": extract_snippet(filepath, node.lineno, node.lineno),
                            })

                    # Duplicate function body detection
                    body_src = ast.dump(ast.Module(body=node.body, type_ignores=[]))
                    if body_src in func_bodies:
                        prev_name, prev_line = func_bodies[body_src]
                        findings.append({
                            "id": str(uuid.uuid4()),
                            "file": rel_path,
                            "line_start": node.lineno,
                            "line_end": node.end_lineno or node.lineno,
                            "category": "code-smell",
                            "severity": "medium",
                            "rule": "custom.duplicate-function",
                            "title": "Duplicate Function Body",
                            "description": f"Function '{node.name}' has the same body as '{prev_name}' (line {prev_line}). Extract into a shared function.",
                            "snippet": extract_snippet(filepath, node.lineno, node.lineno + 4),
                        })
                    else:
                        func_bodies[body_src] = (node.name, node.lineno)

                    # Unused variables (simple check: assigned but never used in function)
                    assigned = {}
                    used_names = set()
                    for n in ast.walk(node):
                        if isinstance(n, ast.Assign):
                            for t in n.targets:
                                if isinstance(t, ast.Name):
                                    assigned[t.id] = n.lineno
                        elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                            used_names.add(n.id)
                    for var_name, var_line in assigned.items():
                        if var_name not in used_names and not var_name.startswith('_'):
                            findings.append({
                                "id": str(uuid.uuid4()),
                                "file": rel_path,
                                "line_start": var_line,
                                "line_end": var_line,
                                "category": "code-smell",
                                "severity": "low",
                                "rule": "custom.unused-variable",
                                "title": "Unused Variable",
                                "description": f"Variable '{var_name}' is assigned but never used. Remove it to improve clarity.",
                                "snippet": extract_snippet(filepath, var_line, var_line),
                            })

                # Deep nesting detection (if inside if inside if...)
                if isinstance(node, ast.If):
                    depth = 0
                    parent = node
                    for n in ast.walk(tree):
                        if isinstance(n, ast.If) and n is node:
                            # count nesting by checking body contains another if
                            inner = node
                            d = 0
                            while inner and isinstance(inner, ast.If):
                                d += 1
                                inner_ifs = [x for x in inner.body if isinstance(x, ast.If)]
                                inner = inner_ifs[0] if inner_ifs else None
                            if d >= 4:
                                findings.append({
                                    "id": str(uuid.uuid4()),
                                    "file": rel_path,
                                    "line_start": node.lineno,
                                    "line_end": node.end_lineno or node.lineno,
                                    "category": "readability",
                                    "severity": "medium",
                                    "rule": "custom.deep-nesting",
                                    "title": "Deeply Nested Code",
                                    "description": f"Code is nested {d} levels deep starting at line {node.lineno}. Refactor using early returns or helper functions.",
                                    "snippet": extract_snippet(filepath, node.lineno, node.lineno + 4),
                                })
                            break


            # ── Taint Analysis: user input → dangerous sinks ──────────────────
            # Track which names are "tainted" (sourced from user input)
            tainted_names = set()
            taint_sources = {
                # request sources
                "request", "req",
                # input() calls tracked below
            }

            # First pass: find all tainted assignments
            for n in ast.walk(tree):
                if isinstance(n, ast.Assign):
                    # Check if value comes from request.* or input()
                    val_src = ast.dump(n.value)
                    is_tainted = (
                        "request" in val_src or "req" in val_src
                        or "input()" in val_src
                        or any(t in val_src for t in ["args", "form", "json", "params", "body", "query"])
                    )
                    if is_tainted:
                        for t in n.targets:
                            if isinstance(t, ast.Name):
                                tainted_names.add(t.id)

            # Second pass: check if tainted names flow into SQL sinks
            for n in ast.walk(tree):
                if isinstance(n, ast.Call):
                    call_src = ast.dump(n)
                    # SQL sink: .execute() called with tainted variable in string concat
                    if "execute" in call_src:
                        for arg in n.args:
                            arg_src = ast.dump(arg)
                            if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                                # Check if any tainted name is in the concat
                                names_in_arg = {node.id for node in ast.walk(arg) if isinstance(node, ast.Name)}
                                if names_in_arg & tainted_names:
                                    findings.append({
                                        "id": str(uuid.uuid4()),
                                        "file": rel_path,
                                        "line_start": n.lineno,
                                        "line_end": n.lineno,
                                        "category": "security",
                                        "severity": "critical",
                                        "rule": "custom.taint-sql-injection",
                                        "title": "Taint: SQL Injection via User Input",
                                        "description": f"User-controlled data flows directly into a SQL execute() call via string concatenation. An attacker can manipulate the query. Use parameterized queries: cursor.execute(query, (param,)).",
                                        "snippet": extract_snippet(filepath, n.lineno, n.lineno),
                                    })

            # ── Security checks ───────────────────────────────────────────────

            # pickle.loads (insecure deserialization)
            for n in ast.walk(tree):
                if isinstance(n, ast.Call):
                    call_str = ast.dump(n)
                    if "pickle" in call_str and "loads" in call_str:
                        findings.append({
                            "id": str(uuid.uuid4()),
                            "file": rel_path,
                            "line_start": n.lineno,
                            "line_end": n.lineno,
                            "category": "security",
                            "severity": "critical",
                            "rule": "custom.insecure-deserialization",
                            "title": "Insecure Deserialization (pickle)",
                            "description": "pickle.loads() can execute arbitrary code if given untrusted data. Never deserialize data from untrusted sources with pickle. Use JSON or another safe format.",
                            "snippet": extract_snippet(filepath, n.lineno, n.lineno),
                        })

            # Hardcoded IPs and local paths
            for i_line, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if re.search(r'["\'](\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})["\']', line) and not re.search(r'127\.0\.0\.1|0\.0\.0\.0', line):
                    findings.append({
                        "id": str(uuid.uuid4()),
                        "file": rel_path, "line_start": i_line, "line_end": i_line,
                        "category": "maintainability", "severity": "medium",
                        "rule": "custom.hardcoded-ip",
                        "title": "Hardcoded IP Address",
                        "description": "IP address hardcoded in source. Use environment variables or config files so the address can change between environments.",
                        "snippet": extract_snippet(filepath, i_line, i_line),
                    })
                if re.search(r'["\'](C:\\\\|/home/|/usr/local/|/var/www)', line):
                    findings.append({
                        "id": str(uuid.uuid4()),
                        "file": rel_path, "line_start": i_line, "line_end": i_line,
                        "category": "maintainability", "severity": "medium",
                        "rule": "custom.hardcoded-path",
                        "title": "Hardcoded File Path",
                        "description": "Absolute file path hardcoded in source. This breaks portability across machines and environments. Use relative paths or environment variables.",
                        "snippet": extract_snippet(filepath, i_line, i_line),
                    })

            # ── Performance / Resource checks ─────────────────────────────────

            # N+1 Query: DB call inside a loop
            for n in ast.walk(tree):
                if isinstance(n, (ast.For, ast.While)):
                    for inner in ast.walk(n):
                        if isinstance(inner, ast.Call) and inner is not n:
                            inner_str = ast.dump(inner)
                            if any(k in inner_str.lower() for k in ["execute", "query", "fetchone", "fetchall", "filter", "get_by", "find_by", "select"]):
                                findings.append({
                                    "id": str(uuid.uuid4()),
                                    "file": rel_path,
                                    "line_start": inner.lineno,
                                    "line_end": inner.lineno,
                                    "category": "maintainability",
                                    "severity": "high",
                                    "rule": "custom.n-plus-one-query",
                                    "title": "N+1 Query Problem",
                                    "description": "Database query detected inside a loop. For N items this executes N queries, which can be catastrophically slow. Use bulk queries, joins, or prefetch_related() instead.",
                                    "snippet": extract_snippet(filepath, inner.lineno, inner.lineno),
                                })
                                break

            # Unbounded recursion: function calls itself without obvious base case
            for n in ast.walk(tree):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self_calls = [
                        c for c in ast.walk(n)
                        if isinstance(c, ast.Call)
                        and isinstance(getattr(c, "func", None), ast.Name)
                        and c.func.id == n.name
                    ]
                    if self_calls:
                        # Check for a return/if guard near the top
                        has_base_case = any(
                            isinstance(b, (ast.Return, ast.If))
                            for b in n.body[:3]
                        )
                        if not has_base_case:
                            findings.append({
                                "id": str(uuid.uuid4()),
                                "file": rel_path,
                                "line_start": n.lineno,
                                "line_end": n.lineno,
                                "category": "maintainability",
                                "severity": "high",
                                "rule": "custom.unbounded-recursion",
                                "title": "Potential Unbounded Recursion",
                                "description": f"Function '{n.name}' calls itself recursively but has no obvious base case at the start. Without a termination condition this will cause a stack overflow.",
                                "snippet": extract_snippet(filepath, n.lineno, n.lineno + 4),
                            })

            # Global variable mutation (thread safety risk)
            for n in ast.walk(tree):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for inner in ast.walk(n):
                        if isinstance(inner, ast.Global):
                            findings.append({
                                "id": str(uuid.uuid4()),
                                "file": rel_path,
                                "line_start": inner.lineno,
                                "line_end": inner.lineno,
                                "category": "maintainability",
                                "severity": "medium",
                                "rule": "custom.global-mutation",
                                "title": "Global Variable Mutation",
                                "description": f"Function '{n.name}' modifies a global variable ({", ".join(inner.names)}). This is not thread-safe and makes code hard to test. Use function parameters and return values instead.",
                                "snippet": extract_snippet(filepath, inner.lineno, inner.lineno),
                            })

            # ── Logic & Reliability checks ────────────────────────────────────

            # Float comparison with ==
            for n in ast.walk(tree):
                if isinstance(n, ast.Compare):
                    for op in n.ops:
                        if isinstance(op, ast.Eq):
                            # Check if either side looks like a float
                            all_nodes = [n.left] + n.comparators
                            for comp_node in all_nodes:
                                if isinstance(comp_node, ast.Constant) and isinstance(comp_node.value, float):
                                    findings.append({
                                        "id": str(uuid.uuid4()),
                                        "file": rel_path,
                                        "line_start": n.lineno,
                                        "line_end": n.lineno,
                                        "category": "maintainability",
                                        "severity": "medium",
                                        "rule": "custom.float-equality",
                                        "title": "Float Equality Comparison",
                                        "description": "Comparing floats with == is unreliable due to floating-point precision issues. Use abs(a - b) < epsilon or math.isclose(a, b) instead.",
                                        "snippet": extract_snippet(filepath, n.lineno, n.lineno),
                                    })

            # God function: cognitive complexity (count branches)
            for n in ast.walk(tree):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    branch_count = sum(
                        1 for node in ast.walk(n)
                        if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                                             ast.With, ast.Assert, ast.comprehension))
                    )
                    if branch_count >= 10:
                        findings.append({
                            "id": str(uuid.uuid4()),
                            "file": rel_path,
                            "line_start": n.lineno,
                            "line_end": n.end_lineno or n.lineno,
                            "category": "maintainability",
                            "severity": "high",
                            "rule": "custom.god-function",
                            "title": "God Function (High Cognitive Complexity)",
                            "description": f"Function '{n.name}' has {branch_count} branches/loops (complexity score: {branch_count}). Functions this complex are hard to test and maintain. Break it into smaller, focused functions.",
                            "snippet": extract_snippet(filepath, n.lineno, n.lineno + 3),
                        })

            # Insecure cookie setting
            for i_line, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if re.search(r'set_cookie\s*\(', line) or re.search(r'response\.set_cookie', line):
                    if "httponly" not in line.lower() and "http_only" not in line.lower():
                        findings.append({
                            "id": str(uuid.uuid4()),
                            "file": rel_path, "line_start": i_line, "line_end": i_line,
                            "category": "security", "severity": "high",
                            "rule": "custom.insecure-cookie-httponly",
                            "title": "Cookie Missing HttpOnly Flag",
                            "description": "Cookie set without HttpOnly flag. This allows JavaScript to read the cookie, enabling session theft via XSS. Add httponly=True.",
                            "snippet": extract_snippet(filepath, i_line, i_line),
                        })
                    if "secure" not in line.lower():
                        findings.append({
                            "id": str(uuid.uuid4()),
                            "file": rel_path, "line_start": i_line, "line_end": i_line,
                            "category": "security", "severity": "medium",
                            "rule": "custom.insecure-cookie-secure",
                            "title": "Cookie Missing Secure Flag",
                            "description": "Cookie set without Secure flag. This allows the cookie to be transmitted over HTTP (unencrypted). Add secure=True.",
                            "snippet": extract_snippet(filepath, i_line, i_line),
                        })

            # Mass assignment: passing request data directly to model
            for i_line, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if re.search(r'\w+\.(?:update|create|save)\s*\(\s*(?:request|req)\.(?:data|body|POST|json|form)\s*\)', line):
                    findings.append({
                        "id": str(uuid.uuid4()),
                        "file": rel_path, "line_start": i_line, "line_end": i_line,
                        "category": "security", "severity": "high",
                        "rule": "custom.mass-assignment",
                        "title": "Mass Assignment Vulnerability",
                        "description": "User request data passed directly to a model update/create. An attacker can set any field including isAdmin or role. Use an explicit allowlist of permitted fields.",
                        "snippet": extract_snippet(filepath, i_line, i_line),
                    })

        except SyntaxError:
            pass

    except Exception as e:
        logger.error(f"AST analysis error for {filepath}: {e}")

    return findings


def analyze_js_patterns(filepath: str, base_dir: str) -> list:
    """Regex-based JS/TS analysis."""
    import re
    findings = []

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        rel_path = os.path.relpath(filepath, base_dir)

        patterns = [
            # Secrets & credentials
            (r'(?i)(password|api_key|apikey|secret|token|auth|private_key|admin_key)\s*[=:]\s*["\']{1}[^\"\'{]{4,}["\']{1}', "Hardcoded Secret", "Sensitive credential hardcoded in source code. If committed to Git, it becomes public. Move to environment variables (process.env.MY_KEY).", "security", "critical"),

            # Dangerous execution
            (r'\beval\s*\(', "Dangerous eval()", "eval() executes arbitrary strings as code. If any user input reaches this, attackers can run any code on your server.", "security", "critical"),
            (r'(?:exec|execSync|spawn|spawnSync)\s*\([^)]*(?:req\.|request\.|query\.|params\.|body\.|user)', "Command Injection", "Shell command built from user input (req.query/body/params). An attacker can append shell commands like '; rm -rf /' to execute arbitrary commands on the server.", "security", "critical"),
            (r'(?:exec|execSync|spawn|spawnSync)\s*\([^)]*\+', "Potential Command Injection", "Shell command built with string concatenation. If any concatenated variable comes from user input, this is a command injection vulnerability.", "security", "critical"),

            # Path traversal
            (r'(?:writeFile|readFile|createReadStream|createWriteStream|appendFile|unlink)\w*\s*\([^)]*(?:req\.|request\.|query\.|params\.|body\.|user)', "Path Traversal via User Input", "File path built from user input. An attacker can use '../../../etc/passwd' to read or overwrite sensitive system files. Always sanitize and validate file paths.", "security", "high"),
            (r'(?:writeFile|readFile|readFileSync|writeFileSync)\w*\s*\([^)]*\+', "Potential Path Traversal", "File path built with string concatenation. If any part comes from user input, attackers can traverse directories and access sensitive files.", "security", "high"),

            # Arbitrary file write
            (r'(?:writeFile|writeFileSync)\s*\([^)]*(?:req\.|body\.|params\.|query\.)', "Arbitrary File Write", "Writing file content directly from user input without validation. An attacker could write a malicious script (.js, .sh) to a web-accessible folder and execute it.", "security", "high"),

            # XSS
            (r'\.innerHTML\s*=', "XSS via innerHTML", "Setting innerHTML with dynamic content allows XSS attacks. Use textContent, or sanitize with DOMPurify before assigning.", "security", "high"),

            # SQL injection
            (r'(?i)(SELECT|INSERT|UPDATE|DELETE).{0,50}(\+\s*\w|\w\s*\+)', "SQL Injection Risk", "SQL query built with string concatenation. Use parameterized queries or a query builder.", "security", "high"),

            # Unsafe equality
            (r'\b==\s*(?!==)', "Loose Equality (==)", "Using == instead of === performs type coercion which can cause unexpected behavior. Use strict equality === instead.", "code-smell", "low"),

            # Blocking I/O in async context
            (r'(?:readFileSync|writeFileSync|execSync|appendFileSync)\s*\(', "Blocking Synchronous I/O", "Synchronous file/exec operations block the entire Node.js event loop. No other requests can be handled until this completes. Use the async versions (readFile, writeFile) with callbacks or async/await.", "code-smell", "high"),

            # Response with raw stdout (XSS risk)
            (r'res\.send\s*\([^)]*stdout', "Unescaped Command Output in Response", "Sending raw command output (stdout) directly in an HTTP response. This can expose sensitive server info and is an XSS vector if rendered as HTML.", "security", "high"),

            # General issues
            (r'\bconsole\.(log|warn|error|debug)\s*\(', "Console Statement Left In", "Remove console statements before production. They can leak sensitive data.", "code-smell", "low"),
            (r'\bvar\s+\w+', "Use of var", "Use 'const' or 'let' instead of 'var' to avoid hoisting and scoping issues.", "code-smell", "low"),
            (r'//\s*(TODO|FIXME|HACK|XXX)', "Unresolved TODO/FIXME", "Unresolved TODO or FIXME. Address before shipping to production.", "maintainability", "low"),
            (r'catch\s*\(\s*\w+\s*\)\s*\{\s*\}', "Empty Catch Block", "Empty catch block silently swallows errors. Add proper error handling or at minimum log the error.", "maintainability", "medium"),
            (r'(?<![.\w])(0\.\d+)(?![\w%])', "Magic Decimal Number", "Magic decimal found. Use a named constant like DISCOUNT_RATE = 0.85 for clarity.", "readability", "low"),
            (r'if\s*\(.+\)\s*\{[^}]*if\s*\(.+\)\s*\{[^}]*if\s*\(.+\)\s*\{[^}]*if\s*\(', "Deeply Nested Conditionals", "Code is nested 4+ levels deep. Refactor using early returns or helper functions.", "readability", "medium"),
        ]

        for pattern, title, description, category, severity in patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    findings.append({
                        "id": str(uuid.uuid4()),
                        "file": rel_path,
                        "line_start": i,
                        "line_end": i,
                        "category": category,
                        "severity": severity,
                        "rule": f"custom.{title.lower().replace(' ', '-')}",
                        "title": title,
                        "description": description,
                        "snippet": extract_snippet(filepath, i, i),
                    })


        # Extra contextual JS checks (multi-line aware)
        full_source = "".join(lines)

        # JWT alg:none vulnerability
        jwt_pattern = r'alg\s*:\s*.{0,3}none'
        if re.search(jwt_pattern, full_source, re.IGNORECASE):
            line_no = next((i+1 for i, l in enumerate(lines) if re.search(jwt_pattern, l, re.IGNORECASE)), 1)
            findings.append({
                "id": str(uuid.uuid4()), "file": rel_path,
                "line_start": line_no, "line_end": line_no,
                "category": "security", "severity": "critical",
                "rule": "custom.jwt-alg-none",
                "title": "JWT Algorithm None Vulnerability",
                "description": "JWT configured with alg:'none' disables signature verification entirely. Any attacker can forge tokens and impersonate any user. Always specify a strong algorithm like RS256 or HS256.",
                "snippet": extract_snippet(filepath, line_no, line_no),
            })

        # Insecure cookie flags
        for i, line in enumerate(lines, 1):
            if re.search(r'res\.cookie\s*\(', line):
                if "httponly" not in line.lower() and "httpOnly" not in line:
                    findings.append({
                        "id": str(uuid.uuid4()), "file": rel_path,
                        "line_start": i, "line_end": i,
                        "category": "security", "severity": "high",
                        "rule": "custom.cookie-no-httponly",
                        "title": "Cookie Missing HttpOnly Flag",
                        "description": "Cookie set without httpOnly: true. JavaScript can read this cookie, enabling session theft via XSS attacks.",
                        "snippet": extract_snippet(filepath, i, i),
                    })
                if "secure" not in line.lower():
                    findings.append({
                        "id": str(uuid.uuid4()), "file": rel_path,
                        "line_start": i, "line_end": i,
                        "category": "security", "severity": "medium",
                        "rule": "custom.cookie-no-secure",
                        "title": "Cookie Missing Secure Flag",
                        "description": "Cookie set without secure: true. The cookie can be sent over unencrypted HTTP connections.",
                        "snippet": extract_snippet(filepath, i, i),
                    })

        # Mass assignment: req.body passed directly to model
        for i, line in enumerate(lines, 1):
            if re.search(r'\.(?:update|create|save|findOneAndUpdate)\s*\(\s*req\.body', line):
                findings.append({
                    "id": str(uuid.uuid4()), "file": rel_path,
                    "line_start": i, "line_end": i,
                    "category": "security", "severity": "high",
                    "rule": "custom.mass-assignment",
                    "title": "Mass Assignment Vulnerability",
                    "description": "req.body passed directly to a model method. An attacker can set any field including isAdmin or role. Use an explicit allowlist: const {name, email} = req.body.",
                    "snippet": extract_snippet(filepath, i, i),
                })

        # N+1 query: DB call inside a loop
        in_loop = False
        loop_depth = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.search(r'\bfor\b|\bwhile\b|\.forEach\s*\(|\.map\s*\(|\.filter\s*\(', stripped):
                loop_depth += 1
            if loop_depth > 0 and re.search(r'\.find\s*\(|\.findOne\s*\(|\.query\s*\(|\.execute\s*\(|\.get\s*\(http|db\.', stripped):
                findings.append({
                    "id": str(uuid.uuid4()), "file": rel_path,
                    "line_start": i, "line_end": i,
                    "category": "maintainability", "severity": "high",
                    "rule": "custom.n-plus-one",
                    "title": "N+1 Query Problem",
                    "description": "Database/API call detected inside a loop. For N items this fires N queries. Use bulk operations, Promise.all(), or include() to fetch related data in one query.",
                    "snippet": extract_snippet(filepath, i, i),
                })
            if "{" in stripped:
                pass
            if "}" in stripped and loop_depth > 0:
                loop_depth = max(0, loop_depth - 1)

        # Hardcoded IP addresses
        for i, line in enumerate(lines, 1):
            if re.search(r'[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}', line):
                if not re.search(r'127\.0\.0\.1|0\.0\.0\.0|localhost', line):
                    findings.append({
                        "id": str(uuid.uuid4()), "file": rel_path,
                        "line_start": i, "line_end": i,
                        "category": "maintainability", "severity": "medium",
                        "rule": "custom.hardcoded-ip",
                        "title": "Hardcoded IP Address",
                        "description": "IP address hardcoded in source. Use environment variables (process.env.DB_HOST) so it can change between environments.",
                        "snippet": extract_snippet(filepath, i, i),
                    })

        # Float equality comparison
        for i, line in enumerate(lines, 1):
            if re.search(r'\d+\.\d+\s*===?\s*|===?\s*\d+\.\d+', line):
                findings.append({
                    "id": str(uuid.uuid4()), "file": rel_path,
                    "line_start": i, "line_end": i,
                    "category": "maintainability", "severity": "medium",
                    "rule": "custom.float-equality",
                    "title": "Float Equality Comparison",
                    "description": "Comparing floats with == or === is unreliable due to floating-point precision. Use Math.abs(a - b) < Number.EPSILON instead.",
                    "snippet": extract_snippet(filepath, i, i),
                })

    except Exception as e:
        logger.error(f"JS analysis error for {filepath}: {e}")

    return findings



def analyze_cpp_patterns(filepath: str, base_dir: str) -> list:
    """C/C++ static analysis using regex patterns."""
    import re
    findings = []

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
            src_lines = source.splitlines()

        rel_path = os.path.relpath(filepath, base_dir)

        patterns = [
            # Dangerous functions — buffer overflow / memory corruption
            (r"\bgets\s*\(", "Dangerous gets() Function", "gets() reads unlimited input and is the most notorious cause of stack buffer overflows. It has been removed from C11. Replace with fgets(buf, sizeof(buf), stdin) or std::cin.", "security", "critical"),
            (r"\bstrcpy\s*\(", "Unsafe strcpy()", "strcpy() does not check buffer size and will overflow if input exceeds the destination buffer. Use strncpy(), strlcpy(), or std::string instead.", "security", "critical"),
            (r"\bstrcat\s*\(", "Unsafe strcat()", "strcat() does not check buffer bounds and can overflow the destination buffer. Use strncat() or std::string concatenation.", "security", "critical"),
            (r"\bsprintf\s*\(", "Unsafe sprintf()", "sprintf() can overflow the destination buffer. Use snprintf() which accepts a maximum length argument.", "security", "high"),
            (r"\bscanf\s*\(\s*[^,)]*,\s*\"?%s", "Unsafe scanf %s", "scanf() with %s reads unlimited characters. Use a width specifier like %255s or switch to fgets().", "security", "critical"),
            (r"\bprintf\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\)", "Format String Vulnerability", "printf() called with a variable as the format string. If that variable contains user input, attackers can read/write arbitrary memory. Always use printf(\"\%s\", var).", "security", "critical"),

            # Memory management issues
            (r"\bdelete\s+(?!\[)\w+\s*;", "Wrong delete for Array", "Using delete on an array allocated with new[]. This is undefined behavior and causes heap corruption. Use delete[] for arrays.", "security", "high"),
            (r"=\s*new\s+\w+\[", "Raw Array Allocation", "Raw new[] allocation detected. Prefer std::vector<T> or std::array which manage memory automatically and prevent leaks.", "maintainability", "medium"),
            (r"\bnew\s+\w+\s*(?:;|\))", "Raw Heap Allocation", "Raw new allocation without a smart pointer. If an exception occurs before delete, memory leaks. Use std::make_unique<T>() or std::make_shared<T>() instead.", "maintainability", "high"),
            (r"(?:char|int|float)\s*\*\s*\w+\s*=\s*new", "Raw Pointer Ownership", "Raw owning pointer detected. Raw pointers do not express ownership and are easy to leak or double-free. Use std::unique_ptr or std::shared_ptr.", "maintainability", "high"),

            # Null/dangling pointer risks
            (r"delete\s+\w+\s*;(?!\s*\w+\s*=\s*nullptr)", "Pointer Not Nullified After Delete", "Pointer is deleted but not set to nullptr. Any subsequent access becomes a dangling pointer dereference, causing undefined behavior or crashes.", "security", "medium"),

            # Deprecated / unsafe patterns
            (r"\bmalloc\s*\(", "Use of malloc in C++", "malloc() does not call constructors and requires manual free(). In C++, use new/delete or preferably std::vector/smart pointers.", "code-smell", "medium"),
            (r"\bfree\s*\(", "Use of free() in C++", "free() does not call destructors. In C++, pair new with delete (or use smart pointers), never mix malloc/free with new/delete.", "code-smell", "medium"),
            (r"#include\s*<cstring>|#include\s*<string\.h>", "C String Header Included", "Including C string functions. Consider using std::string from <string> which is safer and manages memory automatically.", "maintainability", "low"),
            (r"using namespace std;", "Using Namespace std", "Importing the entire std namespace can cause name collisions in larger projects. Prefer explicit std:: prefix or targeted using declarations.", "code-smell", "low"),

            # Resource leaks
            (r"=\s*new\s+\w+[^;]*;[\s\S]{0,2000}return\s*;(?![\s\S]{0,100}delete)", "Potential Memory Leak on Return", "Memory allocated with new before a return statement with no corresponding delete. This memory will be leaked every time this code path is taken.", "maintainability", "high"),
            (r"FILE\s*\*\s*\w+\s*=\s*fopen", "Potential File Handle Leak", "fopen() result stored in raw FILE pointer. If an early return or exception occurs before fclose(), the file handle is leaked. Use RAII wrappers.", "maintainability", "medium"),

            # Integer issues
            (r"int\s+\w+\s*=\s*strlen\s*\(", "Signed/Unsigned Mismatch", "strlen() returns size_t (unsigned). Storing in a signed int can cause issues on large strings where the value wraps. Use size_t.", "maintainability", "medium"),

            # Hardcoded values
            (r"(?i)(password|secret|api_key|token)\s*=\s*[\"'][^\",;]{4,}[\"']", "Hardcoded Secret", "Sensitive credential hardcoded in source. Move to environment variables or a config file.", "security", "critical"),
            (r"#define\s+\w*(?:PASSWORD|SECRET|KEY|TOKEN)\s+", "Hardcoded Secret via #define", "Secret or credential defined as a preprocessor macro. These are compiled into the binary and are easily extracted. Use environment variables.", "security", "high"),

            # Style / maintainability
            (r"//\s*(TODO|FIXME|HACK|XXX)", "Unresolved TODO/FIXME", "Unresolved TODO or FIXME comment. Address before shipping.", "maintainability", "low"),
            (r"\bcatch\s*\(\.\.\.\)\s*\{\s*\}", "Empty Catch-All Block", "catch(...) with empty body silently swallows all exceptions including std::bad_alloc. Always log or handle exceptions.", "maintainability", "medium"),
        ]

        for pattern, title, description, category, severity in patterns:
            for i, line in enumerate(src_lines, 1):
                stripped = line.strip()
                if stripped.startswith("//") or stripped.startswith("/*"):
                    continue
                if re.search(pattern, line):
                    findings.append({
                        "id": str(uuid.uuid4()),
                        "file": rel_path,
                        "line_start": i,
                        "line_end": i,
                        "category": category,
                        "severity": severity,
                        "rule": f"custom.cpp.{title.lower().replace(' ', '-').replace('(', '').replace(')', '')}",
                        "title": title,
                        "description": description,
                        "snippet": extract_snippet(filepath, i, i),
                    })

    except Exception as e:
        logger.error(f"C++ analysis error for {filepath}: {e}")

    return findings


def analyze_java_patterns(filepath: str, base_dir: str) -> list:
    """Java static analysis using regex patterns."""
    import re
    findings = []

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            src_lines = f.readlines()

        rel_path = os.path.relpath(filepath, base_dir)

        patterns = [
            (r"(?i)(password|secret|api_key|token)\s*=\s*\"[^\"]{4,}\"", "Hardcoded Secret", "Sensitive credential hardcoded. Move to environment variables or a secrets manager.", "security", "critical"),
            (r"Statement\s+\w+\s*=|createStatement\(\)", "Raw SQL Statement", "Using raw Statement instead of PreparedStatement. String-concatenated queries are vulnerable to SQL injection. Use PreparedStatement with ? placeholders.", "security", "critical"),
            (r"\"\s*\+\s*\w+\s*\+\s*\"[^;]*(?:SELECT|INSERT|UPDATE|DELETE|WHERE)", "SQL Injection via Concatenation", "SQL query built by string concatenation. An attacker can inject malicious SQL. Use PreparedStatement.", "security", "critical"),
            (r"Runtime\.getRuntime\(\)\.exec\(|ProcessBuilder\([^)]*\+", "Command Injection Risk", "Executing shell commands with dynamic input. An attacker can inject shell metacharacters. Validate and sanitize all inputs.", "security", "critical"),
            (r"MessageDigest\.getInstance\(\"MD5\"\)", "Weak Hashing (MD5)", "MD5 is cryptographically broken. Use SHA-256 or bcrypt/argon2 for passwords.", "security", "high"),
            (r"MessageDigest\.getInstance\(\"SHA-1\"\)", "Weak Hashing (SHA1)", "SHA-1 is considered weak. Use SHA-256 or stronger.", "security", "high"),
            (r"new\s+Random\s*\(\)", "Weak Random Number Generator", "java.util.Random is not cryptographically secure. Use java.security.SecureRandom for security-sensitive operations.", "security", "high"),
            (r"catch\s*\(Exception\s+\w+\)\s*\{\s*\}", "Empty Catch Block", "Empty catch block swallows exceptions silently. Log the error or rethrow.", "maintainability", "medium"),
            (r"catch\s*\(Exception\s+\w+\)\s*\{[^}]*\}", "Catching Generic Exception", "Catching Exception catches everything including RuntimeException. Catch specific exceptions for clearer error handling.", "maintainability", "medium"),
            (r"System\.out\.print", "System.out.println in Production", "Use a logging framework (SLF4J, Log4j) instead of System.out. Logging frameworks support log levels and can be disabled in production.", "code-smell", "low"),
            (r"public\s+\w+\s*\(\w+(?:,\s*\w+){5,}\)", "Too Many Parameters", "Method has 6+ parameters. Consider using a Builder pattern or a parameter object.", "readability", "medium"),
            (r"//\s*(TODO|FIXME|HACK|XXX)", "Unresolved TODO/FIXME", "Unresolved TODO or FIXME. Address before shipping.", "maintainability", "low"),
            (r"(?i)(password|secret|key)\s*=\s*\"[^\"]+\"", "Hardcoded Credential", "Credential hardcoded in source. Move to environment variables or a vault.", "security", "critical"),
            (r"\.equals\s*\(null\)", "Incorrect Null Check", "Calling .equals(null) will always return false. Use == null for null checks.", "code-smell", "medium"),
            (r"instanceof\s+\w+\s*&&", "Redundant instanceof Check", "instanceof already returns false for null, so a separate null check is redundant.", "readability", "low"),
        ]

        for pattern, title, description, category, severity in patterns:
            for i, line in enumerate(src_lines, 1):
                stripped = line.strip()
                if stripped.startswith("//") or stripped.startswith("*"):
                    continue
                if re.search(pattern, line):
                    findings.append({
                        "id": str(uuid.uuid4()),
                        "file": rel_path,
                        "line_start": i,
                        "line_end": i,
                        "category": category,
                        "severity": severity,
                        "rule": f"custom.java.{title.lower().replace(' ', '-').replace('(', '').replace(')', '')}",
                        "title": title,
                        "description": description,
                        "snippet": extract_snippet(filepath, i, i),
                    })

    except Exception as e:
        logger.error(f"Java analysis error for {filepath}: {e}")

    return findings


def analyze_job(job_id: str, tmp_dir: str, file_paths: list):
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["message"] = "Running analysis..."
        jobs[job_id]["total_files"] = len(file_paths)

        findings = run_analysis(file_paths, tmp_dir)

        jobs[job_id]["progress"] = 95
        jobs[job_id]["message"] = "Finalizing results..."

        by_category = {}
        by_severity = {}
        for f in findings:
            by_category[f["category"]] = by_category.get(f["category"], 0) + 1
            by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1

        summary = {
            "total_issues": len(findings),
            "by_category": by_category,
            "by_severity": by_severity,
            "files_analyzed": len(file_paths),
        }

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = "Analysis complete."
        jobs[job_id]["results"] = findings
        jobs[job_id]["summary"] = summary
        jobs[job_id]["files_processed"] = len(file_paths)

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = str(e)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.post("/analyze")
async def analyze(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    job_id = str(uuid.uuid4())
    tmp_dir = tempfile.mkdtemp()
    file_paths = []

    for upload in files:
        ext = Path(upload.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue
        dest = os.path.join(tmp_dir, upload.filename)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        content = await upload.read()
        with open(dest, "wb") as f:
            f.write(content)
        file_paths.append(dest)

    if not file_paths:
        raise HTTPException(status_code=400, detail="No supported files found.")

    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "message": "Job queued.",
        "files": [f.filename for f in files],
        "results": None,
        "summary": None,
        "files_processed": 0,
        "total_files": len(file_paths),
    }

    thread = threading.Thread(target=analyze_job, args=(job_id, tmp_dir, file_paths))
    thread.daemon = True
    thread.start()

    return {"job_id": job_id, "message": f"Successfully queued {len(file_paths)} files for analysis"}


@app.get("/job/{job_id}/status")
def get_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "message": job["message"],
        "files_processed": job.get("files_processed", 0),
        "total_files": job.get("total_files", len(job["files"])),
    }


@app.get("/job/{job_id}/results")
def get_results(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not complete. Status: {job['status']}")
    return {
        "job_id": job_id,
        "summary": job["summary"],
        "findings": job["results"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}