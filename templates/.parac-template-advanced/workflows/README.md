# Workflows

This directory contains workflow definitions.

## Available Workflows

### feature_development
Full feature development cycle:
1. Architect designs feature
2. Coder implements
3. Tester creates tests
4. Reviewer reviews code
5. Documenter writes docs

### bugfix
Streamlined bug fix workflow:
1. Coder fixes bug
2. Tester validates
3. Reviewer approves

### code_review
Comprehensive code review:
1. Reviewer checks quality
2. Security agent scans for vulnerabilities
3. Tester validates tests

### security_audit
Security scanning workflow:
1. Security agent runs scans
2. Generates compliance reports
3. Creates remediation tickets

### release
Release management workflow:
1. Release manager bumps version
2. Generates changelog
3. Creates release artifacts
4. Deploys to environments

## Creating Custom Workflows

Create YAML files in this directory:

```yaml
# .parac/workflows/my_workflow.yaml
name: My Custom Workflow
description: Does something useful

steps:
  - id: step1
    agent: architect
    task: Design solution

  - id: step2
    agent: coder
    task: Implement solution
    depends_on: [step1]
```
