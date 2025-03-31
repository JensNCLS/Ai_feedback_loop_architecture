# Ai_feedback_loop_architecture

Developing a software architecture which allows implementation of a human-in-the-loop AI feedback loop and complies with GDPR and EU AI Act standards.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)

## Overview

This project aims to create a robust architecture for AI systems that integrates human feedback into the model retraining process. The architecture is designed to ensure compliance with the EU AI Act.

## Features

- **Human-in-the-Loop Feedback**: Allows users to provide feedback on AI predictions to improve model performance.
- **Model Retraining**: Automates the retraining process based on user feedback.
- **(Partial) EU AI Act Compliance**: Ensures every process is logged.
- **Architecture**: Modular design with separate services for backend, frontend, database, and AI models.
- **MLflow Integration**: Tracks experiments, models, and artifacts.

## Project Structure

The project is organized as follows:

```
Ai_feedback_loop_architecture/
├── backend/          # Backend service (Django REST API)
├── frontend/         # Frontend service (React application)
├── ai_models/        # AI models and training scripts
├── database/         # Database configuration and migrations
├── mlflow/           # MLflow tracking server setup
├── docker-compose.yml # Docker Compose configuration
└── README.md         # Project documentation
```

## Setup Instructions

### Prerequisites

- Docker and Docker Compose installed
- Node.js and npm installed (for frontend development)
- Python 3.12 installed (for backend development)

### Steps

1. Clone the repository:
```zsh
   git clone <repository>
   cd Ai_feedback_loop_architecture
```

2. Build and start the services:
```zsh
    docker-compose up --build
```

3. Apply database migrations:
```zsh
    docker exec -it django-backend bash
    python manage.py makemigrations
    python manage.py migrate
```

4. Access the services:

 - **Frontend:** http://localhost:3000
 - **Backend:** http://localhost:8000
 - **MLflow:** http://localhost:5001
 - **pgAdmin:** http://localhost:5050


