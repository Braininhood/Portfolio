# C Programming Projects

This repository contains a collection of C programming projects demonstrating various algorithms, data structures, and programming concepts.

## Projects

### Basic Programs
- **[hello](./hello/)**: Simple "Hello, World" program using CS50 library for string input.

### Console Applications
- **[cash](./cash/)**: Program that calculates the minimum number of coins needed to make change.
- **[credit](./credit/)**: Credit card number validator using Luhn's algorithm.
- **[mario1](./mario1/)**: Program that prints a half-pyramid pattern using hashes.
- **[mario2](./mario2/)**: Extension of mario1 that prints a full double pyramid pattern.
- **[readability](./readability/)**: Text readability calculator using the Coleman-Liau index.
- **[scrabble](./scrabble/)**: Program that calculates Scrabble scores for words.

### Cryptography
- **[caesar](./caesar/)**: Implementation of Caesar's cipher for text encryption.
- **[substitution](./substitution/)**: Encryption program using a substitution cipher.

### Memory Management
- **[filter-less](./filter-less/)**: Simple image filtering program with grayscale, sepia, reflection, and blur filters.
- **[filter-more](./filter-more/)**: Advanced image filtering program that adds edge detection.
- **[recover](./recover/)**: JPEG recovery tool that recovers deleted images from a memory card.
- **[speller](./speller/)**: Spell-checking program using a hash table for dictionary storage.
- **[volume](./volume/)**: Audio file volume adjustment program.

### Algorithms
- **[plurality](./plurality/)**: Simple voting system using the plurality method (first-past-the-post).
- **[runoff](./runoff/)**: Ranked-choice voting system implementation.
- **[tideman](./tideman/)**: Implementation of the Tideman voting algorithm (ranked pairs).

### Data Structures
- **[inheritance](./inheritance/)**: Genetic inheritance simulation using structures and dynamic memory allocation.
- **[sort](./sort/)**: Implementation and comparison of different sorting algorithms.
- **[world](./world/)**: World simulation or mapping program.

## Project Structure

Most projects follow this structure:
- Main source file (e.g., `speller.c`) - Contains the program entry point
- Header files (e.g., `dictionary.h`) - Contains function prototypes and type definitions
- Implementation files (e.g., `dictionary.c`) - Contains the implementation of functions
- Additional resource files when needed (test files, data files, Makefiles)

## Key Concepts Demonstrated

- Memory management and pointers
- File I/O operations
- Command-line argument parsing
- Data structures (arrays, linked lists, hash tables)
- Algorithm implementation
- Bitwise operations
- Image processing

## Technologies Used

- C Programming Language
- Standard C libraries (stdio.h, stdlib.h, string.h, etc.)
- Make build system

## Getting Started

1. Clone the repository
2. Navigate to any project directory
3. Compile the project using gcc or make:
   ```
   gcc -o program_name source_file.c
   ```
   or
   ```
   make
   ```
4. Run the compiled program:
   ```
   ./program_name [command_line_arguments]
   ```

## Requirements

- GCC compiler or compatible C compiler
- CS50 library (for some projects)
- Make (for projects with Makefiles) 