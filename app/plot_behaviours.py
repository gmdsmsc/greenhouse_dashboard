# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import numpy as np
import pandas as pd

''' Provides classes for visualisation of data. This is the main
    class for the visualisation. It handles the data processing
    and the plotting. '''
class StandardPlot:
    def process(self, x_axis, y_axis, df):
        return x_axis, y_axis, df

    def get_labels(self):
        return {}


class XYPlot:
    def process(self, x_axis, y_axis, df):
        try:
            df = df.pivot(index='datetime', columns='variable', values='value')
        except KeyError:
            df = df.pivot(index='day', columns='variable', values='value')
        if x_axis not in df.columns:
            df[x_axis] = None
        if y_axis not in df.columns:
            df[y_axis] = None
        return x_axis, y_axis, df

    def get_labels(self):
        return {}


class GroupYPlot:
    def process(self, x_axis, y_axis, df):
        df_metadata = self.project.get_group_df(self.dataset)
        df_metadata = df_metadata[df_metadata['key'] == self.y_axis]
        df1 = df[df['variable'] != self.x_axis]
        df2 = df[df['variable'] == self.x_axis]
        df = df1.merge(df2, on='datetime')
        df = df.merge(df_metadata, left_on='variable_x', right_on='sensor')
        return 'value_x', 'value_y', df

    def get_labels(self):
        return {'value_x': self.x_axis, 'value_y': self.y_axis}


class DLIPreprocess:
    def process(self):
        df = self.dataset.get_dataframe(self.sensors)
        df_dli = df.copy()
        df_dli = df_dli.pivot(index='datetime', columns='variable', values='value')
        df_dli = df_dli.reset_index()
        df_dli['day'] = df_dli['datetime'].dt.date
        df_dli.drop('datetime', axis=1, inplace=True)
        sensors = [column for column in df_dli.columns if column != 'day']
        df_dli = df_dli[['day'] + sensors].groupby('day').sum().reset_index()
        df_dli[sensors] = 60 * df_dli[sensors] / 1000000
        df_dli = df_dli.melt(id_vars='day', var_name='variable', value_name='value').reset_index()
        return 'day', 'value', df_dli

    def display_text(self):
        return 'DLI (mol/m2/day)'
        


class TransmissibilityPreprocess:
    def process(self):
        sensors = self.sensors + [self.reference_sensor]
        df = self.dataset.get_dataframe(sensors)
        df = df.pivot(index='datetime', columns='variable', values='value')
        for sensor in self.sensors:
            df[sensor.name] = df[sensor.name] / df[self.reference_sensor.name]
        df = df.drop(self.reference_sensor.name, axis=1)
        df = df.reset_index()
        df = df.melt(id_vars='datetime', var_name='variable', value_name='value')
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        df.reset_index(inplace=True)
        return self.x_axis, self.y_axis, df
        
    def display_text(self):
        return f'Transmissibility (ratio) against {self.reference_sensor.get_display_name()}'

class DetrendPreprocess:
    def process(self):
        df = self.dataset.get_dataframe(self.sensors).reset_index()
        df = df.pivot(index='datetime', columns='variable', values='value')
        # Downsample only
        interval_in_seconds = self.quantity * {'s': 1, 'min': 60, 'h': 3600}[self.detrend_units]
        time_in_seconds = df.reset_index()['datetime'].astype('int64') // 10**9
        mean_time_interval = time_in_seconds.diff().mean() * 1000
        if mean_time_interval < interval_in_seconds:
            new_time_interval = f"{self.quantity}{self.detrend_units}"
            df = df.copy().reset_index().resample(new_time_interval, on='datetime').mean()
        df_mean = df.reset_index()
        # Original data
        sensor_names = [sensor.name for sensor in self.sensors]
        df = self.dataset.get_dataframe(self.sensors).reset_index()
        df = df.pivot(index='datetime', columns='variable', values='value').reset_index()
        
        # Detrend
        df_mean_downsampled = df[['datetime']].merge(df_mean, how='left', on='datetime').interpolate(limit_direction='both')
        df_detrended = df[sensor_names] - df_mean_downsampled[sensor_names]
        df_detrended['datetime'] = df['datetime'].values
        df = df_detrended.melt(id_vars='datetime', var_name='variable', value_name='value').reset_index()
        return self.x_axis, self.y_axis, df

    def display_text(self):
        return f'Detrended ({self.quantity} {self.detrend_units})'


class RunningMeanPreprocess:
    def process(self):
        df = self.dataset.get_dataframe(self.sensors).reset_index()
        df = df.pivot(index='datetime', columns='variable', values='value')
        # Upsample only
        interval_in_seconds = self.quantity * {'s': 1, 'min': 60, 'h': 3600}[self.detrend_units]
        time_in_seconds = df.reset_index()['datetime'].astype('int64') // 10**9
        mean_time_interval = time_in_seconds.diff().mean() * 1000       
        if mean_time_interval > interval_in_seconds:
            new_time_interval = f"{self.quantity}{self.detrend_units}"
            df = df.copy().reset_index().resample(new_time_interval, on='datetime').mean()
        df = df.reset_index().melt(id_vars='datetime', var_name='variable', value_name='value').reset_index()
        return self.x_axis, self.y_axis, df
    
    def display_text(self):
        return f'Running mean ({self.quantity} {self.detrend_units})'


class OccurrencePreprocess:
    def process(self):
        df = self.dataset.get_dataframe(self.sensors)
        df = df.pivot(index='datetime', columns='variable', values='value').reset_index()
        series = []
        for sensor in self.sensors:
            in_limits = df[['datetime', sensor.name]][df[sensor.name].between(self.lower_limit, self.upper_limit)]
            in_limits['day'] = in_limits['datetime'].dt.date
            in_limits = in_limits.groupby('day').size()
            series.append(in_limits)
        df = pd.concat(series, axis=1)
        df.columns = [sensor.name for sensor in self.sensors]
        df.reset_index(inplace=True)
        df = df.melt(id_vars='day', var_name='variable', value_name='value')
        df.dropna(inplace=True)
        df = df.reset_index()
        return 'day', self.y_axis, df

    def display_text(self):
        return f'Occurrence count between ({self.lower_limit} - {self.upper_limit})'


class NoPreprocess:
    def process(self):
        df = self.dataset.get_dataframe(self.sensors)
        return self.x_axis, self.y_axis, df

    def display_text(self):
        return 'Raw Data'


class VisualisationBehaviour:

    def get_df_for_csv(self):
        try:
            _, _, df = self.get_preprocessor().process(self)
            return df.pivot(index='datetime', columns='variable', values='value').reset_index()
        except KeyError:
            return df.pivot(index='day', columns='variable', values='value').reset_index()

    def get_preprocessor(self):
        transformations = {'dli': DLIPreprocess,
                           'tx': TransmissibilityPreprocess,
                           'detrend': DetrendPreprocess,
                           'running_mean': RunningMeanPreprocess,
                           'occurrence_count': OccurrencePreprocess}
        return transformations.get(self.preprocess, NoPreprocess)

    def get_pdescription(self):
        return self.get_preprocessor().display_text(self)

    def get_title(self, index):
        pdesc = self.get_pdescription()
        return f"Item {index} - Plot - Dataset: {self.dataset.name} - {pdesc}"

    def render(self):
        x_axis, y_axis, df = self.get_preprocessor().process(self)

        plot_types = {'xy': XYPlot, 
                      'groupy': GroupYPlot, }
        plot_type = plot_types.get(self.plot_format, StandardPlot)
        x_axis, y_axis, df = plot_type.process(self, x_axis, y_axis, df)
        labels = plot_type.get_labels(self)


        import plotly.express as px
        if self.color is None:
            # Create a scatter plot using Plotly Express
            if self.plot_type == 'Scatter':
                return px.scatter(df, x=x_axis, y=y_axis, color_discrete_sequence=['light blue'], labels=labels)
            return px.line(df, x=x_axis, y=y_axis, color_discrete_sequence=['light blue'], labels=labels)
        else:
            if self.plot_type == 'Scatter':
                return px.scatter(df, x=x_axis, y=y_axis, color=self.color, labels=labels)
            return px.line(df, x=x_axis, y=y_axis, color=self.color, labels=labels)
