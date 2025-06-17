# Ai_feedback_loop_architecture

Developing a software architecture which allows implementation of a human-in-the-loop AI feedback loop and complies with GDPR and EU AI Act standards.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Training & Evaluation](#training--evaluation)

## Overview

This project aims to create a robust architecture for AI systems that integrates human feedback into the model retraining process. The architecture is designed to ensure compliance with the EU AI Act.

## Features

- **Human-in-the-Loop Feedback**: Allows users to provide feedback on AI predictions to improve model performance.
- **Model Retraining**: Automates the retraining process based on user feedback.
- **K-fold Cross-validation**: Enables more robust model evaluation through k-fold cross-validation.
- **(Partial) EU AI Act Compliance**: Ensures every process is logged.
- **Architecture**: Modular design with separate services for backend, frontend, database, and AI models.
- **MLflow Integration**: Tracks experiments, models, and artifacts.
- **DVC Integration**: AI Pipeline and data versioning

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
 - **MiniO** http://localhost:9001

## Training & Evaluation

### Standard Training

To run the standard model training pipeline using DVC:

```zsh
docker exec -it django-backend bash
dvc repro data_collection data_formatting model_training
```

Or run individual steps:

```zsh
python manage.py fetch_training_data
python manage.py format_training_data
python manage.py train_model
```

### K-fold Cross-validation

K-fold cross-validation allows for more robust model evaluation by:
1. Splitting the dataset into K folds
2. Training K different models, each using K-1 folds for training and 1 fold for validation
3. Averaging metrics across all K folds to get a better estimate of model performance

#### Using DVC Pipeline (Recommended)

To run the K-fold cross-validation using DVC pipeline:

```zsh
docker exec -it django-backend bash

# Run the complete pipeline (data collection, k-fold formatting, k-fold training)
dvc repro data_collection kfold_data_formatting kfold_model_training

# Optionally override parameters
dvc repro kfold_model_training -p K_FOLDS=10,EPOCHS=30,BATCH_SIZE=16
```

You can customize parameters in params.yaml or override them on the command line. Available parameters:
- `K_FOLDS`: Number of folds (default: 5)
- `EPOCHS`: Number of training epochs (default: 20)
- `BATCH_SIZE`: Batch size (default: 8)
- `IMG_SIZE`: Image size (default: 640)
- `PATIENCE`: Early stopping patience (default: 5)

#### Using Shell Script (Alternative)

Alternatively, you can use the shell script:

```zsh
docker exec -it django-backend bash
./run_kfold_cv.sh --k=5 --epochs=20 --batch-size=8 --img-size=640
```

### Results

K-fold cross-validation results will be stored in:
- `media/runs/kfold/` directory
- `media/runs/kfold/kfold_results.csv` file contains metrics for each fold
- MLflow dashboard will show results for each fold and average metrics


