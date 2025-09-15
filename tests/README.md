# Legal Simulation Platform Test Suite

This directory contains comprehensive tests for the Legal Simulation Platform, covering all aspects from unit tests to end-to-end workflows.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                # Shared fixtures and configuration
├── requirements-test.txt      # Test dependencies
├── README.md                  # This file
├── integration/               # Integration tests
│   └── test_evidence_pipeline.py
├── determinism/               # Render determinism tests
│   └── test_render_determinism.py
├── compliance/                # Policy compliance tests
│   └── test_policy_compliance.py
├── performance/               # Performance and load tests
│   └── test_load_scenarios.py
├── e2e/                      # End-to-end workflow tests
│   └── test_case_creation_flow.py
└── unit/                     # Unit tests (to be created)
```

## Test Categories

### 1. Integration Tests (`tests/integration/`)

Tests the complete evidence processing flow from upload to final storage:

- **Evidence Pipeline**: Complete OCR, ASR, and NLP processing
- **Storage Integrity**: WORM compliance and checksum verification
- **Concurrent Processing**: Multiple evidence items simultaneously
- **Accuracy Validation**: OCR/ASR accuracy on legal documents

**Key Features:**
- Tests with real document formats (PDF, images, audio)
- Verifies chain of custody requirements
- Tests storage integrity and tamper detection
- Concurrent processing validation

### 2. Determinism Tests (`tests/determinism/`)

Ensures frame-perfect reproducibility for legal evidence:

- **Render Reproducibility**: Identical renders produce identical outputs
- **Seed Propagation**: Seeds properly propagated through pipeline
- **Checksum Consistency**: Frame checksums consistent across renders
- **Golden Test Cases**: Regression detection against known good outputs

**Key Features:**
- Tests render reproducibility across multiple runs
- Validates deterministic random number generation
- Verifies checksum consistency for legal integrity
- Golden test cases for regression detection

### 3. Compliance Tests (`tests/compliance/`)

Validates policy compliance and jurisdiction rules:

- **Jurisdiction Rules**: Federal, state, and local compliance
- **Evidence Requirements**: Chain of custody, authentication, best evidence rule
- **Demonstrative Standards**: Accuracy requirements, dispute marking
- **Sandbox Restrictions**: AI assistance, speculation, cinematic rendering

**Key Features:**
- Tests all supported jurisdictions
- Validates evidence authentication requirements
- Tests mode-specific restrictions (DEMONSTRATIVE vs SANDBOX)
- Edge case and boundary condition testing

### 4. Performance Tests (`tests/performance/`)

Load testing and performance validation:

- **Concurrent Users**: Multiple users processing cases simultaneously
- **Large Files**: 1GB+ evidence file processing
- **Render Queue**: Queue performance under load
- **Database Optimization**: Query performance and optimization
- **Memory Profiling**: Memory usage under various operations

**Key Features:**
- Simulates realistic user load scenarios
- Tests with large evidence files (1GB+)
- Measures render queue performance
- Database query optimization validation
- Memory usage profiling and leak detection

### 5. End-to-End Tests (`tests/e2e/`)

Complete user workflow testing:

- **Case Creation Flow**: Full workflow from case creation to render
- **Demonstrative Workflow**: High-accuracy demonstrative case processing
- **Error Recovery**: Upload failures, render crashes, partial state recovery
- **Collaboration Features**: Multi-user workflows and permissions

**Key Features:**
- Tests complete user workflows
- Validates data integrity across the pipeline
- Tests error recovery and resilience
- Multi-user collaboration scenarios

## Running Tests

### Prerequisites

Install test dependencies:
```bash
python run_tests.py install
```

### Test Runner

Use the comprehensive test runner:

```bash
# Run all tests
python run_tests.py all

# Run specific test categories
python run_tests.py integration
python run_tests.py determinism
python run_tests.py compliance
python run_tests.py performance
python run_tests.py e2e

# Run with verbose output
python run_tests.py all -v

# Run performance tests in parallel
python run_tests.py performance -p

# Run specific test file
python run_tests.py all --test-path tests/integration/test_evidence_pipeline.py
```

### Direct Pytest Usage

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov-report=html

# Run specific test category
pytest tests/integration/ -v

# Run with markers
pytest -m "integration" -v
pytest -m "performance and not slow" -v

# Run in parallel
pytest -n auto

# Generate HTML report
pytest --html=test-report.html --self-contained-html
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)

- **Coverage**: Minimum 80% coverage required
- **Timeouts**: 300-second timeout for long-running tests
- **Markers**: Categorized test markers (integration, performance, etc.)
- **Reporting**: HTML, XML, and terminal reports
- **Async**: Automatic async test detection

### Test Fixtures (`conftest.py`)

Shared fixtures for all tests:
- **Temp Directories**: Isolated test file storage
- **Mock Services**: Database, storage, OCR, ASR, renderer services
- **Test Data**: Sample cases, evidence, storyboards
- **Performance Monitoring**: Memory and timing measurements
- **Deterministic Seeds**: Consistent test execution

## Test Data

### Sample Files

The test suite includes various sample files:
- **Documents**: Legal documents in various formats
- **Audio**: Deposition recordings and testimony
- **Images**: Evidence photos and diagrams
- **Video**: Surveillance footage and demonstrations

### Test Scenarios

Predefined test scenarios for different use cases:
- **Simple Case**: Basic civil case with 2 evidence items
- **Complex Case**: Criminal case with 10+ evidence items
- **Demonstrative Case**: High-accuracy civil case
- **Sandbox Case**: Experimental criminal case with AI assistance

## Continuous Integration

### GitHub Actions Integration

Tests are designed to run in CI environments:
- **Parallel Execution**: Tests run in parallel for faster CI
- **Artifact Collection**: Test reports and coverage data
- **Matrix Testing**: Multiple Python versions and environments
- **Performance Baselines**: Regression detection for performance tests

### Test Reports

Multiple report formats:
- **Terminal**: Colored output with timing information
- **HTML**: Interactive reports with screenshots
- **XML**: JUnit format for CI integration
- **Coverage**: HTML and XML coverage reports

## Best Practices

### Writing Tests

1. **Isolation**: Each test should be independent
2. **Deterministic**: Tests should produce consistent results
3. **Fast**: Unit tests should run quickly
4. **Clear**: Test names and assertions should be descriptive
5. **Comprehensive**: Cover edge cases and error conditions

### Test Organization

1. **Arrange-Act-Assert**: Clear test structure
2. **Fixtures**: Reuse common test setup
3. **Parametrization**: Test multiple scenarios efficiently
4. **Mocking**: Isolate units under test
5. **Documentation**: Document complex test scenarios

### Performance Testing

1. **Baselines**: Establish performance baselines
2. **Monitoring**: Track memory and CPU usage
3. **Regression**: Detect performance regressions
4. **Load Testing**: Simulate realistic user loads
5. **Resource Limits**: Test within resource constraints

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Timeout Issues**: Increase timeout for slow tests
3. **Memory Issues**: Monitor memory usage in performance tests
4. **Flaky Tests**: Make tests deterministic and isolated
5. **Coverage Gaps**: Add tests for uncovered code paths

### Debug Mode

Run tests with debug output:
```bash
pytest -v -s --log-cli-level=DEBUG
```

### Test Isolation

Run tests in isolation to identify issues:
```bash
pytest tests/integration/test_evidence_pipeline.py::TestEvidencePipeline::test_document_processing_flow -v
```

## Coverage Goals

- **Overall Coverage**: >90%
- **Critical Paths**: 100% (evidence processing, rendering, compliance)
- **New Code**: 100% coverage required
- **Legacy Code**: >80% coverage maintained

## Test Maintenance

### Regular Tasks

1. **Update Dependencies**: Keep test dependencies current
2. **Review Coverage**: Identify and fill coverage gaps
3. **Performance Baselines**: Update performance expectations
4. **Test Data**: Refresh test data and scenarios
5. **Documentation**: Keep test documentation current

### Test Review

1. **Code Reviews**: All test code must be reviewed
2. **Coverage Analysis**: Review coverage reports regularly
3. **Performance Monitoring**: Track test execution times
4. **Flaky Test Detection**: Identify and fix unstable tests
5. **Test Effectiveness**: Measure test effectiveness and value

This comprehensive test suite ensures the Legal Simulation Platform maintains high quality, reliability, and compliance with legal requirements.
