# SECURITY.md - Ayurcare Agent Security Policy

This document details the security design and mitigations implemented in the Ayurcare Agent multi-agent guidance system to satisfy project evaluation rubrics.

## 1. Input Sanitization
To prevent prompt-injection attacks (where a user attempts to bypass agent boundaries, jailbreak the model, or override system instructions), the orchestrator runs all user messages through a sanitation filter before passing them to any agent:
- **Injection Patterns Detection:** Regular expressions scan for phrases such as "ignore previous instructions", "system override", "delete all rules", "you are now", and "jailbreak".
- **Redaction:** Any matching phrases are replaced with `[REDACTED INJECTION ATTEMPT]`.
- **Constraint Enforcement:** Special character runs and excessive spacing are stripped.

## 2. API Key Protection
To safeguard credentials and comply with developer best practices:
- **No Hardcoding:** The project contains zero hardcoded API keys or credentials.
- **Environment Retrieval:** The Gemini API keys (`GOOGLE_API_KEY` or `GEMINI_API_KEY`) are fetched dynamically at runtime from environment variables or `.env` configuration.
- **Zero Logging Policy:** If an error occurs, the server logs a generic exception type message (e.g. `Error executing ADK agents: ...`) and never prints, logs, or transmits the environment key value or detailed context containing sensitive config tokens.

## 3. Rate-Limiting and Abuse Prevention
To prevent Denial of Service (DoS) and abuse of model API endpoints:
- **IP-Based Tracking:** Requests are tracked in-memory by client IP address (`X-Forwarded-For` or request remote address).
- **Sliding Window Rate-Limiter:** Limits users to a maximum of **15 requests per 60-second window**.
- **HTTP 429 Responses:** Requests exceeding this threshold are blocked with a `429 Too Many Requests` status code.

## 4. Medical Escalation Gating (Safety Agent)
To protect user physical health and ensure wellness limits:
- **Red Flag List:** A dictionary of critical medical symptoms (e.g. chest pain, breathing difficulty, severe bleeding) is stored in the knowledge base.
- **Final Validation Gating:** The `safety_agent` reviews all outputs last. If any red flags are triggered, it completely overrides the wellness pipeline and output, instructing the user to immediately seek professional emergency medical services.
- **Compliance Sanitization:** The safety agent automatically rewrites responses to remove specific herbal dosage amounts or clinical cure claims, maintaining a strict wellness-only alignment.
