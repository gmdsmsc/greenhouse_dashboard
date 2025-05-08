# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st
from sqlalchemy import inspect, select
import app.db.model as db
from app.backend import load_table
from datetime import datetime


# Define your pages
def home():
    st.title("Home")
    st.write("Welcome to the home page.")

    st.write("This is a temporary placeholder for the main page that will be populated with as yet undecided content.")
    st.write("Visit the Trials page on the main menu first. Next, visit the Projects page to create a new Project.")

# Multiple functions are required here due to prevent re-triggering of the menu navigation   
def go_back_trial():
    menu_nav.go_back()

def go_back_project():
    menu_nav.go_back()

def go_back_dataset():
    menu_nav.go_back()

def open_trial():
    dataset = st.session_state.menu_tracking[-1]
    trial = dataset.trial
    menu_nav.navigate_to(trial)
    st.rerun()

@st.dialog("New Dataset")
def new_dataset():

    st.write("Choose a trial and a specific range of interest. Once the Dataset has been created, options to exclude time periods of the data will be available.")
    session = st.session_state.db_session

    trials = {trial.name: trial for trial in load_table(session, db.Trial)}
    trial_name = st.selectbox("Choose a dataset:", trials.keys())
    if trial_name:
        trial = trials[trial_name]

        minimum_date = trial.start_datetime.date()
        maximum_date = trial.end_datetime.date()
        minimum_time = trial.start_datetime.time()
        maximum_time = trial.end_datetime.time()
        
        name = st.text_input("Dateset Name:")                     

        # Datetime range selection
        date_range = st.date_input(
            "Select date range",
            value=(minimum_date, maximum_date),
            min_value=minimum_date, max_value=maximum_date
        )
        start_time = st.time_input("Start time", minimum_time, step=60)
        stop_time = st.time_input("Stop time", maximum_time, step=60)

        if st.button("Submit"):
            if session.execute(select(db.Dataset).where(db.Dataset.name == name)).one_or_none() is not None:
                st.error("❌ A Dataset with this name already exists.")
            else:
                start_datetime = datetime.combine(date_range[0], start_time)
                end_datetime = datetime.combine(date_range[1], stop_time)
                dataset = db.Dataset(name=name, trial=trial,
                                      start_datetime=start_datetime, 
                                      end_datetime=end_datetime)
                session.add(dataset)
                session.commit()
                menu_nav.navigate_to(dataset)
                st.rerun()


@st.dialog("New Project")
def new_project():
    session = st.session_state.db_session
    name = st.text_input("Project Name:")
    if st.button("Submit"):
        if session.execute(select(db.Project).where(db.Project.name == name)).one_or_none() is not None:
            st.error("❌ A Project with this name already exists.")
        else:
            project = db.Project(name=name)
            session.add(project)
            session.commit()
            menu_nav.navigate_to(project)
            st.rerun()

def menu_location():
    return menu_nav.get_menu_path()


def home_from_project():
    # User has deselected from the project, return to project selection
    return {
        "Main": [
            st.Page(home, title="Home", icon=":material/home:"),
            st.Page("gui/menu_items/trial.py", title="Trials", icon=":material/folder:"),
            st.Page("gui/menu_items/trial_maker.py", title="New Trial", icon=":material/add:"),
            st.Page("gui/menu_items/dataset.py", title="Datasets", icon=":material/folder:"),
            st.Page(new_dataset, title="New Dataset", icon=":material/add:"),
            st.Page("gui/menu_items/project.py", title="Projects", icon=":material/folder:", default=True),
            st.Page(new_project, title="New Project", icon=":material/add:"),
        ]
    }

def home_from_trial():
    # User has deselected from the project, return to project selection
    return {
        "Main": [
            st.Page(home, title="Home", icon=":material/home:"),
            st.Page("gui/menu_items/trial.py", title="Trials", icon=":material/folder:", default=True),
            st.Page("gui/menu_items/trial_maker.py", title="New Trial", icon=":material/add:"),
            st.Page("gui/menu_items/dataset.py", title="Datasets", icon=":material/folder:"),
            st.Page(new_dataset, title="New Dataset", icon=":material/add:"),
            st.Page("gui/menu_items/project.py", title="Projects", icon=":material/folder:"),
            st.Page(new_project, title="New Project", icon=":material/add:"),
        ]
    }

def project_from_dataset():
    # User has selected a project, show project pages and main navigation
    return {
        f"{menu_location()}": [
            st.Page(go_back_project, title="Return", icon=":material/exit_to_app:"),
            st.Page("gui/menu_items/project_overview.py", title="Overview", icon=":material/dashboard:"),
            st.Page("gui/menu_items/project_dataset.py", title="Datasets", icon=":material/database:", default=True),
            st.Page("gui/menu_items/group.py", title="Sensor Groups", icon=":material/group_work:"),
            st.Page("gui/menu_items/plot.py", title="Plots", icon=":material/insert_chart_outlined:"),

        ]}

def no_selection():
    # No project selected, only show main navigation
    return {
        "Main": [
            st.Page(home, title="Home", icon=":material/home:", default=True),
            st.Page("gui/menu_items/trial.py", title="Trials", icon=":material/folder:"),
            st.Page("gui/menu_items/trial_maker.py", title="New Trial", icon=":material/add:"),
            st.Page("gui/menu_items/dataset.py", title="Datasets", icon=":material/folder:"),
            st.Page(new_dataset, title="New Dataset", icon=":material/add:"),
            st.Page("gui/menu_items/project.py", title="Projects", icon=":material/folder:"),
            st.Page(new_project, title="New Project", icon=":material/add:"),
        ]
    }

def project_selected():
    # User has selected a project, show project pages and main navigation
    return {
        f"{menu_location()}": [
            st.Page(go_back_project, title="Return", icon=":material/exit_to_app:"),
            st.Page("gui/menu_items/project_overview.py", title="Overview", icon=":material/dashboard:", default=True),
            st.Page("gui/menu_items/project_dataset.py", title="Datasets", icon=":material/database:"),
            st.Page("gui/menu_items/group.py", title="Sensor Groups", icon=":material/group_work:"),
            st.Page("gui/menu_items/plot.py", title="Plots", icon=":material/insert_chart_outlined:"),
        ]}

def trial_from_home():
    # User has selected a trial, show trial pages and main navigation
    return {
        f"{menu_location()}": [
            st.Page(go_back_trial, title="Return", icon=":material/exit_to_app:"),
            st.Page("gui/menu_items/trial_overview.py", title="Overview", icon=":material/dashboard:", default=True),
            st.Page("gui/menu_items/trialdata.py", title="Time Data", icon=":material/database:"),
            st.Page("gui/menu_items/image_gallery.py", title="Image Gallery", icon=":material/image:"),
        ]}

def trial_from_dataset():
    # User has selected a trial from dataset, show trial pages and main navigation
    return {
        f"{menu_location()}": [
            st.Page(go_back_trial, title="Return", icon=":material/exit_to_app:"),
            st.Page("gui/menu_items/trial_overview.py", title="Overview", icon=":material/dashboard:", default=True),
            st.Page("gui/menu_items/trialdata.py", title="Time Data", icon=":material/database:"),
            st.Page("gui/menu_items/image_gallery.py", title="Image Gallery", icon=":material/image:"),
        ]}

def dataset_selected():
    # User has selected a dataset, show dataset pages and main navigation
    return {
        f"{menu_location()}": [
            st.Page(go_back_dataset, title="Return", icon=":material/exit_to_app:"),
            st.Page("gui/menu_items/dataset_overview.py", title="Overview", icon=":material/dashboard:", default=True),
            st.Page("gui/menu_items/exclusion_selector.py", title="Exclusions", icon=":material/fullscreen:"),
            st.Page(open_trial, title="Open Trial", icon=":material/folder:"),
        ]}


def check_database(expected_tables):
    ''' Check if the current tables in the database match the expected tables. '''
    inspector = inspect(st.session_state.db_session.get_bind())
    current_tables = inspector.get_table_names()
    for table in expected_tables:
        if table not in current_tables:
            return False
    return True

def get_last_item(lst):
    return lst[-1] if lst else None

def get_second_last_item(lst):
    return lst[-2] if len(lst) > 1 else None


def make_table():
    if hasattr(st.session_state, 'db_session'):
        # Initialise menu tracking
        if "menu_tracking" not in st.session_state:
            st.session_state.menu_tracking = []
        if not check_database(db.Base.metadata.tables.keys()):
            st.write("Database not initialised.")
            from create_db import main
            main()
        else:
            # Define navigation based on project selection
            current_selection = get_last_item(st.session_state.menu_tracking)
            prev_selection = get_second_last_item(st.session_state.menu_tracking)
            if current_selection is None and type(prev_selection) == db.Project:
                pages = home_from_project()
            elif current_selection is None and type(prev_selection) == db.Trial:
                pages = home_from_trial()
            elif type(current_selection) is db.Project and type(prev_selection) == db.Dataset:
                pages = project_from_dataset()
            elif type(current_selection) is db.Trial and type(prev_selection) == db.Dataset:
                pages = trial_from_dataset()
            elif type(current_selection) == db.Project:
                pages = project_selected()
            elif type(current_selection) == db.Trial:
                pages = trial_from_home()
            elif type(current_selection) == db.Dataset:
                pages = dataset_selected()
            else:
                pages = no_selection()

            # Set up navigation
            pg = st.navigation(pages)
            pg.run()
        
class menu_nav:
    def get_current_selection():
        return get_last_item(st.session_state.menu_tracking)
    
    def get_previous_selection():
        return get_second_last_item(st.session_state.menu_tracking)
    
    def navigate_to(selection):
        st.session_state.menu_tracking.append(selection)
        st.rerun()
    
    def go_back():
        if len(st.session_state.menu_tracking) > 1:
            st.session_state.menu_tracking.pop(-1)
            st.rerun()
        else:
            st.session_state.menu_tracking = []
            st.rerun()

    def get_menu_path():
        return "->".join([item.name for item in st.session_state.menu_tracking])
