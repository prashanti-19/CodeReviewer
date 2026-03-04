# CodeReviewer
This automated code review tool provides comprehensive static analysis to identify code smells, security vulnerabilities, and maintainability issues. Designed for both quick checks and deep architectural audits, it allows users to analyze their codebase by uploading individual files or entire directories.

## Deep Semantic Analysis:
For core languages, the tool performs high-fidelity AST-based parsing and Taint analysis to uncover logic-based risks:
  * Python: Detects N+1 queries, global mutations, pickle deserialization, and insecure cookies.
  * JavaScript/TypeScript: Flags XSS, command injection, JWT vulnerabilities, and blocking sync I/O.
  * C/C++: Scans for buffer overflows, memory leaks, dangling pointers, and unsafe functions like gets().
  * Java: Identifies SQL injection, hardcoded credentials, and insecure random number generation.

## Pattern-Based Scanning:
The tool provides broad coverage for Ruby, PHP, C#, Go, Shell, HTML, CSS, and YAML/JSON, specifically targeting:
  * Hardcoded Secrets: API keys, IPs, and credentials.
  * Dangerous Functions: Usage of eval() and insecure defaults.
  * Technical Debt: TODO tracking and inline script violations.

## Technical Architecture:
Built for speed and precision, the platform is powered by:
  * Backend: Python – Manages the entire analysis engine, regex pattern matching, and file handling.
  * Frontend: TypeScript & React – Delivers a type-safe, responsive UI for visualizing findings.
  * Styling: Tailwind CSS – Ensures a clean, modern developer experience.

## Development Workflow: 
The user interface was conceptualized and prototyped in Figma, while the core logic and implementation were refined through a collaborative pairing with Claude, ensuring optimized code quality and robust security checks.
