# SYNSPEC Modernization Project (iSynspec)

## Overview
This project aims to modernize the SYNSPEC spectral synthesis program by creating a modern Python interface around the existing Fortran codebase. The goal is to make SYNSPEC more accessible to modern astronomers while preserving its robust computational core.

## Project Goals

### Phase 1: Core Python Library (isynspec)
1. Create a Python wrapper library that:
   - [✓] Handles all fort.n file I/O operations transparently
   - [✓] Manages SYNSPEC execution and configuration
   - [✓] Provides a clean, intuitive API for interacting with SYNSPEC
   - [✓] Processes and returns results in modern data formats (e.g., numpy arrays)

2. Implement core functionality:
   - [✓] Input file generation and validation
   - [✓] Configuration file management
   - [✓] SYNSPEC execution control
   - [✓] Output file parsing and data extraction
   - [In Progress] Error handling and logging
   - [In Progress] Documentation and type hints

3. Create data structures for:
   - [✓] Model atmosphere parameters (via fort.8 and input handling)
   - [✓] Atomic and molecular line lists (Line class, Fort19)
   - [✓] Spectral synthesis parameters (Fort55, Fort56)
   - [✓] Output spectra (Fort7, Fort17)

### Phase 2: Additional Features
1. Data Visualization:
   - [TODO] Built-in plotting capabilities using matplotlib
   - [TODO] Interactive spectrum visualization

2. Documentation and Examples:
   - [In Progress] Type hints and docstrings
   - [TODO] API documentation with Sphinx
   - [TODO] Quick-start guide
   - [TODO] Jupyter notebook tutorials
   - [TODO] Example scripts for common tasks
   - [TODO] Migration guide from original SYNSPEC

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
│   ├── session.py         # Main SYNSPEC session management
│   └── config.py          # Configuration management
├── io/
│   ├── input.py          # Model input handling
│   ├── execution.py      # SYNSPEC execution
│   ├── workdir.py        # Working directory management
│   ├── line.py          # Spectral line data structure
│   ├── fort7.py         # Spectrum output handling
│   ├── fort16.py        # Equivalent widths
│   ├── fort17.py        # Continuum data
│   ├── fort19.py        # Line list handling
│   ├── fort55.py        # Synthesis parameters
│   └── fort56.py        # Abundance changes
├── models/              # Future model abstractions
├── utils/
│   └── fortio.py       # Fortran I/O utilities
└── tests/              # Comprehensive test suite
    ├── test_*.py      # Unit and integration tests
    ├── conftest.py    # pytest configuration
    └── data/          # Test data files
```

## Testing Strategy

### Test-Driven Development Approach
1. Unit Testing
   - [✓] Use pytest for test framework
   - [✓] Test each component in isolation
   - [✓] Write tests before implementing features
   - [✓] Implement test fixtures and data
   - [In Progress] Expand test coverage (current: ~80%)

2. Integration Testing
   - [✓] Test interactions between components
   - [✓] Verify SYNSPEC input/output handling
   - [✓] Test file I/O operations
   - [TODO] Test full workflow scenarios
   - [TODO] Add performance benchmarks

3. Test Data Management
   - [✓] Maintain suite of test input files (test_model.5, test_model.7)
   - [✓] Test data for fort.n files
   - [✓] Version controlled test data
   - [In Progress] Document test data format and usage

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
  - NumPy: Array operations for spectra and line lists
  - typing_extensions: Enhanced type hints
  - dataclasses: Data structure definitions
  - pathlib: Path operations
  - pytest: Testing framework
  - Fortran compiler (gfortran)

- Optional dependencies:
  - Pandas: Dataframe exports (fort.19)
  - Matplotlib: Future plotting capabilities
  - Jupyter: Future interactive examples
  - Streamlit/PyQt: Future GUI development

## Development Roadmap

1. Initial Setup (1-2 weeks)
   - [✓] Project structure and build system
   - [✓] Testing framework setup
   - [✓] Initial test suite configuration
   - [In Progress] Basic SYNSPEC integration with tests

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
   - [TODO] Parallel processing for batch calculations
   - [TODO] Caching of intermediate results
   - [TODO] Memory-efficient line list handling
   - [TODO] Optimized file I/O operations

2. Additional Features
   - [TODO] Integration with astropy
   - [TODO] Support for Kurucz/ATLAS model atmospheres
   - [TODO] Support for MARCS model atmospheres
   - [TODO] Batch processing for parameter grids
   - [TODO] Line list management tools
   - [TODO] Model atmosphere interpolation

3. Community Building
   - [TODO] Documentation website
   - [TODO] Contributing guidelines
   - [TODO] Issue templates
   - [TODO] CI/CD pipeline setup
   - [TODO] Package distribution (PyPI)
   - [TODO] Example gallery
