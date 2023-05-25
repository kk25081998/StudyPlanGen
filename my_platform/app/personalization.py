import openai
from app import celery
from flask import current_app
from flask_login import current_user
from app import db
from app.models import LearningPath, Content
from dotenv import load_dotenv
import os
# Load the .env file
load_dotenv()

from bs4 import BeautifulSoup
import re

def convert_contents_to_html(contents, progress_data=None):
    # If progress_data is not provided, initialize it as an empty dictionary
    if progress_data is None:
        progress_data = {}

    soup = BeautifulSoup(features="html.parser")

    # Split contents into lines
    lines = contents.split('\n')

    # Initialize a list to hold the current list hierarchy
    current_lists = []
    
    # Initialize week and task counters
    week_counter = 0
    task_counter = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Initialize item to None at the start of each loop
        item = None

        # Determine the current list level
        list_level = 0 if line.startswith('Week') else 1

        # Remove list markers
        line = re.sub(r'-\s*', '', line)

        # Check for a link in the line
        match = re.search(r'(https?://\S+)', line)
        if match:
            link = match.group(1)
            line = line.replace(link, '').strip()

            # Create a link element
            link_element = soup.new_tag('a', href=link)
            link_element.string = link

            # Create an item element
            item = soup.new_tag('div')

            # Check if the task is checked in the progress data
            checked = ' checked' if progress_data.get(str(week_counter), {}).get(str(task_counter), {}).get('checked', False) else ''

            # Add a checkbox to the item
            checkbox = soup.new_tag('input', type='checkbox', **{'data-week': week_counter, 'data-task': task_counter, 'checked': checked})
            item.append(checkbox)

            # Add the line text and the link to the item
            item.append(f' {line} ')
            item.append(link_element)
            
            # Increment the task counter
            task_counter += 1
        else:
            # If the line is not a link, it might be a new week or a simple list item
            if line.startswith('Week'):
                # Create a new week header
                header = soup.new_tag('h3')
                header.string = line
                soup.append(header)

                # Reset the current list hierarchy
                current_lists = []
                
                # Increment the week counter and reset the task counter
                week_counter += 1
                task_counter = 0
            else:
                # Create a new list item with the line text
                item = soup.new_tag('li')
                item.string = line

        # Make sure the current list hierarchy is deep enough
        while len(current_lists) < list_level:
            new_list = soup.new_tag('ul')
            if current_lists:
                current_lists[-1].append(new_list)
            else:
                soup.append(new_list)
            current_lists.append(new_list)

        # Trim the current list hierarchy if it is too deep
        current_lists = current_lists[:list_level]

        # Add the item to the current list
        if item is not None:
            if current_lists:
                current_lists[-1].append(item)
            else:
                soup.append(item)

    # Return the formatted contents
    return str(soup)

@celery.task(bind=True)
def generate_personalized_learning_plan_task(self, user_id, username, title, topic_of_study, current_skill_level, target_skill_level, time_frame, api_key):
    openai.api_key = api_key

    # Generate the prompt
    prompt = (f"Create a simple study plan with links to resources for me to learn {topic_of_study} in {time_frame} weeks."
              f" My current skill level is {current_skill_level} and I want to be {target_skill_level} by the end of the study plan."
              f" Skill level 1 is beginner where level 5 is expert. Make sure to make the plan attainable and if the requirement for the user is unattainable, still try to give them a plan."
              f" Make sure the links are to popular videos from big learning platforms, articles and other learning materials" 
              f" In the response, only provide the study plan and nothing else. The format of the study plan should be week by week. Please provide a flat list with no nested bullet points, and use only '-' for bullet points everywhere.")
              
    # Call the OpenAI API
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1000,
        n=1,
        stop=None,
        temperature=0.1,
    )

    # Extract the generated plan and convert to HTML
    print(prompt)
    generated_plan = response.choices[0].text.strip()
    print(generated_plan)
    html_plan = convert_contents_to_html(generated_plan)
    print(html_plan)

    # Create a new learning path object with the formatted plan
    learning_path = LearningPath(
        title=title, 
        contents=html_plan, 
        user_id=user_id, 
        topic_of_study=topic_of_study, 
        current_skill_level=current_skill_level, 
        target_skill_level=target_skill_level, 
        time_frame=time_frame,
    )
    db.session.add(learning_path)
    db.session.commit()

    return learning_path.id

def convert_html_to_dict(html_contents):
    contents_dict = {}
    weeks = re.findall(r'<h3>Week (\d+):</h3><ul data-week="\1">(.*?)</ul>', html_contents, flags=re.DOTALL)

    for week_number, tasks_html in weeks:
        tasks = re.findall(r'<li><input type="checkbox" data-task="(\d+)">(.*?)</li>', tasks_html, flags=re.DOTALL)
        tasks_dict = {task_id: {'task_text': task_text.strip(), 'checked': False} for task_id, task_text in tasks}
        contents_dict[week_number] = tasks_dict

    return contents_dict


def convert_dict_to_html(data):
    html_contents = "<div>"
    for week_number, week_data in data.items():
        html_contents += f"<h3>Week {week_number}:</h3>"
        html_contents += f'<ul data-week="{week_number}">'
        for task_id, task_data in week_data.items():
            checked = task_data.get('checked', False)
            task_text = task_data.get('task_text', '')

            # Add checkbox and task_text to the bullet point
            task_text = f'<input type="checkbox" data-task="{task_id}" {"checked" if checked else ""}> {task_text}'

            html_contents += f'<li>{task_text}</li>'
        html_contents += "</ul>"
    html_contents += "</div>"
    return html_contents




