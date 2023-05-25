# StudyPlanGen

This repository contains a simple web application that generates a user-specific study plan based on their preferences.

**Note**: The provided .env file contains an OpenAI key, but it has been deactivated. Please replace it with your own OpenAI key.

## Technologies Used

The project utilizes the following technologies:

1. Flask: Python web framework used for the backend.
2. Celery and Redis: Celery leverages Redis as a message broker and result backend. Redis serves as a reliable and scalable means to pass messages between producers and workers, facilitating the distribution and execution of tasks.
3. JavaScript, HTML, and CSS: These technologies are used for the frontend of the application.

## Prerequisites

Before running the application, ensure that you have the following dependencies installed:

- Redis
- Celery
- Python
- SQLite

Additionally, make sure to download all necessary packages.

## Getting Started

To start the application, follow these steps:

1. Configure the database:
   - Remove any existing databases by running the command: `rm app.db`
   - Open a Python terminal and run the following commands:
     ```python
     from app import create_app, db
     app = create_app()
     with app.app_context():
         db.create_all()
     ```

2. Start Celery:
   Open a terminal and execute the following command:
   ```
   celery -A celery_worker.celery worker --loglevel=info
   ```

3. Start the Flask app:
   Open a terminal and run the command:
   ```
   python3 run.py
   ```

Once the application is running, you can access it in your web browser. Make sure to adapt the database settings if necessary, as the project currently uses SQLite for simplicity. Feel free to switch to a different database for production purposes or further practice.

That's it! You should now have the StudyPlanGen application up and running. Enjoy generating personalized study plans!
