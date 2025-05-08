# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import pandas as pd
import warnings
from dateutil import parser

''' Detects the type of each column in a dataframe.
    Returns a generator that yields the type of each column. The types can be:
    - 'datetime': if the column is a datetime column
    - 'date': if the column is a date column
    - 'time': if the column is a time column
    - 'float': if the column is a float column 
'''


def detect_types(df):
    ''' For a given dataframe, detect datetime, date and time columns.'''
    df = df.astype(str)
    # Temporarily catch warnings within this block
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        # Loop through each column and try to convert it to datetime
        for i in range(len(df.columns)):
            try:
                col = pd.to_datetime(df.iloc[:, i])
                # If all entries are just the date component of the datetime, must be date column
                if (all(col.dt.date == col)):
                    yield 'date'
                # If the reader receives just empty strings, it will assume it could be a datetime column
                # but it could be that the first few entries are empty and the rest are not dates.
                # We'll reject any columns with the first entry being an empty so the user must
                # make sure that the data starts with a non-null datetime.
                elif pd.isnull(col.iloc[0]):
                    yield None
                elif col.dtype == 'datetime64[ns]':
                    yield 'datetime'
            except (ValueError, UserWarning, pd._libs.tslibs.parsing.DateParseError):
                # If datetime or date not detected, try to parse the column as time
                col = df.iloc[:, i]
                # Make sure that the column does not have floats first
                try:
                    col.astype('float')
                    yield 'float'
                except ValueError:
                    try:
                        col = col.apply(lambda x: parser.parse(x).time())
                    except (TypeError, parser._parser.ParserError):
                        yield None
                    else:
                        if pd.isnull(col.iloc[0]):
                            yield None
                        else:
                            yield 'time'
