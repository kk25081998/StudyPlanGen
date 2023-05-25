from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
from datetime import datetime
import re
from bs4 import BeautifulSoup

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(200), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    learning_path_id = db.Column(db.Integer, db.ForeignKey('learning_path.id'))  # Add this line

    def __repr__(self):
        return f"Content('{self.title}', '{self.source}', '{self.content_type}', '{self.difficulty}')"

class LearningPath(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    topic_of_study = db.Column(db.String(120), nullable=False)
    current_skill_level = db.Column(db.Integer, nullable=False)
    target_skill_level = db.Column(db.Integer, nullable=False)
    time_frame = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contents = db.Column(db.Text, nullable=False)

    def update_contents(self, checkbox_data):
        # Update the contents based on the checkbox data
        soup = BeautifulSoup(self.contents, 'html.parser')
        for week_number, week_data in checkbox_data.items():
            for task_id, task_data in week_data.items():
                checked = task_data.get('checked', False)
                # Find the corresponding <input> element in the contents
                checkbox = soup.find('input', attrs={'data-week': str(week_number), 'data-task': str(task_id)})
                if checkbox:
                    if checked:
                        checkbox['checked'] = 'checked'
                    elif 'checked' in checkbox.attrs:
                        del checkbox['checked']
        self.contents = str(soup)

    def __repr__(self):
        return f"LearningPath('{self.title}', '{self.topic_of_study}', '{self.current_skill_level}', '{self.target_skill_level}', '{self.time_frame}')"

class StudyPlanProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    learning_path_id = db.Column(db.Integer, nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    task_id = db.Column(db.Integer, nullable=False)
    checked = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return f"StudyPlanProgress(user_id={self.user_id}, learning_path_id={self.learning_path_id}, week_number={self.week_number}, task_id={self.task_id}, checked={self.checked})"