# AI IDE Instructions for Paracle

This directory contains configuration files for various AI-powered IDEs to help them understand and work effectively with Paracle's `.parac` configuration system.

## 📋 Available Instructions

- `.cursorrules` - Cursor IDE
- `.clinerules` - Cline
- `.windsurfrules` - Windsurf
- `.github-copilot.md` - GitHub Copilot
- `.deepseek-coder.md` - DeepSeek Coder
- `.google-gemini.md` - Google Gemini
- `.mistral-codestral.md` - Mistral Codestral
- `.kimi-k2.md` - Kimi K2
- `.paracle` - Paracle-specific rules

## 🎯 Purpose

These files help AI assistants:

1. **Understand `.parac` structure** - Learn the organization of Paracle configuration files
2. **Follow conventions** - Apply proper naming, formatting, and schema rules
3. **Maintain consistency** - Ensure changes align with project standards
4. **Provide better suggestions** - Offer contextually appropriate recommendations
5. **Validate changes** - Check for common mistakes and anti-patterns

## 🚀 Usage

### For Project Setup

Copy the appropriate file(s) to your project root:

```bash
# For Cursor IDE
cp templates/ai-instructions/.cursorrules .cursorrules

# For Cline
cp templates/ai-instructions/.clinerules .clinerules

# For Windsurf
cp templates/ai-instructions/.windsurfrules .windsurfrules

# For general Paracle rules
cp templates/ai-instructions/.paracle .paracle
```

### For Individual IDEs

Most AI IDEs automatically detect and load their respective configuration files:

- **Cursor**: Looks for `.cursorrules`
- **Cline**: Looks for `.clinerules`
- **Windsurf**: Looks for `.windsurfrules`
- **GitHub Copilot**: Reference `.github-copilot.md` in your docs
- **Others**: Use the markdown files as reference documentation

## 📝 What's Included

Each instruction file covers:

### 1. `.parac` Structure Understanding
- Directory organization
- File purposes and relationships
- Schema versions and validation

### 2. Configuration Management
- Project settings (`project.yaml`)
- Agent specifications (`agents/`)
- Workflow definitions (`workflows/`)
- Tool registry (`tools/`)
- Security policies (`policies/`)

### 3. Best Practices
- Naming conventions
- YAML formatting
- Security considerations
- Version control

### 4. Common Operations
- Creating new agents
- Defining workflows
- Configuring providers
- Managing tools and policies

### 5. Validation Rules
- Schema compliance
- Required fields
- Value constraints
- Cross-reference validation

## 🔧 Customization

You can customize these files for your specific project:

1. Copy the file to your project root
2. Edit to add project-specific rules
3. Add custom conventions or requirements
4. Reference internal documentation

Example additions:

```yaml
# In .cursorrules or similar
custom_rules:
  - "All agents must have a 'cost_tier' field"
  - "Use 'gpt-4' for production, 'gpt-3.5-turbo' for development"
  - "Security policies must be reviewed by @security-team"
```

## 🎓 Learning Resources

For more information about `.parac` configuration:

- [Template Documentation](../.parac-template/README.md)
- [Getting Started Guide](../../docs/getting-started.md)
- [Architecture Documentation](../../docs/architecture.md)

## 🤝 Contributing

Improvements to these AI instructions are welcome:

1. Test with your AI IDE
2. Identify gaps or issues
3. Submit improvements via PR
4. Share your customizations

## 📜 License

These instruction files are part of Paracle and licensed under Apache 2.0.

---

**Note**: AI assistants are helpers, not replacements for understanding Paracle's architecture. Always review AI-generated code and configurations.
