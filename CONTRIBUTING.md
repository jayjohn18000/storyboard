# Contributing to Legal Simulation Platform

Thank you for your interest in contributing to the Legal Simulation Platform! This document provides guidelines for contributing to the project.

## Development Workflow

### Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment:
   ```bash
   make up  # Start all services
   make test  # Run tests
   ```

### Making Changes

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make small, focused changes**:
   - Keep pull requests small and focused on a single feature or bug fix
   - Each PR should be reviewable in 15-30 minutes
   - Avoid sweeping refactors in a single PR

3. **Follow the commit style**:
   ```
   feat(scope): brief description
   fix(scope): brief description
   docs(scope): brief description
   test(scope): brief description
   refactor(scope): brief description
   ```
   
   Examples:
   - `feat(evidence): add file upload validation`
   - `fix(gateway): resolve circuit breaker timeout`
   - `docs(api): update OpenAPI documentation`

4. **Run checks before committing**:
   ```bash
   make check  # Runs format, lint, and test
   ```

5. **Test your changes**:
   ```bash
   make test        # Unit tests
   make e2e         # End-to-end tests
   make integration # Integration tests
   ```

## Code Standards

### Python Code Style

- Follow PEP 8 guidelines
- Use type hints for all function parameters and return values
- Use `black` for code formatting
- Use `flake8` for linting
- Use `mypy` for type checking

### API Design

- Follow RESTful conventions
- Use consistent HTTP status codes
- Provide clear error messages
- Document all endpoints with OpenAPI

### Database

- Use Alembic for all schema changes
- Write migrations that are reversible
- Include proper indexes for performance
- Follow naming conventions (snake_case)

### Testing

- Write unit tests for all new functionality
- Maintain test coverage above 80%
- Use pytest fixtures for test data
- Mock external dependencies

## Pull Request Process

### Before Submitting

1. **Ensure all checks pass**:
   ```bash
   make check
   ```

2. **Update documentation** if needed:
   - Update API documentation
   - Add/update docstrings
   - Update README if necessary

3. **Add tests** for new functionality:
   - Unit tests for business logic
   - Integration tests for service interactions
   - E2E tests for complete workflows

### PR Description

Include the following in your PR description:

1. **Summary**: Brief description of changes
2. **Type**: Feature, Bug Fix, Documentation, etc.
3. **Testing**: How you tested the changes
4. **Breaking Changes**: Any breaking changes (if applicable)
5. **Checklist**: Confirm you've completed all requirements

### Review Process

1. **Automated checks** must pass
2. **Code review** by at least one maintainer
3. **Approval** required before merging
4. **Squash and merge** when approved

## Environment Setup

### Required Tools

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 14+
- Redis 6+
- Make

### Development Environment

1. **Copy environment file**:
   ```bash
   cp env.example .env
   ```

2. **Start services**:
   ```bash
   make up
   ```

3. **Run database migrations**:
   ```bash
   make db-upgrade
   ```

4. **Verify setup**:
   ```bash
   make test
   ```

## Service-Specific Guidelines

### API Gateway

- All routes should go through the gateway
- Implement proper error handling and status codes
- Use middleware for cross-cutting concerns
- Aggregate OpenAPI documentation

### Evidence Processor

- Implement proper file validation
- Follow chain of custody requirements
- Use content-addressed storage
- Implement virus scanning hooks

### Storyboard Service

- Validate narrative structure
- Implement version control
- Support collaborative editing
- Export to multiple formats

### Timeline Compiler

- Use OTIO for timeline operations
- Validate temporal sequences
- Optimize for performance
- Support multiple export formats

### Render Orchestrator

- Integrate with Blender properly
- Implement render job queuing
- Support multiple output formats
- Handle render failures gracefully

## Security Guidelines

### Authentication & Authorization

- Use JWT tokens for authentication
- Implement proper role-based access control
- Follow principle of least privilege
- Audit all access attempts

### Data Protection

- Encrypt sensitive data at rest and in transit
- Implement proper input validation
- Follow OWASP guidelines
- Regular security audits

### Chain of Custody

- Maintain immutable audit trails
- Implement WORM storage for evidence
- Log all evidence access
- Support legal compliance requirements

## Troubleshooting

### Common Issues

1. **Service won't start**: Check Docker logs and environment variables
2. **Database connection issues**: Verify PostgreSQL is running and accessible
3. **Test failures**: Ensure all services are running and dependencies are installed
4. **Import errors**: Check Python path and virtual environment

### Getting Help

- Check existing issues and discussions
- Create a new issue with detailed information
- Join our community discussions
- Contact maintainers for urgent issues

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Breaking changes are documented
- [ ] Migration scripts are tested
- [ ] Security review completed
- [ ] Performance benchmarks met

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to providing a welcoming and inclusive environment for all contributors.

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.