# Flask Projects

This directory contains Flask-based web applications and microservices demonstrating various Flask features and architectural patterns.

## Projects

### [jmgdo-microservices](./jmgdo-microservices/)

A comprehensive microservices project showcasing different Flask implementations and API patterns.

**Project Structure:**

#### CRUD Application (`/CRUD/`)
- **Description**: Basic Flask application demonstrating CRUD (Create, Read, Update, Delete) operations
- **Features**:
  - RESTful API endpoints for product management
  - Static file serving
  - Basic Flask routing and request handling
- **Technologies**: Flask, Python
- **Files**:
  - `products.py` - Main application with CRUD operations
  - `static/` - Static assets directory

#### Swagger API Documentation (`/swagger_example/`)
- **Description**: Flask application with integrated Swagger/OpenAPI documentation
- **Features**:
  - Automatic API documentation generation
  - Interactive API testing interface
  - Multiple configuration formats (JSON and YAML)
  - RESTful API endpoints with proper documentation
- **Technologies**: Flask, Swagger/OpenAPI, Flask-RESTx
- **Files**:
  - `app.py` - Main Flask application with Swagger integration
  - `swagger_config.json` - Swagger configuration in JSON format
  - `swagger_config.yml` - Swagger configuration in YAML format

#### GraphQL Example (`/graphql_example/`)
- **Description**: GraphQL server implementation using Node.js for comparison with Flask REST APIs
- **Features**:
  - GraphQL schema definition and resolvers
  - US cities data querying
  - Docker containerization support
  - Flexible data querying capabilities
- **Technologies**: Node.js, GraphQL, Docker
- **Files**:
  - `graphserver.js` - GraphQL server implementation
  - `package.json` - Node.js dependencies
  - `UScities.json` - Sample dataset with US cities information
  - `Dockerfile` - Container configuration

## Key Features Demonstrated

### Flask Web Development
- **Routing**: URL routing and request handling
- **Static Files**: Serving static assets (CSS, JS, images)
- **RESTful APIs**: Building REST API endpoints
- **Request Processing**: Handling different HTTP methods (GET, POST, PUT, DELETE)

### API Documentation
- **Swagger Integration**: Automatic API documentation generation
- **Interactive Testing**: Built-in API testing interface
- **Multiple Formats**: Support for JSON and YAML configuration
- **OpenAPI Standards**: Following OpenAPI specification

### Microservices Architecture
- **Service Separation**: Different services for different functionalities
- **API Gateway Patterns**: Centralized API management
- **Documentation Standards**: Consistent API documentation across services
- **Containerization**: Docker support for deployment

### Alternative Technologies
- **GraphQL**: Comparison between REST and GraphQL approaches
- **Node.js Integration**: Multi-language microservices architecture
- **Data Management**: Handling large datasets efficiently

## Getting Started

### Prerequisites
- Python 3.7+
- Flask
- Node.js (for GraphQL example)
- Docker (optional, for containerized deployment)

### Running the CRUD Application
1. Navigate to the CRUD directory:
   ```bash
   cd Flask/jmgdo-microservices/CRUD
   ```

2. Install Flask if not already installed:
   ```bash
   pip install flask
   ```

3. Run the application:
   ```bash
   python products.py
   ```

### Running the Swagger Example
1. Navigate to the swagger_example directory:
   ```bash
   cd Flask/jmgdo-microservices/swagger_example
   ```

2. Install required dependencies:
   ```bash
   pip install flask flask-restx
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Access the Swagger UI at `http://localhost:5000/`

### Running the GraphQL Example
1. Navigate to the graphql_example directory:
   ```bash
   cd Flask/jmgdo-microservices/graphql_example
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Run the GraphQL server:
   ```bash
   node graphserver.js
   ```

4. Access the GraphQL playground at `http://localhost:4000/graphql`

### Docker Deployment (GraphQL Example)
1. Build the Docker image:
   ```bash
   docker build -t graphql-server .
   ```

2. Run the container:
   ```bash
   docker run -p 4000:4000 graphql-server
   ```

## API Endpoints

### CRUD Application
- `GET /products` - Retrieve all products
- `POST /products` - Create a new product
- `PUT /products/<id>` - Update a product
- `DELETE /products/<id>` - Delete a product

### Swagger Example
- Interactive documentation available at the root URL
- All endpoints documented with request/response schemas
- Built-in testing interface

### GraphQL Example
- Single endpoint: `/graphql`
- Flexible querying based on GraphQL schema
- Support for complex data relationships

## Technologies Used

- **Backend**: Flask, Python, Node.js
- **API Documentation**: Swagger/OpenAPI, Flask-RESTx
- **Data Query**: GraphQL
- **Containerization**: Docker
- **Data Formats**: JSON, YAML
- **Development Tools**: npm, pip

## License

This project is licensed under the MIT License - see the [LICENSE](./jmgdo-microservices/LICENSE) file for details. 