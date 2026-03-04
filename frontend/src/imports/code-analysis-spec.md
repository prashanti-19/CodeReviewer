Technical Specification: Code Quality Analysis Platform
What You're Building
A web application where users upload 20+ code files (potentially millions of lines), and the system returns structured findings for:

Code smells (duplicated logic, long methods, god classes, etc.)
Security vulnerabilities (SQL injection, hardcoded secrets, XSS vectors, etc.)
Poor maintainability (high cyclomatic complexity, deeply nested logic, magic numbers, etc.)
Low readability (unclear naming, missing docs, overly long lines, etc.)

Each finding must include the exact code snippet and a plain-English explanation like: "Lines 42–47 show a hardcoded API key, which exposes credentials in source control."

Stack Confirmation: Yes, Python + React Works Well
This is a solid, pragmatic choice. Here's how it maps:
LayerTechnologyFrontendReact (file upload UI, results dashboard)Backend APIPython with FastAPIAnalysis EnginePython static analysis librariesFile HandlingPython's built-in ast, plus third-party toolsQueue/JobsCelery + Redis (for large file processing async)

Backend (Python / FastAPI)
File Upload & Parsing

Accept multi-file uploads via a single API endpoint (POST /analyze)
Support common languages: .py, .js, .ts, .java, .go, .rb, .php, .cs, etc.
Store uploaded files temporarily (local disk or S3)
Language detection can be done by file extension or a library like guesslang

Analysis Pipeline — This Is the Core
The team should run multiple specialized analyzers and merge their results:
For Python files:

pylint — code smells, style issues, complexity
bandit — security vulnerabilities specifically
radon — cyclomatic complexity, maintainability index
pyflakes — unused variables, bad imports

For JavaScript/TypeScript:

eslint with plugins: eslint-plugin-security, sonarjs
jshint as backup

For multi-language support:

SonarQube (self-hosted, open source community edition) is the gold standard — it handles 20+ languages and produces exactly the kind of structured findings you described. The Python backend can trigger SonarQube scans via its API and fetch results back.
Alternatively, Semgrep (open source, Python-callable) is lighter weight, supports 30+ languages, and returns structured JSON with file, line numbers, severity, and message — very easy to parse.

Recommended approach: Use Semgrep as the primary engine (easy to integrate, fast, multi-language JSON output) and layer in language-specific tools (bandit for Python security, eslint for JS) for deeper coverage.
Output Data Structure
Each finding should be normalized into this shape:
json{
  "file": "src/auth/login.py",
  "line_start": 42,
  "line_end": 47,
  "category": "security",
  "severity": "high",
  "rule": "hardcoded-credentials",
  "title": "Hardcoded API Key Detected",
  "description": "These lines contain a hardcoded API key, which exposes credentials in source control and makes rotation difficult.",
  "snippet": "API_KEY = 'sk-live-abc123...'"
}
Async Processing (Critical for Large Files)
Millions of lines of code can't be processed synchronously in an HTTP request. The team needs:

Celery (Python task queue) + Redis (message broker)
Flow: Upload → create a Job ID → run analysis in background → poll for results
Frontend polls GET /job/{id}/status until complete, then fetches GET /job/{id}/results


Frontend (React)
Key Views

Upload Page — drag-and-drop or file picker, supports 20+ files at once, shows upload progress per file
Processing Screen — live status (e.g., "Analyzing 14/22 files…") using polling or WebSockets
Results Dashboard — the main product:

Summary cards: total issues by category and severity
Filterable table: filter by file, category (smell / security / maintainability / readability), severity (critical / high / medium / low)
Each row expands to show the code snippet with syntax highlighting (use react-syntax-highlighter) and the plain-English explanation
File-level view: click a file to see all its issues grouped



Libraries the Team Should Use

react-dropzone — file upload UX
react-syntax-highlighter — code snippet rendering with line highlighting
axios or react-query — API calls and polling
recharts or chart.js — summary visualizations


Key Architecture Decisions to Communicate
1. Snippet extraction is the team's responsibility, not the analyzer's.
Most tools return line numbers. The backend must open the file, extract lines start-2 to end+2 for context, and attach it to the finding object. Don't assume the analyzer gives you the snippet.
2. Semgrep is the path of least resistance for multi-language support.
It's a Python library (pip install semgrep), runs via subprocess or Python API, outputs clean JSON, and has a huge open-source ruleset covering all four categories you want (smells, security, maintainability, readability). Tell the team to start here.
3. File size handling. For very large files (100k+ lines), analysis can be slow. The team should set per-file timeouts and stream partial results back rather than waiting for all 20+ files to finish.
4. The results need to be paginated. With 20 files and millions of lines, you could get tens of thousands of findings. The API should return paginated results and the frontend should use virtual scrolling (e.g., react-window) not render all rows at once.

Rough Build Order

Basic FastAPI server that accepts file upload + returns dummy JSON ✅
Integrate Semgrep, get real findings in normalized JSON ✅
Add snippet extraction logic ✅
Add Celery + Redis for async jobs ✅
Build React upload + polling + basic results table ✅
Add filters, syntax-highlighted snippets, summary charts ✅
Add language-specific analyzers (bandit, eslint) on top ✅


This gives your team a clear, opinionated path. The only real decision they need to make upfront is Semgrep vs. SonarQube — Semgrep is faster to ship, SonarQube is more enterprise-grade. For an MVP, Semgrep is the right call.