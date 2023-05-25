# app/routes.py
print("Routes file loaded!")  # Add this line

from flask import render_template, redirect, url_for, flash, abort, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from app import db, create_app, celery
from app.forms import RegistrationForm, LoginForm
from app.forms import AddContentForm, CreateLearningPathForm, LearningPreferencesForm
from app.models import User, LearningPath, Content, StudyPlanProgress
from app.forms import AddContentToPathForm, EditProfileForm
from app.personalization import generate_personalized_learning_plan_task, convert_html_to_dict, convert_dict_to_html
from datetime import datetime
from werkzeug.exceptions import HTTPException  # import HTTPException instead of abort
from flask import Blueprint
from flask import current_app
import json

login_manager = LoginManager()
login_manager.login_view = 'main.login'
main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already taken. Please choose a different one.')
            return redirect(url_for('main.register'))

        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email already registered. Please use a different one or log in.')
            return redirect(url_for('main.register'))

        if form.password.data != form.password_confirm.data:
            flash('Password and confirmation do not match. Please try again.')
            return redirect(url_for('main.register'))

        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful.')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password.')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        session['user_id'] = user.id  # Store the user's id in the session
        return redirect(url_for('main.dashboard'))
    return render_template('login.html', form=form)


@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/create_learning_path', methods=['GET', 'POST'])
@login_required
def create_learning_path():
    form = CreateLearningPathForm()
    if form.validate_on_submit():
        title = form.title.data
        topic_of_study = form.topic_of_study.data
        current_skill_level = form.current_skill_level.data
        target_skill_level = form.target_skill_level.data
        time_frame = form.time_frame.data
        flash('Your learning path is currently being generated and should be available in the next few minutes.', 'success')

        # Generate personalized learning plan
        generate_personalized_learning_plan_task.apply_async(args=[current_user.id, current_user.username, title, topic_of_study, current_skill_level, target_skill_level, time_frame, current_app.config['OPENAI_API_KEY']])

        return redirect(url_for('main.dashboard'))
        
    return render_template('create_learning_path.html', title='Create Learning Path', form=form)


# @main.route('/update_task_completion', methods=['POST'])
# def update_task_completion():
#     data = request.get_json()
#     learning_path_id = data.get('learning_path_id')
#     task_index = data.get('task_index')

#     # Update the learning path's completed tasks in the database
#     learning_path = LearningPath.query.get(learning_path_id)
#     if learning_path:
#         week_number = get_week_number_from_task_index(task_index)
#         learning_path.mark_task_completed(week_number, task_index)
#         db.session.commit()
#         return jsonify({'message': 'Task completion updated'})
#     else:
#         return jsonify({'message': 'Learning path not found'}), 404

@main.route('/learning_paths')
@login_required
def learning_paths():
    paths = LearningPath.query.filter_by(user_id=current_user.id).all()
    return render_template('learning_paths.html', paths=paths)


# @main.route('/learning_path/<int:path_id>', methods=['GET', 'POST'])
# @login_required
# def view_learning_path(path_id):
#     path = LearningPath.query.get_or_404(path_id)
#     if path.user_id != current_user.id:
#         abort(403)
#     form = AddContentToPathForm()
#     form.content.choices = [(c.id, c.title) for c in Content.query.filter_by(user_id=current_user.id).all()]
#     if form.validate_on_submit():
#         content = Content.query.get(form.content.data)
#         content.learning_path_id = path_id
#         db.session.commit()
#         flash('Content added to learning path.')
#         return redirect(url_for('main.view_learning_path', path_id=path_id))
#     return render_template('view_learning_path.html', path=path, form=form)

@main.route('/learning_path/<int:path_id>', methods=['GET', 'POST'])
@login_required
def view_learning_path(path_id):
    path = LearningPath.query.get_or_404(path_id)
    if path.user_id != current_user.id:
        abort(403)
    form = AddContentToPathForm()
    form.content.choices = [(c.id, c.title) for c in Content.query.filter_by(user_id=current_user.id).all()]
    if form.validate_on_submit():
        content = Content.query.get(form.content.data)
        content.learning_path_id = path_id
        db.session.commit()
        flash('Content added to learning_path.')
        return redirect(url_for('main.view_learning_path', path_id=path_id))

    progress_data = get_progress_from_database(current_user.id, path_id)  # Fetch the progress data
    return render_template('view_learning_path.html', path=path, form=form, progress_data=progress_data)


@main.route('/update_progress', methods=['POST'])
def update_progress():
    data = request.get_json()
    print(f"Received data: {data}")
    user_id = data.get('user_id')
    progress_data = data.get('progress_data')

    # Retrieve the learning path
    path_id = data.get('path_id')
    path = LearningPath.query.get(path_id)

    if path:
        # Update the progress for each task
        for week_number, week_data in progress_data.items():
            for task_id, task_data in week_data.items():
                checked = task_data.get('checked', False)

                # Check if the progress exists in the database
                progress = StudyPlanProgress.query.filter_by(
                    user_id=user_id,
                    learning_path_id=path_id,
                    week_number=week_number,
                    task_id=task_id
                ).first()

                if progress:
                    # Update the progress
                    progress.checked = checked
                else:
                    # Create a new progress entry
                    progress = StudyPlanProgress(
                        user_id=user_id,
                        learning_path_id=path_id,
                        week_number=week_number,
                        task_id=task_id,
                        checked=checked
                    )
                    db.session.add(progress)

        # Update the contents attribute with the new checkbox state
        path.update_contents(progress_data)

        # Commit the database changes
        db.session.commit()

        # Calculate overall progress
        total_tasks = path.contents.count('data-task=')
        completed_tasks = StudyPlanProgress.query.filter_by(
            user_id=user_id,
            learning_path_id=path_id,
            checked=True
        ).count()
        overall_progress = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

        return jsonify({'progress': overall_progress}), 200
    else:
        return jsonify({'error': 'Learning path not found'}), 404

@main.route('/get_progress')
def get_progress():
    user_id = request.args.get('user_id')
    path_id = request.args.get('path_id')

    if not user_id or not path_id:
        abort(400, "Invalid parameters")

    try:
        progress_data = get_progress_from_database(user_id, path_id)
    except Exception as e:
        abort(500, "Failed to get progress from database: " + str(e))

    # Ensure keys are strings
    try:
        progress_data_str_keys = {str(k): v for k, v in progress_data.items()}
        print("Test")
        print(progress_data_str_keys)
        print("End of test")
    except Exception as e:
        abort(500, "Failed to convert progress data keys to strings: " + str(e))

    return jsonify(progress_data_str_keys), 200


def get_progress_from_database(user_id, path_id):
    progress_data = {}
    
    # Query StudyPlanProgress to get progress of a user on a specific learning path
    progress_entries = StudyPlanProgress.query.filter_by(user_id=user_id, learning_path_id=path_id).all()
    print(progress_entries)

    # Populate progress_data dictionary from the query results
    for entry in progress_entries:
        if entry.week_number not in progress_data:
            progress_data[entry.week_number] = {}
        progress_data[entry.week_number][entry.task_id] = {'checked': entry.checked}

    return progress_data

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/get_user_id')
@login_required
def get_user_id():
    # Add your own checks here to ensure only the authorized user can access the ID
    return jsonify({'user_id': current_user.id})

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = EditProfileForm(current_user.username, current_user.email)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('profile.html', title='Edit Profile', form=form)