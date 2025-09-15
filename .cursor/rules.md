# Cursor Development Rules

These rules guide development practices for the Legal Simulation Platform using Cursor AI.

## Code Change Principles

### Minimal Diffs
- **Always write minimal, focused diffs**
- Make the smallest change necessary to achieve the goal
- Avoid unnecessary refactoring or style changes
- Focus on the specific requirement or bug fix

### Refuse Sweeping Refactors
- **Refuse requests for sweeping refactors**
- Avoid changing multiple files unless absolutely necessary
- Prefer incremental improvements over large-scale changes
- If refactoring is needed, break it into small, focused changes

### Preserve Existing Interfaces
- **Prefer interfaces already present in the codebase**
- Don't create new interfaces when existing ones suffice
- Maintain backward compatibility
- Follow established patterns and conventions

### Preserve Public APIs
- **Preserve public API and environment variable names**
- Don't change existing endpoint URLs
- Maintain existing environment variable names
- Keep backward compatibility for external consumers

## Development Guidelines

### Service Architecture
- Follow the microservices architecture defined in `docs/LEGAL_SIM_ARCH.md`
- Each service should have clear boundaries and responsibilities
- Use the established service communication patterns
- Maintain the event-driven architecture

### Code Quality
- Write clean, readable code with proper type hints
- Follow PEP 8 and use black for formatting
- Add comprehensive docstrings for all public functions
- Write tests for all new functionality

### Database Changes
- Use Alembic for all database schema changes
- Write reversible migrations
- Follow the established naming conventions
- Test migrations in both directions

### API Design
- Follow RESTful conventions
- Use consistent HTTP status codes
- Provide clear error messages
- Document all endpoints with OpenAPI

### Security
- Implement proper authentication and authorization
- Follow the chain of custody requirements
- Use secure coding practices
- Validate all inputs

## File Organization

### Service Structure
- Each service follows the established directory structure
- Keep service-specific code within service boundaries
- Use shared modules for common functionality
- Maintain clear separation of concerns

### Shared Components
- Use `services/shared/` for common functionality
- Implement interfaces in `services/shared/interfaces/`
- Keep implementations in `services/shared/implementations/`
- Use factories for dependency injection

### Configuration
- Use environment variables for configuration
- Follow the established naming conventions
- Provide sensible defaults
- Document all configuration options

## Testing Requirements

### Test Coverage
- Maintain test coverage above 80%
- Write unit tests for all business logic
- Add integration tests for service interactions
- Include E2E tests for complete workflows

### Test Organization
- Use pytest fixtures for test data
- Mock external dependencies
- Test both happy path and error cases
- Follow the established test structure

## Documentation Standards

### Code Documentation
- Add docstrings to all public functions
- Document complex algorithms and business logic
- Keep comments up-to-date with code changes
- Use type hints for better documentation

### API Documentation
- Document all endpoints with OpenAPI
- Provide clear examples
- Document error responses
- Keep documentation synchronized with code

### Architecture Documentation
- Update architecture docs when making significant changes
- Document new patterns and conventions
- Keep integration checklist current
- Document deployment and operational procedures

## Error Handling

### Service Communication
- Use the shared HTTP client with retries and circuit breakers
- Implement proper error handling and logging
- Provide meaningful error messages
- Handle timeouts and connection failures gracefully

### Database Operations
- Use proper transaction management
- Handle database connection failures
- Implement proper rollback procedures
- Log database errors appropriately

### File Operations
- Validate file uploads properly
- Handle storage failures gracefully
- Implement proper cleanup procedures
- Follow chain of custody requirements

## Performance Considerations

### Service Performance
- Use async/await for I/O operations
- Implement proper caching strategies
- Optimize database queries
- Monitor service performance

### Resource Management
- Use connection pooling
- Implement proper resource cleanup
- Monitor memory usage
- Handle resource exhaustion gracefully

## Security Guidelines

### Authentication
- Use JWT tokens for authentication
- Implement proper token validation
- Handle token expiration gracefully
- Log authentication events

### Authorization
- Implement role-based access control
- Use the policy engine for authorization
- Follow principle of least privilege
- Audit all access attempts

### Data Protection
- Encrypt sensitive data
- Implement proper input validation
- Follow secure coding practices
- Regular security reviews

## Deployment Considerations

### Environment Configuration
- Use environment variables for configuration
- Provide different configs for different environments
- Document all configuration options
- Validate configuration at startup

### Service Discovery
- Use the established service discovery pattern
- Don't hardcode service URLs
- Implement proper health checks
- Handle service unavailability gracefully

### Monitoring
- Implement proper logging
- Use structured logging with correlation IDs
- Add metrics for business events
- Monitor service health

## Common Patterns

### Repository Pattern
- Use repositories for data access
- Keep business logic out of repositories
- Implement proper error handling
- Use dependency injection

### Event-Driven Architecture
- Use the event bus for service communication
- Implement proper event handling
- Handle event failures gracefully
- Maintain event ordering

### Chain of Custody
- Implement proper audit trails
- Use WORM storage for evidence
- Log all evidence access
- Support legal compliance

## Anti-Patterns to Avoid

### Don't Do These
- Don't hardcode URLs or configuration
- Don't put business logic in controllers
- Don't ignore error handling
- Don't skip tests
- Don't make breaking changes without migration
- Don't ignore security requirements
- Don't skip documentation updates
- Don't make large, unfocused changes