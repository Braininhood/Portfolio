# Software Testing Projects and Tutorials

This directory contains a collection of testing projects, test suites, and tutorial notebooks demonstrating various software testing techniques and concepts.

## Project Overview

### Python Unit Testing Projects

Each project folder contains a Python module and its corresponding test suite:

**Text Processing Projects:**
- **test_twttr**: Tests a function that removes vowels from text
  - `twttr.py`: The module containing the `shorten` function
  - `test_twttr.py`: Test suite verifying the vowel removal functionality

**Input Validation Projects:**
- **test_plates**: Tests license plate validation functions
  - `plates.py`: License plate validation code
  - `test_plates.py`: Test suite for license plate validation

- **test_fuel**: Tests a fuel gauge reading function
  - `fuel.py`: The module containing fuel gauge percentage calculation
  - `test_fuel.py`: Tests for validating fuel gauge readings

- **numb3rs**: Tests an IPv4 address validation function using regex
  - `numb3rs.py`: IPv4 validation code using regular expressions
  - `test_numb3rs.py`: Test suite for IPv4 validation

**Date and Time Projects:**
- **seasons**: Tests age calculation and time formatting functions
  - `seasons.py`: Module for calculating and formatting time
  - `test_seasons.py`: Test suite for age and time format functions

**Financial Applications:**
- **test_bank**: Tests a greeting value calculation function
  - `bank.py`: Module for determining values based on greeting types
  - `test_bank.py`: Test suite verifying greeting calculations

**Miscellaneous Testing Projects:**
- **jar**: Tests a cookie jar simulation
- **um**: Tests a word counting function
- **working**: Tests working hours format validation

## Jupyter Notebook Tutorials

The folder also contains comprehensive Jupyter notebooks on software testing concepts:

- **TestingSoftware.ipynb**: Introduction to software testing concepts
  - Database connection testing
  - Data validation
  - Testing scenarios and edge cases
  - Error handling and exception testing

- **TestingSoftwareAutomation.ipynb**: Automated testing techniques
  - Test automation frameworks
  - Continuous integration concepts
  - Automating test suites
  - Reporting and metrics

- **TestingAutomation2.ipynb**: Advanced test automation
  - Performance testing
  - Security testing
  - Integration testing strategies
  - Testing best practices

## Testing Techniques Demonstrated

These projects and tutorials demonstrate a variety of testing techniques:

### Unit Testing
- Testing individual functions and methods
- Isolating components for testing
- Handling edge cases and boundary values

### Test-Driven Development (TDD)
- Writing tests before implementation
- Iterative development based on test results

### Testing Methodologies
- Black box testing
- White box testing
- Integration testing
- Regression testing

### Test Case Design
- Equivalence partitioning
- Boundary value analysis
- Error guessing
- Decision tables

## Getting Started

To run the Python test suites:

1. Navigate to the desired project folder
2. Run tests using pytest:
   ```
   pytest test_numb3rs.py -v
   ```
   
To explore the Jupyter notebooks:
1. Start Jupyter Notebook or Jupyter Lab
2. Open any of the tutorial notebooks to learn about testing concepts

## Skills Demonstrated

These projects demonstrate proficiency in:
- Writing effective unit tests
- Designing test cases for various scenarios
- Implementing test automation
- Working with testing frameworks (pytest)
- Using assertions effectively
- Testing data validation and error handling
- Implementing test-driven development 