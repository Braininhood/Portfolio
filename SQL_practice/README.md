# SQL Practice Projects

This directory contains a collection of SQL practice projects demonstrating various database query techniques and SQL skills.

## Projects Overview

### Songs Database Project
**Location:** [songs/](./songs/)

A project focused on querying a music database containing information about popular songs.

**Files:**
- `songs.db`: SQLite database containing song data (titles, artists, tempo, etc.)
- `1.sql` to `8.sql`: A series of SQL query files with increasing complexity
- `answers.txt`: Contains the expected output of each query for reference

**Skills Demonstrated:**
- Basic SELECT queries
- Sorting with ORDER BY
- Filtering with WHERE clause
- Aggregate functions (COUNT, AVG, etc.)
- Data grouping and filtering
- Query optimization

**Example Queries:**
- Retrieving all song names
- Sorting songs by tempo
- Filtering songs by specific attributes
- Calculating average tempo

### Movies Database Project
**Location:** [movies/](./movies/)

A project centered around querying a movie database containing information about films, actors, ratings, and more.

**Files:**
- `1.sql` to `13.sql`: A series of SQL query files with progressively complex requirements

**Skills Demonstrated:**
- Basic SELECT queries
- Joining multiple tables
- Complex filtering conditions
- Subqueries and nested queries
- Aggregate functions with grouping
- Working with date/time data
- Advanced query techniques

**Example Queries:**
- Finding movies from a specific year
- Identifying movies with particular ratings
- Finding collaborations between actors and directors
- Complex analytics on movie performance

## Getting Started

To execute these SQL queries:

1. Ensure you have SQLite installed on your system
2. Navigate to the project directory (songs or movies)
3. Run queries using the SQLite command line:
   ```
   sqlite3 songs.db < 1.sql
   ```
   or
   ```
   sqlite3 movies.db < 1.sql
   ```

## Learning Path

These projects are designed to build SQL skills progressively:

1. Start with the basic queries in the songs project (1.sql - 3.sql)
2. Progress to more complex filtering and sorting (4.sql - 6.sql)
3. Move to the movies project for advanced concepts like:
   - Multi-table joins
   - Subqueries
   - Complex filtering
   - Advanced aggregations

## Skills Demonstrated

These projects demonstrate proficiency in:
- Writing efficient SQL queries
- Database schema understanding
- Data filtering and sorting
- Aggregating and summarizing data
- Working with relational database concepts
- Query optimization techniques
- Complex data analysis using SQL 