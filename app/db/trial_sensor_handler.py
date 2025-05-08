# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

from sqlalchemy import event
from sqlalchemy.orm import Session

''' Defines event listeners for the SQLAlchemy session to handle specific actions.'''

@event.listens_for(Session, 'before_attach')
def receive_before_attach(session, instance):
    if instance.__class__.__name__ == 'Trial':
        instance.apply_readings_map()

@event.listens_for(Session, "before_flush")
def enforce_non_empty_groups(session, flush_context, instances):
    for obj in session.new.union(session.dirty):
        if obj.__class__.__name__ == 'Visualisation' and not obj.sensors:
            e = Exception()
            e.orig = "Visualisation must have at least one sensor."
            raise e
