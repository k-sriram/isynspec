# SYNSPEC Modernization Project (iSynspec)

## Overview
This project aims to modernize the SYNSPEC spectral synthesis program by creating a modern Python interface around the existing Fortran codebase. The goal is to make SYNSPEC more accessible to modern astronomers while preserving its robust computational core.

## Project Goals

### Phase 1: Core Python Library (isynspec)
1. Create a Python wrapper library that:
   - Provides a clean, intuitive API for interacting with SYNSPEC
   - Handles all fort.n file I/O operations transparently
   - Manages SYNSPEC execution and configuration
   - Processes and returns results in modern data formats (e.g., numpy arrays, pandas DataFrames)

2. Implement core functionality:
   - Input file generation and validation
   - Configuration file management
   - SYNSPEC execution control
   - Output file parsing and data extraction
   - Error handling and logging

3. Create data structures for:
   - Model atmosphere parameters
   - Atomic and molecular line lists
   - Spectral synthesis parameters
   - Output spectra

### Phase 2: Additional Features
1. Data Visualization:
   - Built-in plotting capabilities using matplotlib
   - Interactive spectrum visualization
   - Comparison tools for observed vs. synthetic spectra

2. Documentation and Examples:
   - Comprehensive API documentation
   - Jupyter notebook tutorials
   - Example scripts for common use cases
   - Migration guide for existing SYNSPEC users

### Phase 3: GUI Development (Future)
1. Create a graphical interface that:
   - Provides easy access to all library features
   - Offers interactive parameter adjustment
   - Displays real-time spectrum visualization
   - Supports batch processing

2. Consider implementation options:
   - Web-based interface (e.g., Streamlit, Dash)
   - Desktop application (e.g., PyQt, wxPython)
   - VS Code extension

## Technical Architecture

### Core Library Structure
```
isynspec/
├── __init__.py
├── core/
│   ├── synspec.py          # Main SYNSPEC interface
│   ├── config.py           # Configuration management
│   └── runner.py          # SYNSPEC execution handling
├── io/
│   ├── input_handler.py    # Input file generation
│   ├── output_handler.py   # Output file parsing
│   └── fort_files.py       # Fort.n file management
├── models/
│   ├── atmosphere.py       # Atmosphere model classes
│   ├── linelist.py         # Line list management
│   └── spectrum.py         # Spectrum data structures
├── utils/
│   ├── validators.py       # Input validation
│   ├── converters.py       # Data format conversion
│   └── plotting.py         # Visualization utilities
├── tests/                  # Test suite
│   ├── unit/              # Unit tests matching package structure
│   ├── integration/       # End-to-end and integration tests
│   ├── fixtures/          # Test data and mock objects
│   └── conftest.py        # pytest configuration
└── gui/                    # Future GUI components
```

## Testing Strategy

### Test-Driven Development Approach
1. Unit Testing
   - Write tests before implementing features
   - Test each component in isolation
   - Use pytest for test framework
   - Implement mock SYNSPEC responses for testing
   - Maintain high test coverage (target: 90%+)

2. Integration Testing
   - Test interactions between components
   - Verify SYNSPEC input/output handling
   - Test full workflow scenarios
   - Include performance benchmarks

3. Test Data Management
   - Maintain suite of test input files
   - Create mock SYNSPEC outputs
   - Version control test data
   - Document test data format and usage

4. Continuous Integration
   - Automated test runs on commits
   - Coverage reports
   - Performance regression testing
   - Cross-platform testing (Linux, Windows, macOS)

5. Testing Tools
   - pytest: Test framework
   - pytest-cov: Coverage reporting
   - pytest-benchmark: Performance testing
   - pytest-mock: Mocking framework
   - tox: Test automation and environment management

### Dependencies
- Core dependencies:
  - NumPy: Numerical computations
  - Pandas: Data management
  - Matplotlib: Plotting
  - PyYAML: Configuration handling
  - Click: CLI interface
  - Fortran compiler (gfortran)

- Optional dependencies:
  - Jupyter: Interactive examples
  - Streamlit/PyQt: Future GUI development

## Development Roadmap

1. Initial Setup (1-2 weeks)
   - Project structure and build system
   - Testing framework setup
   - Initial test suite configuration
   - Basic SYNSPEC integration with tests

2. Core Functionality (4-6 weeks)
   - Test-driven development of:
     * File I/O systems
     * SYNSPEC execution
     * Basic data structures
   - Continuous integration setup
   - Test coverage monitoring

3. Advanced Features (4-6 weeks)
   - Test-first development of:
     * Visualization tools
     * API endpoints
   - Integration test suite expansion
   - Performance benchmark creation
   - Documentation and example notebooks

4. GUI Development (Future)
   - Interface design
   - Test-driven UI component development
   - End-to-end testing
   - User acceptance testing

## Best Practices

1. Code Quality and Testing
   - Follow PEP 8 style guide
   - Type hints for better IDE support
   - Comprehensive docstrings
   - Write tests before implementation (TDD)
   - No pull requests without tests
   - Maintain test coverage above 90%
   - Regular performance benchmark runs

2. Version Control
   - Git for source control
   - Semantic versioning
   - Feature branches
   - Pull request reviews

3. Documentation
   - API documentation using Sphinx
   - README with quick start guide
   - Contributing guidelines
   - Change log

## Installation and Distribution

1. Package Distribution
   - PyPI package
   - Conda package (optional)
   - Docker container (optional)

2. Installation Requirements
   - Python 3.10+
   - Fortran compiler
   - Required libraries

## Future Considerations

1. Performance Optimization
   - Parallel processing for batch calculations
   - Caching mechanisms
   - Memory optimization

2. Additional Features
   - Integration with other astronomical tools
   - Support for different model atmosphere formats
   - Batch processing capabilities

3. Community Building
   - User feedback system
   - Contributing guidelines
   - Regular updates and maintenance
