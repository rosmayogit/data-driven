# CLAUDE.md

This file provides guidance for AI assistants working with the **data-driven** repository.

## Project Overview

A playground project for exploring data-driven approaches. The repository is in its early stages with no established tech stack, build system, or source code yet.

## Repository Structure

```
data-driven/
├── README.md       # Project description
└── CLAUDE.md       # This file — AI assistant guidance
```

## Current State

- **Single commit** on `master` branch with an initial README
- No source code, configuration files, or dependencies have been added yet
- No tech stack has been chosen

## Development Guidelines

Since this project is in its initial phase, follow these principles when contributing:

### General

- Keep changes small and focused
- Write clear, descriptive commit messages
- Prefer simple solutions over complex abstractions

### When Adding New Technologies

- Document the rationale for tech stack choices in commit messages or README
- Include appropriate configuration files (e.g., `package.json`, `requirements.txt`, `tsconfig.json`)
- Set up linting and formatting from the start
- Add a `.gitignore` appropriate for the chosen stack

### When Adding Code

- Establish and follow consistent naming conventions
- Add tests alongside new functionality
- Keep secrets and credentials out of the repository — use environment variables or `.env` files (gitignored)

## Commands

No build, test, or lint commands are configured yet. Update this section as tooling is added.

<!-- Example format for when commands are established:
```
npm install          # Install dependencies
npm run build        # Build the project
npm test             # Run tests
npm run lint         # Run linter
```
-->
