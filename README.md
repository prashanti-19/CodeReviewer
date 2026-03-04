# CodeReviewer: Automated Static Analysis Platform
CodeReviewer is an automated code review platform that performs comprehensive static analysis to identify security vulnerabilities, code smells, maintainability issues, and readability problems across an entire codebase. Designed for both quick spot-checks and deep architectural audits, it allows developers to upload individual files or batches of 20+ files and receive structured, actionable findings with exact line numbers and code snippets.

Unlike cloud-based scanning tools, CodeReviewer runs entirely offline and no data leaves the machine, no third-party API calls are made, and no account or subscription is required.

**Key Features**

- Upload 20+ files simultaneously across multiple languages in a single session
- Every finding includes the exact file, line numbers, code snippet, and a plain-English explanation
- Filter results by category, severity, and file name with full-text search
- Summary charts showing issue distribution by category and severity
- Export complete results as JSON
- Live progress tracking with async background processing
- Fully offline. No internet, no API keys, no data leaves your machine

---

**Analysis Approach**

The platform uses three layers of analysis:

**Taint Analysis** - Tracks user-controlled data (from req.body, request.args, input(), etc.) through the codebase and flags when it reaches a dangerous sink like cursor.execute() or os.system(). This catches logic-based vulnerabilities that pattern matching alone misses.

**AST-Based Analysis** - Uses Abstract Syntax Tree parsing to detect structural issues regex cannot catch: duplicate function bodies, unused variables, god functions scored by cognitive complexity, unbounded recursion, N+1 database queries inside loops, global variable mutations, and naming convention violations.

**Regex Pattern Analysis** - A broad pattern-matching layer applied across all supported languages, targeting hardcoded secrets, dangerous functions, weak cryptographic algorithms, insecure cookie configuration, mass assignment, blocking I/O, magic numbers, and unresolved TODOs.

---

**Language Support**

Deep Analysis (Taint + AST + Patterns):
- **Python** - N+1 queries, insecure cookies, pickle deserialization, taint-traced SQL injection, god functions, duplicate code, naming conventions, and more
- **JavaScript / TypeScript** - XSS, command injection, path traversal, JWT alg:none, mass assignment, blocking sync I/O, insecure cookies, hardcoded secrets
- **C / C++** - Buffer overflows, gets()/strcpy(), memory leaks, wrong delete[], dangling pointers, format string vulnerabilities, raw pointer ownership
- **Java** - SQL injection, weak hashing (MD5/SHA1), insecure Random, command injection, System.out, empty catches, hardcoded credentials

Pattern-Based Analysis (Secrets + Common Vulnerabilities):
Ruby, PHP, C#, Go, Shell, HTML, CSS/SCSS, YAML/JSON

---

**Finding Categories**

- **Security** (Critical–High) - SQL injection, XSS, command injection, buffer overflows, hardcoded secrets, insecure deserialization, JWT vulnerabilities, mass assignment, weak hashing
- **Code Smells** (Medium–Low) - Duplicate functions, unused variables, console.log left in production, use of var, print statements, dead code
- **Maintainability** (High–Low) - God functions, N+1 queries, unbounded recursion, global mutation, unclosed resources, hardcoded IPs and file paths
- **Readability** (Medium–Low) - Magic numbers, deeply nested code, too many parameters, non-standard naming conventions, float equality comparisons

---

**Technical Architecture**

- **Backend** - Python (FastAPI): analysis engine, AST parsing, taint analysis, regex patterns, async job processing via background threads, REST API
- **Frontend** - TypeScript and React (Figma Make): type-safe, responsive UI for file upload, live progress polling, results dashboard, syntax-highlighted code snippets
- **Styling** - Tailwind CSS
- **API** - Three REST endpoints: POST /analyze (upload files, receive job ID), GET /job/{id}/status (poll progress), GET /job/{id}/results (retrieve findings)

---

**Development**

The frontend was built and deployed using Figma Make. The analysis engine, API architecture, and security detection logic were developed through a collaborative session with Claude (Anthropic), with iterative refinement based on real test cases across Python, JavaScript, C++, and Java files.
