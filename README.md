# Smolit_AdminBot

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/EcoSphereNetwork/Smolit_AdminBot)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-yellow.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

A robust, AI-powered system administration bot with advanced monitoring, security, and self-healing capabilities.

## 📋 Table of Contents
- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
  - [Standard Installation](#standard-installation)
  - [Docker Installation](#docker-installation)
- [Configuration](#-configuration)
  - [Basic Configuration](#basic-configuration)
  - [Advanced Configuration](#advanced-configuration)
  - [Security Settings](#security-settings)
  - [LLM Configuration](#llm-configuration)
- [Usage](#-usage)
  - [Basic Usage](#basic-usage)
  - [Advanced Features](#advanced-features)
  - [API Endpoints](#api-endpoints)
- [Development](#-development)
  - [Setting Up Dev Environment](#setting-up-dev-environment)
  - [Code Style Guide](#code-style-guide)
  - [Making Changes](#making-changes)
- [Testing](#-testing)
  - [Running Tests](#running-tests)
  - [Writing Tests](#writing-tests)
  - [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#-troubleshooting)
  - [Common Issues](#common-issues)
  - [Debug Mode](#debug-mode)
  - [Logs](#logs)
- [Contributing](#-contributing)
  - [Contribution Process](#contribution-process)
  - [Code Review Process](#code-review-process)
- [License](#-license)
- [Support](#-support)

## Features

### Security
- File integrity monitoring with SHA-256 verification
- AppArmor profile for sandboxed operation
- Input validation and sanitization
- Structured security audit logging
- Automated security scanning

### Monitoring
- Real-time system resource monitoring
- File system change detection
- Process health checking
- ML-based anomaly detection
- Comprehensive event logging

### Reliability
- Watchdog process monitoring
- Automatic process recovery
- Retry mechanisms with exponential backoff
- Task persistence and recovery
- Structured error handling

### Management
- Advanced CLI interface
- JSON-structured logging
- Resource usage analytics
- Configuration management
- Automated maintenance

## 📦 Requirements

### System Requirements
- Linux-based operating system (Ubuntu 20.04+ recommended)
- Python 3.10 or higher
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space
- Root/sudo privileges

### Python Dependencies
- psutil>=5.9.0
- requests>=2.25.0
- python-daemon>=2.3.0
- numpy>=1.24.0
- torch>=2.0.0
- transformers>=4.36.0

### Optional Requirements
- Docker 20.10+ (for containerized deployment)
- NVIDIA GPU with CUDA support (for improved LLM performance)

## Installation
Standard Installation

Clone the repository:
  
    git clone https://github.com/EcoSphereNetwork/Smolit_AdminBot.git
    cd Smolit_AdminBot

Install Python dependencies:

    pip install -r requirements.txt

Run the bot:

    python rootbot-cli.py

Docker Installation

Ensure Docker and Docker Compose are installed.

Build and start the container:

    docker-compose up --build

Access the bot interface via the CLI or API:

    docker exec -it smolit_adminbot python rootbot-cli.py

Stop the container:

    docker-compose down

Usage
Basic Usage

Run the bot in CLI mode:

    python rootbot-cli.py

Advanced Features

  - **Configuration:** Use the rootbot.conf file to customize bot settings.
  - **Monitoring:** Run watchdog.py to monitor system health and generate reports.
  - **Testing:** Execute test_bot.py for system checks:

        python test_bot.py

Contributing

Contributions are welcome! To contribute:

    Fork the repository.
    Create a feature branch:

git checkout -b feature-name

Commit your changes:

git commit -m "Feature description"

Push the branch:

    git push origin feature-name

    Submit a Pull Request.

Refer to the CONTRIBUTING.md file for more details.
License

Smolit_AdminBot is licensed under the MIT License.
Support

For issues or feedback, please open an issue in the GitHub repository.


