"""Example: Using the Security Agent for vulnerability scanning and security audits.

This example demonstrates:
1. Creating security agent from .parac/agents/specs/security.md
2. Running security scans on code
3. Creating specialized security agents through inheritance
4. Security workflow integration

Security Agent capabilities:
- Dependency vulnerability scanning
- Static security analysis
- Secret detection
- OWASP Top 10 compliance
- Threat modeling
"""

from paracle_domain.factory import AgentFactory
from paracle_domain.models import AgentSpec
from paracle_store import AgentRepository


def main() -> None:
    """Run security agent example."""
    print("\n🔒 PARACLE SECURITY AGENT")
    print("=" * 70)

    # Setup
    repo = AgentRepository()
    factory = AgentFactory(spec_provider=repo.get_spec)

    # =============================================================================
    # Step 1: Create Base Security Agent
    # =============================================================================
    print("\n" + "=" * 70)
    print("STEP 1: Create Security Agent")
    print("=" * 70)

    security_agent = AgentSpec(
        name="security",
        description="Security auditing, vulnerability detection, and compliance enforcement",
        provider="openai",
        model="gpt-4",
        temperature=0.2,  # Lower temperature for consistent security analysis
        system_prompt=(
            "You are a security expert specializing in application security. "
            "Your role is to identify vulnerabilities, enforce security best practices, "
            "and ensure compliance with security standards (OWASP, CWE, etc.). "
            "You perform thorough security audits, dependency scanning, and threat modeling. "
            "Focus on: authentication, authorization, input validation, injection attacks, "
            "secrets management, and secure coding practices."
        ),
        tools=[
            # Static analysis
            "bandit",
            "safety",
            "semgrep",
            "detect_secrets",
            "pip_audit",
            # Dynamic testing
            "trivy",
            # Comprehensive tools
            "static_analysis",
            "security_scan",
            "vulnerability_detector",
            "secret_scanner",
            "dependency_auditor",
            "compliance_checker",
        ],
        skills=[
            "security-hardening",
            "testing-qa",
            "paracle-development",
            "performance-optimization",
        ],
        metadata={
            "role": "security_audit",
            "source": ".parac/agents/specs/security.md",
            "owasp_version": "2023",
            "compliance": ["owasp-top-10", "cwe-top-25"],
        }
    )

    repo.register_spec(security_agent)
    agent = factory.create(security_agent)
    effective = agent.get_effective_spec()

    print("\n✅ Security Agent Created")
    print(f"   Name: {security_agent.name}")
    print(
        f"   Temperature: {security_agent.temperature} (strict for security)")
    print(f"   Tools: {len(effective.tools)} security tools")
    print(f"   Skills: {len(effective.skills)} skills")
    print(f"   OWASP Version: {effective.metadata['owasp_version']}")

    # =============================================================================
    # Step 2: Security Audit Workflow
    # =============================================================================
    print("\n" + "=" * 70)
    print("STEP 2: Security Audit Workflow")
    print("=" * 70)

    print("\n📋 Security Audit Tasks:")
    audit_tasks = [
        "1. Dependency Vulnerability Scan (pip-audit, safety, trivy)",
        "2. Static Security Analysis (bandit, semgrep)",
        "3. Secret Detection (detect-secrets)",
        "4. OWASP Top 10 Compliance Check",
        "5. Authentication/Authorization Review",
        "6. Input Validation Check",
        "7. SQL Injection Test",
        "8. XSS Vulnerability Test",
        "9. CSRF Protection Validation",
        "10. Security Headers Check",
    ]

    for task in audit_tasks:
        print(f"   {task}")

    print("\n🔍 Example: Dependency Scan")
    print("   Command: pip-audit --desc")
    print("   Result: Scanning 150 packages...")
    print("   ✅ No HIGH or CRITICAL vulnerabilities found")
    print("   ⚠️  2 MEDIUM vulnerabilities (marked for review)")

    # =============================================================================
    # Step 3: Create Specialized Security Agents
    # =============================================================================
    print("\n" + "=" * 70)
    print("STEP 3: Specialized Security Agents via Inheritance")
    print("=" * 70)

    # Python Security Specialist
    python_security = AgentSpec(
        name="python-security-specialist",
        description="Python-specific security expert",
        parent="security",  # Inherits from base security agent
        provider="openai",
        model="gpt-4-turbo",
        temperature=0.15,  # Even stricter
        system_prompt=(
            "You are a Python security expert. Focus on Python-specific vulnerabilities: "
            "pickle deserialization, eval/exec injection, subprocess injection, "
            "path traversal, regex DoS, and Python-specific OWASP issues."
        ),
        tools=[
            "pylint_secure_coding",  # Python-specific linter
        ],  # Adds to base security tools
        skills=[
            "python-security",
        ],  # Adds to base security skills
        metadata={
            "language": "python",
            "focus": "python_vulnerabilities",
        }
    )

    repo.register_spec(python_security)
    python_sec_agent = factory.create(python_security)
    python_sec_effective = python_sec_agent.get_effective_spec()

    print("\n✅ Python Security Specialist Created")
    print(f"   Parent: {python_security.parent}")
    print(
        f"   Tools: {len(python_sec_effective.tools)} (inherited + specialized)")
    print(f"   Skills: {len(python_sec_effective.skills)}")
    print("   Focus: Python-specific vulnerabilities")

    # API Security Specialist
    api_security = AgentSpec(
        name="api-security-specialist",
        description="API security expert",
        parent="security",
        provider="openai",
        model="gpt-4",
        temperature=0.2,
        system_prompt=(
            "You are an API security expert. Focus on API-specific vulnerabilities: "
            "authentication bypass, broken authorization, rate limiting, "
            "mass assignment, API injection, and REST/GraphQL security."
        ),
        tools=[
            "owasp_zap",  # API security scanner
            "burp_suite",  # Web vulnerability scanner
        ],
        skills=[
            "api-security",
        ],
        metadata={
            "focus": "api_security",
            "standards": ["rest", "graphql", "grpc"],
        }
    )

    repo.register_spec(api_security)
    api_sec_agent = factory.create(api_security)
    api_sec_effective = api_sec_agent.get_effective_spec()

    print("\n✅ API Security Specialist Created")
    print(f"   Parent: {api_security.parent}")
    print(f"   Tools: {len(api_sec_effective.tools)} (includes API scanners)")
    print(f"   Standards: {api_sec_effective.metadata['standards']}")

    # =============================================================================
    # Step 4: Security Metrics & Reporting
    # =============================================================================
    print("\n" + "=" * 70)
    print("STEP 4: Security Metrics & KPIs")
    print("=" * 70)

    security_metrics = {
        "Vulnerabilities": {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 2,
            "LOW": 5,
            "INFO": 12,
        },
        "Coverage": {
            "Security Tests": "87%",
            "Code Coverage": "92%",
            "Dependency Audit": "100%",
        },
        "Compliance": {
            "OWASP Top 10": "✅ Compliant",
            "CWE Top 25": "✅ Compliant",
            "Secret Detection": "✅ No secrets found",
        },
        "Time to Patch": {
            "Average": "2.3 days",
            "Last CRITICAL": "4 hours",
            "Last HIGH": "1.5 days",
        }
    }

    print("\n📊 Security Metrics:")
    for category, metrics in security_metrics.items():
        print(f"\n   {category}:")
        for metric, value in metrics.items():
            print(f"      {metric}: {value}")

    # =============================================================================
    # Step 5: Integration with Other Agents
    # =============================================================================
    print("\n" + "=" * 70)
    print("STEP 5: Multi-Agent Security Workflow")
    print("=" * 70)

    workflow = [
        {"agent": "coder", "task": "Implement feature", "status": "✅ Done"},
        {"agent": "security", "task": "Security audit", "status": "▶️ Running"},
        {"agent": "security", "subtask": "Dependency scan", "status": "✅ Pass"},
        {"agent": "security", "subtask": "Static analysis", "status": "✅ Pass"},
        {"agent": "security", "subtask": "Secret detection", "status": "✅ Pass"},
        {"agent": "python-security-specialist",
            "task": "Python-specific review", "status": "▶️ Running"},
        {"agent": "api-security-specialist",
            "task": "API security test", "status": "⏳ Pending"},
        {"agent": "reviewer", "task": "General code review", "status": "⏳ Pending"},
        {"agent": "tester", "task": "Security regression tests", "status": "⏳ Pending"},
    ]

    print("\n🔄 Workflow Steps:")
    for step in workflow:
        agent_name = step["agent"]
        task = step.get("task", step.get("subtask"))
        status = step["status"]
        indent = "      " if "subtask" in step else "   "
        print(f"{indent}{status} {agent_name}: {task}")

    # =============================================================================
    # Step 6: Security Checklist
    # =============================================================================
    print("\n" + "=" * 70)
    print("STEP 6: Pre-Release Security Checklist")
    print("=" * 70)

    checklist = [
        ("✅", "All dependencies scanned for vulnerabilities"),
        ("✅", "No secrets in source code or git history"),
        ("✅", "Authentication mechanisms tested"),
        ("✅", "Authorization rules validated"),
        ("✅", "Input validation on all endpoints"),
        ("✅", "SQL injection tests passed"),
        ("✅", "XSS prevention verified"),
        ("✅", "CSRF protection enabled"),
        ("✅", "Rate limiting configured"),
        ("✅", "Security headers set"),
        ("✅", "HTTPS enforced"),
        ("⚠️ ", "Error messages sanitized (2 warnings)"),
        ("✅", "Logging doesn't expose PII"),
        ("✅", "Security tests in CI/CD"),
        ("⏳", "Penetration testing scheduled"),
    ]

    print("\n📋 Checklist:")
    for status, item in checklist:
        print(f"   {status} {item}")

    passed = sum(1 for s, _ in checklist if s == "✅")
    total = len(checklist)
    warnings = sum(1 for s, _ in checklist if s == "⚠️")
    pending = sum(1 for s, _ in checklist if s == "⏳")

    print(
        f"\n   Status: {passed}/{total} passed, {warnings} warnings, {pending} pending")

    # =============================================================================
    # Summary
    # =============================================================================
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)

    print("\n✅ Created Agents:")
    print(f"   1. security (base) - {len(effective.tools)} tools")
    print(
        f"   2. python-security-specialist - {len(python_sec_effective.tools)} tools")
    print(
        f"   3. api-security-specialist - {len(api_sec_effective.tools)} tools")

    print("\n🛡️ Security Coverage:")
    print("   - Dependency vulnerabilities: ✅ Scanned")
    print("   - Code security issues: ✅ Analyzed")
    print("   - Secrets detection: ✅ No leaks")
    print("   - OWASP Top 10: ✅ Compliant")
    print("   - Python-specific: ✅ Reviewed")
    print("   - API security: ⏳ In progress")

    print("\n🎯 Benefits:")
    print("   - Automated security scanning")
    print("   - Specialized security expertise")
    print("   - Continuous compliance monitoring")
    print("   - Multi-layer security approach")
    print("   - Integration with development workflow")

    print("\n📖 Next Steps:")
    print("   1. Run full security audit: paracle agent run security --task 'audit'")
    print("   2. Fix identified issues (2 MEDIUM priority)")
    print("   3. Complete penetration testing")
    print("   4. Update security documentation")
    print("   5. Schedule regular security reviews")

    print("\n" + "=" * 70)
    print("✅ SECURITY AGENT EXAMPLE COMPLETED!")
    print("=" * 70)


if __name__ == "__main__":
    main()
