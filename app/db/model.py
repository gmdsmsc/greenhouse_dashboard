# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import io
from PIL import Image as PImage
import pandas as pd
from sqlalchemy import Column, TIMESTAMP, String, Table, ForeignKey, \
                        Integer, Sequence, func, LargeBinary, \
                        PrimaryKeyConstraint, FLOAT,  event, select, \
                        and_, inspect, UniqueConstraint, CheckConstraint, \
                        delete, text
from sqlalchemy.orm import DeclarativeBase, relationship, backref
from app.plot_behaviours import VisualisationBehaviour
import app.db.trial_sensor_handler as trial_sensor_handler # do not delete
from sqlalchemy.sql.functions import coalesce

''' Defines the Entity Relationship model for the database
    and adds the methods and behaviours required for the 
    python objects created by the ORM.'''

class Base(DeclarativeBase):
    pass


sensor_group_association = Table(
    "sensor_name_groups",
    Base.metadata,
    Column("group_id", ForeignKey("grouping.id"), primary_key=True),
    Column("sensor_id", ForeignKey("group_sensor_names.id"), primary_key=True),
)

exclusion_sensor_association = Table(
    "exclusion_sensors",
    Base.metadata,
    Column("exclusion_id", ForeignKey("exclusion.id"), primary_key=True),
    Column("sensor_id", ForeignKey("sensor.id"), primary_key=True),
    )

visualisation_sensor_association = Table(
    "vis_sensors",
    Base.metadata,
    Column("visualisation_id", ForeignKey("visualisation.id"), primary_key=True),
    Column("sensor_id", ForeignKey("sensor.id"), primary_key=True),
    )

project_datasets_association = Table(
    "project_datasets",
    Base.metadata,
    Column("project_id", ForeignKey("project.id"), primary_key=True),
    Column("dataset_id", ForeignKey("dataset.id"), primary_key=True),
    )


class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer, Sequence('project_id_seq'),  primary_key=True)
    name = Column(String, unique=True)
    notes = Column(String)

    def get_dataframe(self):
        dataframes = []
        for dataset in self.datasets:
            trial_df = dataset.trial.get_dataframe()
            trial_df['trial'] = dataset.trial.name
            trial_df['dataset'] = dataset.name
            dataframes.append(trial_df)
        df = pd.concat(dataframes, axis=0)
        df = df.pivot(index=['datetime', 'trial', 'dataset'], columns='variable', values='value')
        return df.reset_index()

    def get_datasets_dataframe(self):
        tuples = [(dataset.name, dataset.start_datetime, dataset.end_datetime, dataset.trial.name)
                for dataset in self.datasets]
        columns = ['name', 'start_datetime', 'end_datetime', 'trial_name']
        return pd.DataFrame(tuples, columns=columns)

    def get_group_display_df(self):
        tuples = [(group.key, group.value, group.get_sensor_names())
                    for group in self.groups]
        columns = ['key', 'value', 'sensors']
        return pd.DataFrame(tuples, columns=columns)

    def get_sensors(self):
        dataset_ids = [dataset.id for dataset in self.datasets]
        qry = select(Sensor).join(Trial).join(Dataset).where(Dataset.id.in_(dataset_ids))
        return inspect(self).session.execute(qry).scalars().all()

    def gen_sensors(self, dataset):
        for group in self.groups:
            for sensor in group.sensors:
                if sensor in dataset.trial.sensors:
                    yield group.id, group.key, group.value, sensor.name

    def get_group_df(self, dataset):
        ''' group metadata dataframe '''
        tuples = list(self.gen_sensors(dataset))
        columns = ['id', 'key', 'value', 'sensor']
        return pd.DataFrame(tuples, columns=columns)

    def get_group_values(self, key):
        return [group.value for group in self.groups if group.key == key]

    def get_unassigned_sensor_names(self, key):
        assigned_sensor_names_lists = [group.get_sensor_names() for group in self.groups if group.key == key]
        assigned_sensor_names = [item for sublist in assigned_sensor_names_lists for item in sublist]
        unassigned_sensor_names = [sensor.get_display_name() for sensor in self.get_sensors() if
                            sensor.get_display_name() not in assigned_sensor_names]
        return list(set(unassigned_sensor_names))

    def get_filter_options(self):
        options = list(set([group.key for group in self.groups]))
        key_to_values = {key: [group.value for group in self.groups if group.key == key] for key in options}
        return options, key_to_values

class Trial(Base):
    _dataframe = None
    _readings_map = None
    __tablename__ = 'trial'
    id = Column(Integer, Sequence('trial_id_seq'),  primary_key=True)
    name = Column(String, nullable=False, unique=True)
    notes = Column(String)
    start_datetime = Column(TIMESTAMP)
    end_datetime = Column(TIMESTAMP)
    greenhouse_name = Column(String)
    postcode = Column(String)

    @property
    def dataframe(self):
        return self._dataframe

    @dataframe.setter
    def dataframe(self, df):
        ''' Performs the required checks to make sure the incoming dataframe is valid. '''
        try:
            if not isinstance(df, pd.DataFrame):
                raise TypeError("Dataframe must be of type pandas.DataFrame.")
            df["datetime"] = df["datetime"].astype("datetime64[ns, UTC]")
            df["variable"] = df["variable"].astype("string")
            df["value"] = df["value"].astype("float64")
            self.start_datetime = df['datetime'].min()
            self.end_datetime = df['datetime'].max()
            self._dataframe = df
        except:
            raise TypeError("Not all the incoming data were of the correct type.")

    @property
    def readings_map(self):
        return self._readings_map

    @readings_map.setter
    def readings_map(self, df):
        ''' Performs the required checks to make sure the incoming readings_map is valid. '''
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Dataframe must be of type pandas.DataFrame.")
        expected_schema = {'name': 'string', 'display_name': 'string'}
        assert_fail_string = f"Incorrect column names. Dataframe must have {expected_schema}. Received {list(df.dtypes.items())}"
        assert all(col in df.columns for col in expected_schema), assert_fail_string
        assert all(str(df[col].dtype) == dtype for col, dtype in expected_schema.items()), assert_fail_string
        self._readings_map = df

    def get_dataframe(self, sensors=None):
        sensor_names = [sensor.name for sensor in sensors]
        session = inspect(self).session
        qry = select(Measurement.datetime, coalesce(Sensor.display_name, Measurement.variable).label("variable"),
                    Measurement.value, Measurement.trial).join(
                        Sensor, onclause=(Measurement.variable == Sensor.name)
                        ).where(
                    Measurement.trial == self.id).where(
                    Measurement.variable.in_(sensor_names)).order_by(Measurement.datetime)
        res = session.execute(qry)
        return pd.DataFrame(res.fetchall(), columns=res.keys())


    def get_files_dataframe(self):
        return pd.DataFrame([{'filename': file.name} for file in self.files])

    def get_stored_readings_map_df(self):
        session = inspect(self).session
        qry = select(Sensor.name, 
                     Sensor.display_name,
                     ).where(
                     Sensor.trial_id == self.id).order_by(Sensor.name)
        res = session.execute(qry)
        return pd.DataFrame(res.fetchall(), columns=res.keys())

    def apply_readings_map(self):
        df = self.readings_map
        sensor_names = {sensor.name: sensor for sensor in self.sensors}
        for row in df.to_dict(orient='records'):
            stored_name = row['name']
            sensor = sensor_names.get(stored_name, None)
            if sensor is not None:
                for key in ['display_name']:
                    if row[key] != getattr(sensor, key):
                        setattr(sensor, key, row[key])
            else:
                sensor = Sensor(name=row['name'], 
                                display_name=row['display_name'],)
                self.sensors.append(sensor)

@event.listens_for(Trial, 'after_insert')
def receive_before_insert(mapper, conn, target):
    ''' Insert the dataframe into the measurements database just after the trial is inserted. '''
    df = target.dataframe
    if df is not None:
        df['trial'] = target.id
        conn.execute(Measurement.__table__.insert(), df.to_dict(orient="records"))
        print('Successfully committed trial data.')

@event.listens_for(Trial, 'before_delete')
def receive_before_insert(mapper, conn, target):
    session = inspect(target).session
    stmt = delete(Measurement).where(Measurement.trial == target.id)
    session.execute(stmt)
    print('Successfully deleted trial data.')


class File(Base):
    __tablename__ = 'files'
    id = Column(Integer, Sequence('files_id_seq'),  primary_key=True)
    name = Column(String, nullable=False)
    data = Column(LargeBinary, nullable=False)
    mime = Column(String, nullable=False)
    trial_id = Column(Integer, ForeignKey('trial.id'))
    trial = relationship("Trial", backref=backref("files", cascade='all, delete-orphan'))

class Sensor(Base):
    __tablename__ = 'sensor'
    id = Column(Integer, Sequence('sensor_id_seq'),  primary_key=True)
    name = Column(String) # Name for the sensor in the original data
    display_name = Column(String) # Optional alternative name for the sensor

    trial_id = Column(Integer, ForeignKey('trial.id'))
    trial = relationship("Trial", backref="sensors")

    __table_args__ = (
            UniqueConstraint('trial_id', 'name', name='uq_trial_sensor_name'),
            UniqueConstraint('trial_id', 'display_name', name='uq_trial_sensor_display_name'))

    def get_display_name(self):
        if self.display_name == '' or self.display_name is None:
            return self.name
        return self.display_name

class GroupSensorName(Base):
    __tablename__ = 'group_sensor_names'
    id = Column(Integer, Sequence('group_sensor_name_id_seq'),  primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Group(Base):
    __tablename__ = 'grouping'
    id = Column(Integer, Sequence('group_id_seq'),  primary_key=True)
    key = Column(String)
    value = Column(String)
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship("Project", backref="groups")
    sensor_name_objects = relationship("GroupSensorName", secondary=sensor_group_association)

    __table_args__ = (
            UniqueConstraint('project_id', 'key', 'value', name='uq_groups'),)

    def get_sensor_names(self):
        return tuple(name_object.name for name_object in self.sensor_name_objects)

    def set_sensor_names(self, session, sensor_names):
        qry = select(GroupSensorName.name).where(GroupSensorName.name.in_(sensor_names))
        existing_sensor_names = session.execute(qry).scalars().all()
        missing_sensor_names = list(set(sensor_names) - set(existing_sensor_names))
        new_sensors = [GroupSensorName(name=sensor_name) for sensor_name in missing_sensor_names]
        session.add_all(new_sensors)
        qry = select(GroupSensorName).where(GroupSensorName.name.in_(sensor_names))
        sensor_name_objects = session.execute(qry).scalars().all()
        self.sensor_name_objects = sensor_name_objects

    def get_sensor_ids(self, dataset):
        sensor_names = self.get_sensor_names()
        return [sensor.id for sensor in dataset.sensors if sensor.get_display_name() in sensor_names]


class Dataset(Base):
    __tablename__ = 'dataset'
    id = Column(Integer, Sequence('dataset_id_seq'),  primary_key=True)
    name = Column(String, unique=True)
    notes = Column(String)
    start_datetime = Column(TIMESTAMP, nullable=False)
    end_datetime = Column(TIMESTAMP, nullable=False)
    trial_id = Column(Integer, ForeignKey('trial.id'), nullable=False)

    trial = relationship("Trial", backref='datasets')
    projects = relationship("Project", backref='datasets', secondary=project_datasets_association)

    @property
    def sensors(self):
        return self.trial.sensors

    @property
    def trial_name(self):
        return self.trial.name

    def get_grouped_df(self, groups):
        ''' Get the dataframe for the selected groups. '''
        session = inspect(self).session
        group_ids = [group.id for group in groups]
        qry = select(Sensor).join(sensor_group_association).join(Group).where(Group.id.in_(group_ids))
        sensors = session.execute(qry).scalars().all()
        df = self.get_dataframe(sensors)

        sensor_ids = [sensor.id for sensor in sensors]
        qry = select(Sensor.name, Group.value).where(Sensor.id.in_(sensor_ids))
        group_map = session.execute(qry)
        group_map_df = pd.DataFrame(group_map.fetchall(), columns=group_map.keys())
        return pd.merge(df, group_map_df, left_on='variable', right_on='name', how='left')


    def get_exclusions_df(self, view_col=False):
        tuples = [(exclusion.id, [sensor.get_display_name() for sensor in exclusion.sensors], 
                   exclusion.start_datetime, exclusion.end_datetime)
                for exclusion in self.exclusions]
        columns = ['id', 'sensors', 'start_datetime', 'end_datetime']
        df = pd.DataFrame(tuples, columns=columns)
        if view_col:
            df['view'] = False
        return df

    def update_exclusions(self, df):
        for row in df.reset_index().to_dict(orient='records'):
            id = row['id']
            session = inspect(self).session
            qry = select(Exclusion).where(Exclusion.id == id)
            exclusion = session.execute(qry).scalar()
            exclusion.check_update(row)

    def remove_exclusions(self, df):
        for row in df.reset_index().to_dict(orient='records'):
            id = row['id']
            session = inspect(self).session
            qry = select(Exclusion).where(Exclusion.id == id)
            exclusion = session.execute(qry).scalar()
            session.delete(exclusion)

    def add_new_exclusions(self, df):
        for row in df.reset_index().to_dict(orient='records'):
            if row['sensors'] is None:
                sensor_names = [sensor.name for sensor in self.trial.sensors]
            else:
                sensor_names = row['sensors']
            sensors = [sensor for sensor in self.trial.sensors if sensor.get_display_name() in sensor_names]
            exclusion = Exclusion(start_datetime=row['start_datetime'], 
                                  end_datetime=row['end_datetime'],
                                  sensors=sensors)
            self.exclusions.append(exclusion)

    def make_meas_query(self, sensors):
        # Get all measurements for the dataset's trial       
        sql_query = select(Measurement.datetime, coalesce(Sensor.display_name, Measurement.variable).label("variable"),
            Measurement.value, Measurement.trial).join(
                Sensor, onclause=(Measurement.variable == Sensor.name)
                ).where(
            Measurement.trial == self.trial.id).order_by(Measurement.datetime)
        # Only between the start and end datetime of the dataset
        sql_query = sql_query.where(Measurement.datetime.between(self.start_datetime, self.end_datetime))
        # Only for the selected sensors
        sql_query = sql_query.where(Measurement.variable.in_([sensor.name for sensor in sensors]))
        # Exclude the measurements that are in the exclusion ranges
        for exclusion in self.exclusions:
            for sensor in exclusion.sensors:
                variable_name = sensor.name
                start, end = exclusion.start_datetime, exclusion.end_datetime
                my_filter = and_(Measurement.variable == variable_name, Measurement.datetime.between(start, end))
                sql_query = sql_query.where(~my_filter)
        # Return the statement as a string
        return sql_query

    def get_dataframe(self, sensors=None):
        session = inspect(self).session
        qry = self.make_meas_query(sensors)
        qry_text = str(qry.compile(compile_kwargs={"literal_binds": True}))
        res = session.execute(text(qry_text))
        df = pd.DataFrame(res.fetchall(), columns=res.keys())
        dtypes = {'datetime': 'datetime64[ns]', 'variable': str, 'value': 'float32'}
        df = df.astype(dtypes)
        return df

    def row_count(self, sensors=None):
        session = inspect(self).session
        qry = self.make_meas_query(sensors)
        qry = select(func.count('*')).select_from(qry.subquery())
        return session.execute(qry).scalar()

    def filtered_sensors(self, sensor_names):
        if sensor_names is None:
            return self.trial.sensors
        return [sensor for sensor in self.trial.sensors if sensor.name in sensor_names]

    def get_sensor_groups(self):
        qry = select(Sensor.group,
        func.group_concat(Sensor.name)).group_by(Sensor.group)
        return inspect(self).session.execute(qry).all()

    def get_filtered_sensors(self, project, *pargs):
        sensors = self.sensors
        for filter_list in pargs:
            for filter in filter_list:
                if filter['filter_type'] == 'group_filter':
                    key = filter['selected_key']
                    value = filter['selected_value']
                    session = inspect(self).session
                    qry = select(Group).where(Group.project_id == project.id, Group.key == key, Group.value == value)
                    group = session.execute(qry).scalar()
                    if group is not None:
                        keep_sensor_ids = group.get_sensor_ids(self)
                    else:
                        keep_sensor_ids = []
                elif filter['filter_type'] == 'sensor_filter':
                    key = filter['selected_key']
                    value = filter['selected_value']
                    keep_sensor_ids = [sensor.id for sensor in sensors if getattr(sensor, key) == value]
                elif filter['filter_type'] == 'reference_filter':
                    key = filter['selected_key']
                    value = filter['selected_value']
                    keep_sensor_ids = [sensor.id for sensor in sensors if getattr(sensor, key) != value]
                sensors = [sensor for sensor in sensors if sensor.id in keep_sensor_ids]
        return sensors

    def set_exclusions_df(self, selections):
        commited_exclusions = self.get_exclusions_df()

        # Prepare the dataframes
        current_ids = commited_exclusions['id'].tolist()
        existing_exclusions = selections[
            selections['id'].isin(current_ids)]
        new_exclusions = selections[
            ~selections['id'].isin(current_ids)]        
        deleted_exclusions = commited_exclusions[
            ~commited_exclusions['id'].isin(selections['id'])]

        self.update_exclusions(existing_exclusions)
        self.add_new_exclusions(new_exclusions)
        self.remove_exclusions(deleted_exclusions)

class Exclusion(Base):
    __tablename__ = 'exclusion'
    id = Column(Integer, Sequence('exclusion_id_seq'),  primary_key=True)
    dataset_id = Column(Integer, ForeignKey('dataset.id'), nullable=False)
    start_datetime = Column(TIMESTAMP, nullable=False)
    end_datetime = Column(TIMESTAMP, nullable=False)

    sensors = relationship("Sensor", backref='exclusions', secondary=exclusion_sensor_association)
    dataset = relationship("Dataset", backref=backref("exclusions", cascade='all, delete-orphan'))

    def check_update(self, row):
        if self.start_datetime != row['start_datetime']:
            self.start_datetime = row['start_datetime']
        if self.end_datetime != row['end_datetime']:
            self.end_datetime = row['end_datetime']

        sensor_names = row['sensors']
        existing_sensor_names = [sensor.get_display_name() for sensor in self.sensors]
        if existing_sensor_names != sensor_names:
            sensor_dict = {sensor.get_display_name(): sensor for sensor in self.dataset.sensors}
            sensors = [sensor_dict[sensor_name] for sensor_name in row['sensors']]
            self.sensors = sensors

class Content(Base):
    __tablename__ = 'content'
    id = Column(Integer, Sequence('content_id_seq'),  primary_key=True)
    content_table = Column(String)
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship("Project", backref=backref("contents", cascade='all, delete-orphan'))

    __mapper_args__ = {
        'polymorphic_identity': 'content',
        'polymorphic_on': content_table
    }


class Visualisation(Content, VisualisationBehaviour):
    __tablename__ = 'visualisation'
    id = Column(Integer, ForeignKey('content.id'), primary_key=True)
    x_axis = Column(String)
    y_axis = Column(String)
    color = Column(String)
    plot_type = Column(String)
    plot_format = Column(String)
    preprocess = Column(String)
    lower_limit = Column(Integer)
    upper_limit = Column(Integer)
    quantity = Column(Integer)
    detrend_units = Column(String)
    reference_sensor = Column(String)
    dataset_id = Column(Integer, ForeignKey('dataset.id'))
    dataset = relationship("Dataset", backref="visualisations")
    sensors = relationship("Sensor", secondary=visualisation_sensor_association)
    
    reference_sensor_id = Column(Integer, ForeignKey('sensor.id'))
    reference_sensor = relationship("Sensor", foreign_keys=[reference_sensor_id])

    __table_args__ = (
        CheckConstraint(
            "preprocess != 'tx' OR reference_sensor_id IS NOT NULL",
            name='check_tx_requires_reference_sensor'),
            )

    __mapper_args__ = {
        'polymorphic_identity': 'visualisation'
    }


class TextNote(Content):
    __tablename__ = 'text_note'
    id = Column(Integer, ForeignKey('content.id'), primary_key=True)
    text = Column(String)
    __mapper_args__ = {
        'polymorphic_identity': 'text_note'
    }

    def get_title(self, index):
        return f"Item {index} - Text Note"

    def render(self):
        return self.text

class Image(Base):
    __tablename__ = 'images'
    id = Column(Integer, Sequence('image_id_seq'),  primary_key=True)
    name = Column(String, nullable=False)
    data = Column(LargeBinary, nullable=False)

    trial_id = Column(Integer, ForeignKey('trial.id'))
    trial = relationship("Trial", backref="images")

    def image(self):
        return PImage.open(io.BytesIO(self.data))

class Metadata(Base):
    __tablename__ = 'metadata'
    id = Column(Integer, Sequence('metadata_id_seq'),  primary_key=True)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)

class Measurement(Base):
    __tablename__ = 'measurement'
    datetime = Column(TIMESTAMP)
    variable = Column(String)
    value = Column(FLOAT)
    trial = Column(Integer)
    __table_args__ = (PrimaryKeyConstraint('datetime', 'variable', 'trial'),)