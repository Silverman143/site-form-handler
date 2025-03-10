# Site Form Handler

## Overview

Site Form Handler is a robust, lightweight Flask application designed to process and manage form submissions from websites. It provides a unified API endpoint for handling various types of web forms, with seamless notification delivery through Telegram and email channels. The service is containerized with Docker for easy deployment and scalability.

## Key Features

- **Universal Form Endpoint**: Process any JSON-formatted form data through a single, consistent API
- **Multi-channel Notifications**: Deliver form submissions via Telegram messages and/or email
- **Customizable Templates**: Easily configure the format of notification messages
- **Spam Protection**: Built-in rate limiting to prevent form abuse
- **Detailed Logging**: Comprehensive logging of form submissions for auditing and analysis
- **CORS Support**: Configurable Cross-Origin Resource Sharing for secure front-end integration
- **Health Monitoring**: Endpoint for checking service status and component health
- **Docker Integration**: Simple deployment with Docker and Docker Compose

## Technical Stack

- **Backend**: Python, Flask
- **Notifications**: Telegram Bot API, SMTP Email
- **Configuration**: Environment variables with dotenv support
- **Containerization**: Docker, Docker Compose
- **Security**: CORS protection, rate limiting

## Quick Start

1. Clone the repository
2. Configure your environment variables in a `.env` file (see `.env.example`)
3. Run with Docker Compose:
   ```docker-compose up -d```
4. The service will be available at `http://localhost:8080` (or your configured port)

## API Endpoints

- **POST /api/form-submit**: Main endpoint for form submissions
- **POST /api/contact**: Legacy endpoint for backward compatibility
- **GET /api/health**: Service health check endpoint

## Configuration

All configuration is managed through environment variables, which can be set in a `.env` file or directly in the environment. See `.env.example` for a complete list of available configuration options.

## Deployment

The application is designed to be deployed as a Docker container, making it suitable for various hosting environments including cloud providers, Kubernetes clusters, or traditional VPS servers.

## License

[MIT License](LICENSE)
