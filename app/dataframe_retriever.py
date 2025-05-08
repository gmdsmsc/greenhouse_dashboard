# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

def split_frame(input_df, rows):
    df = [input_df.loc[i : i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return df

''' Provides classes for retrieving data for the data_editor
    displays. This one passes a dataframe to the constructor.'''
class DataFrameRetriever:
    by = None
    ascending = None

    def __init__(self, dataset):
        self.dataset = dataset

    def get_num_pages(self, batch_size):
        row_count = self.get_row_count()
        return (int(row_count / batch_size) if int(row_count / batch_size) > 0 else 1)

    def get_row_count(self):
        return len(self.dataset)

    def get_page(self, page_num, batch_size):
        df = self.dataset
        if self.by is not None and self.ascending is not None:
            df = df.sort_values(by=self.by, ascending=self.ascending, ignore_index=True)
        pages = split_frame(df, batch_size)
        return pages[page_num - 1]

    def get_options(self):
        return self.dataset.columns

    def set_sort_fields(self, by, ascending):
        self.by = by
        self.ascending = ascending