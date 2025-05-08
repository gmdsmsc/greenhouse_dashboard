# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import pandas as pd

''' Provides a utility function for dataframe type checking. '''

def gen_float_cols(df, dt_cols):
    ''' Generates a list of columns that can be converted to float. '''
    for i, column in enumerate(df.columns):
        if i not in dt_cols:
            try:
                pd.to_numeric(df[column], errors='raise').astype(float)
                yield column
            except ValueError:
                pass