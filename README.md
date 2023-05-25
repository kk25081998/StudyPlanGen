# StudyPlanGen

This is a simple webapp that creates user generated study plan based on their preferences. Change the .env file to use your own openai key. That key doesnt work as I have deactivated it.

This project uses a variety of technologies:
1. Flask for backend
2. Celery and Redis (for messaging and task/queue generation)
3. Javascript/HTML/CSS for front end

Make sure to download all dependencies and packages like redis, celery, python to be able to start the app. To start the app, you simply need to exectute: python run.py
