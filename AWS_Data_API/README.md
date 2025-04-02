# AWS Data API Portfolio

This repository contains a collection of AWS-related projects and examples for working with cloud services, APIs, and data processing.

## Contents

### Jupyter Notebooks

#### [AssessingAPIData.ipynb](./AssessingAPIData.ipynb)
- **Description**: Notebook for assessing and analyzing data obtained from various APIs.
- **Technologies**: Python, API integration, data analysis

#### [IPAddressValidationAndGeolocation.ipynb](./IPAddressValidationAndGeolocationChallenge.ipynb)
- **Description**: Implements IP address validation and geolocation services.
- **Features**: 
  - IP validation using both Python ipaddress module and regex
  - IPv4 and IPv6 validation
  - IP geolocation using Abstract API
  - API key management with dotenv

#### [Lambda_funct.ipynb](./Lambda_funct.ipynb)
- **Description**: AWS Lambda function implementation for mathematical operations.
- **Features**:
  - Serverless mathematical operations
  - Input validation
  - Error handling
  - API Gateway integration

#### [Lambda_S3.ipynb](./Lambda_S3.ipynb)
- **Description**: Integration of AWS Lambda with S3 storage.
- **Technologies**: AWS Lambda, S3, Python

#### [Reading_from_and_saving_to_S3.ipynb](./Reading_from_and_saving_to_S3.ipynb)
- **Description**: Example of reading and writing data to AWS S3 buckets.
- **Features**:
  - S3 object listing
  - Reading CSV files from S3
  - Authentication with AWS credentials

### AWS_Data_API_project Folder

This folder contains a comprehensive AWS Data API project with the following components:

#### Documentation
- [List of information about project.docx](./AWS_Data_API_project/List%20of%20information%20about%20project.docx)
- [Test from Postman.docx](./AWS_Data_API_project/Test%20from%20Postman.docx) - API testing documentation using Postman
- [Test in AWS.docx](./AWS_Data_API_project/Test%20in%20AWS.docx) - AWS testing procedures and results
- [Test plan.docx](./AWS_Data_API_project/Test%20plan.docx) - Testing methodology and plan
- [Vulnerabilities and cybersecurity concerns.docx](./AWS_Data_API_project/Vulnerabilities%20and%20cybersecurity%20concerns.docx) - Security analysis

#### Implementation
- [Project-backend-only.ipynb](./AWS_Data_API_project/Project-backend-only.ipynb) - Backend implementation
- [Python-Project.ipynb](./AWS_Data_API_project/Python-Project.ipynb) - Main project implementation
- [project.zip](./AWS_Data_API_project/project.zip) - Packaged project files

## Technologies Used

- **AWS Services**: Lambda, S3, API Gateway
- **Programming Languages**: Python
- **Data Formats**: JSON, CSV
- **Tools**: Jupyter Notebooks, Postman
- **Libraries**: boto3, requests, ipaddress, python-dotenv

## Getting Started

1. Ensure you have AWS credentials configured
2. Install required dependencies:
   ```
   pip install boto3 requests python-dotenv
   ```
3. Open the desired notebook in Jupyter
4. For notebooks requiring API keys, create a `.env` file with your credentials

## Security Note

Some notebooks may contain placeholders for AWS credentials, for example. Never commit actual AWS credentials to version control. Use environment variables or AWS credential management best practices. 