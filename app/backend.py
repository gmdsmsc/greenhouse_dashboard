# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import app.db.model as db
import pandas as pd
from sqlalchemy import select

''' Provides utility functions for database operations.'''

def load_sensors(session, trial_id):
    qry = select(db.Sensor.name).join(db.trial_sensor_association).join(db.Trial).where(db.Trial.id == trial_id).order_by(db.Sensor.name).distinct()
    return session.execute(qry).scalars().all()

def unattached_keys(session, attached_keys):
    qry = select(db.Group.key).where(db.Group.key.not_in(attached_keys)).distinct()
    return session.execute(qry).scalars().all()

def get_trial_by_name(session, name):
    qry = select(db.Trial).where(db.Trial.name == name)
    return session.execute(qry).scalar()

def get_project_by_name(session, name):
    qry = select(db.Project).where(db.Project.name == name)
    return session.execute(qry).scalar()

def get_dataset_by_name(session, name):
    qry = select(db.Dataset).where(db.Dataset.name == name)
    return session.execute(qry).scalar()

def get_group_by_keyval(session, project, key, val):
    qry = select(db.Group).where(db.Group.project_id == project.id).where(db.Group.key == key).where(db.Group.value == val)
    return session.execute(qry).scalar()

#####

def load_table(session, table_class, columns=None, as_df=False, offset=0, limit=None, order_by=None):
    if columns is None:
        qry = select(table_class)
    else:
        columns = [getattr(table_class, column) for column in columns]
        qry = select(*columns).limit(limit).offset(offset).order_by(order_by)
    res = session.execute(qry)
    if as_df:
        return pd.DataFrame(res.fetchall(), columns=res.keys())
    return res.scalars().all()

from sqlalchemy.orm.session import make_transient, inspect

def clone_item(session, item):
    session.expunge(item)  # Remove it from the session
    make_transient(item)  # Make it transient (detached from session)
    item.id = None  # Reset the ID to None for cloning
    return item

def get_unique_name(session, dataset):
    existing_names = session.execute(select(db.Dataset.name)).scalars().all()
    dataset_name = dataset.name
    if dataset_name not in existing_names:
        return dataset_name
    for counter in range(1, len(existing_names) + 2):
        new_name = f"{dataset_name}_{counter}"
        if new_name not in existing_names:
            return new_name

def clone_exclusion(session, exclusion):
    sensors = exclusion.sensors
    cloned_exclusion = clone_item(session, exclusion)
    session.add(cloned_exclusion)
    cloned_exclusion.sensors.extend(sensors)
    session.flush()
    return cloned_exclusion

def clone_dataset(dataset):
    session = inspect(dataset).session  # Get the session from the dataset
    exclusions = list(dataset.exclusions)
    exclusions = [clone_exclusion(session, exclusion) for exclusion in exclusions]
    dataset = clone_item(session, dataset)  # Clone the dataset
    for exclusion in exclusions:
        exclusion.dataset = dataset
    dataset.name = get_unique_name(session, dataset)
    return dataset

def clone_group(group, project):
    session = inspect(group).session  # Get the session from the dataset
    key, val = group.key, group.value
    sensor_names = group.get_sensor_names()
    unassigned_sensors = project.get_unassigned_sensor_names(key)
    new_sensor_names = [name for name in sensor_names if name in unassigned_sensors]
    new_group = db.Group(key=key, value=val, project_id=project.id)
    new_group.set_sensor_names(session, new_sensor_names)
    return new_group

def remove_dataset_from_project(project, dataset):
    project.datasets.remove(dataset)
    session = inspect(project).session  # Get the session from the project
    session.commit()