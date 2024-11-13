# 🤖 RootBot (Smolit_AdminBot)

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/EcoSphereNetwork/Smolit_AdminBot)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-yellow.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

An intelligent, autonomous system administration bot powered by Python and Mozilla's Llama 3.2 1B LLM technology. RootBot monitors, manages, and optimizes your system resources while providing intelligent insights and automated responses to system events.

## 📋 Table of Contents
- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
  - [Standard Installation](#standard-installation)
  - [Docker Installation](#docker-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Development](#-development)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🔍 System Monitoring
- Real-time CPU, memory, and disk usage tracking
- Network traffic and connection monitoring
- Process management with resource limits
- Anomaly detection and alerting
- Customizable monitoring intervals
- Resource threshold configuration

### 🧠 Intelligent Decision Making
- LLM-powered system analysis using Mozilla's Llama 3.2 1B model
- Automated resource optimization
- Predictive maintenance
- Smart task prioritization
- Context-aware command evaluation
- Adaptive resource management

### 🛡️ Security
- Command whitelisting and blacklisting
- Secure execution environment
- Permission-based access control
- Comprehensive audit logging
- Secure command validation
- Resource usage limits

### 💾 Memory Management
- Short-term and long-term memory systems
- Priority-based event storage
- Automatic memory compaction
- Persistent state management
- Configurable retention policies
- Memory optimization

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

## 🚀 Installation

### Standard Installation

1. Clone the repository:

2. Create a virtual environment (recommended):

