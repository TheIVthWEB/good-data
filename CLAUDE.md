# CLAUDE.md - AI Assistant Guidelines

This document provides essential context and guidelines for AI assistants working with the **good-data** repository.

## Project Overview

**good-data** is a new repository under the TheIVthWEB organization. This project is in its initial setup phase.

### Current Status

- **Repository State**: Initial setup (empty repository)
- **Branch**: Development happening on Claude session branches
- **Next Steps**: Add initial project structure and code

---

## Repository Structure

```
good-data/
├── CLAUDE.md          # AI assistant guidelines (this file)
└── [To be added]      # Project files will be added here
```

> **Note**: Update this section as the project structure develops.

---

## Development Workflow

### Git Branching Strategy

1. **Main Branch**: Primary branch for stable code
2. **Feature Branches**: Use descriptive names (e.g., `feature/add-data-validation`)
3. **Claude Branches**: AI-assisted development uses `claude/*` prefixed branches

### Commit Message Conventions

Follow conventional commit format:
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(parser): add support for CSV files
fix(validation): handle null values correctly
docs: update API documentation
```

---

## Code Conventions

### General Guidelines

1. **Keep it Simple**: Prefer clarity over cleverness
2. **DRY Principle**: Don't repeat yourself, but avoid premature abstraction
3. **Documentation**: Document public APIs and non-obvious logic
4. **Error Handling**: Handle errors gracefully at system boundaries

### File Naming

- Use lowercase with hyphens for file names: `data-processor.ts`
- Use PascalCase for class files if applicable: `DataProcessor.ts`
- Configuration files: `config.json`, `.env.example`

---

## Common Tasks

### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd good-data

# Install dependencies (when applicable)
# npm install / pip install -r requirements.txt / etc.
```

### Running the Project

> **TODO**: Add run commands as the project develops

### Testing

> **TODO**: Add test commands and conventions

### Building

> **TODO**: Add build commands

---

## AI Assistant Guidelines

### When Working in This Repository

1. **Read Before Modifying**: Always read files before making changes
2. **Minimal Changes**: Make only the changes requested; avoid over-engineering
3. **Test Your Changes**: Run tests after modifications when available
4. **Commit Regularly**: Create meaningful commits with clear messages
5. **Ask When Unclear**: If requirements are ambiguous, ask for clarification

### What to Avoid

- Don't add features beyond what was requested
- Don't refactor unrelated code
- Don't add excessive comments or documentation to unchanged code
- Don't introduce new dependencies without justification
- Don't commit sensitive data (API keys, credentials, etc.)

### Security Considerations

- Never commit secrets or credentials
- Use `.env` files for sensitive configuration (add to `.gitignore`)
- Validate all external inputs
- Be cautious with file operations and user-provided paths

---

## Environment Setup

### Prerequisites

> **TODO**: List required tools and versions as the project develops

### Configuration

> **TODO**: Document environment variables and configuration options

---

## Useful Commands Reference

```bash
# Git operations
git status                    # Check current state
git diff                      # View unstaged changes
git log --oneline -10         # View recent commits

# Push to remote (for Claude branches)
git push -u origin <branch-name>
```

---

## Project-Specific Notes

> Add project-specific context, gotchas, and important details here as the project develops.

---

## Contact & Resources

- **Organization**: TheIVthWEB
- **Repository**: good-data

---

*Last updated: 2025-11-29*
