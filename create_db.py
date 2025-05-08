# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

from sqlalchemy import create_engine
import app.db.model as db
from app.db.settings import DATABASE_URL

''' Script to create the empty database. '''


def main():
    # Create projects DB
    engine = create_engine(DATABASE_URL)
    db.Base.metadata.create_all(engine)
    engine.dispose()


if __name__ == '__main__':

    main()
