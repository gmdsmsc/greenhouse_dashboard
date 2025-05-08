# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

from sqlalchemy import func, select, inspect
import pandas as pd

''' Provides classes for retrieving data for the data_editor
    displays.'''
class DatabaseRetriever:
    by = None
    ascending = None

    def __init__(self, session, qry, options=None):
        if len(qry.froms) != 1:
            raise ValueError("Query must have one and only one table")
        self.table = qry.column_descriptions[0]["entity"]
        self.session = session
        self.qry = qry
        self.options = options

    def get_num_pages(self, batch_size):
        row_count = self.get_row_count()
        return (int(row_count / batch_size) if int(row_count / batch_size) > 0 else 1)

    def get_row_count(self):
        qry = select(func.count('*')).select_from(self.qry.subquery())
        return self.session.execute(qry).scalar()

    def get_page(self, page_num, batch_size):
        offset = (page_num - 1) * batch_size
        qry = self.qry
        if self.by is not None and self.ascending is not None:
            qry = qry.order_by(
                getattr(self.table, self.by).asc() 
                if self.ascending 
                else getattr(self.table, self.by).desc())
        qry = qry.offset(offset).limit(batch_size)
        res = self.session.execute(qry).scalars().all()
        res = [[getattr(table, opt) for opt in self.options] for table in res]
        return pd.DataFrame(res, columns=self.options)

    def get_options(self):
        if self.options is None:
            return [column.key for column in self.qry.selected_columns]
        return self.options

    def set_sort_fields(self, by, ascending):
        self.by = by
        self.ascending = ascending


class FullTableDatabaseRetriever:
    by = None
    ascending = None

    def __init__(self, session, table, options=None):
        self.session = session
        self.table = table
        self.options = options

    def get_num_pages(self, batch_size):
        row_count = self.get_row_count()
        return (int(row_count / batch_size) if int(row_count / batch_size) > 0 else 1)

    def get_row_count(self):
        qry = select(func.count('*')).select_from(self.table)
        return self.session.execute(qry).scalar()

    def get_page(self, page_num, batch_size):
        offset = (page_num - 1) * batch_size
        qry = select(self.table)
        if self.by is not None and self.ascending is not None:
            qry = qry.order_by(
                getattr(self.table, self.by).asc() 
                if self.ascending 
                else getattr(self.table, self.by).desc())
        qry = qry.offset(offset).limit(batch_size)
        res = self.session.execute(qry).scalars().all()
        res = [[getattr(table, opt) for opt in self.options] for table in res]
        return pd.DataFrame(res, columns=self.options)

    def get_options(self):
        if self.options is None:
            return [column.key for column in inspect(self.table).mapper.columns]
        return self.options

    def set_sort_fields(self, by, ascending):
        self.by = by
        self.ascending = ascending
