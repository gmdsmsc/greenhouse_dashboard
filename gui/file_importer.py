# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st
from app.file_parser import detect_types
from app.util import gen_float_cols
from app.file_importer import FileReaderBehaviours, CSVReaderBehaviours, ExcelReaderBehaviours

class FileReaderGUI(FileReaderBehaviours):

    def __init__(self, file, filetype_behaviour):
        self.file = file
        self.filetype_behaviour = filetype_behaviour
 
    def start(self):
        if self.filetype_behaviour == ExcelReaderBehaviours:
            sheet_names = self.filetype_behaviour.get_sheet_names(self)
            if len(sheet_names) > 1:
                selected_sheet = st.selectbox("Select Sheet", options=sheet_names)
            else:
                selected_sheet = None
        else:
            selected_sheet = None
        
        st.write("Below presents a preview of the file's contents. " \
        'If the file parser has successfully detected the date/time data, ' \
        ' a further data preview will be displayed for the interpreted data. ' \
        'If the file parser has failed to detect a date/time column, ' \
        'only the raw file preview will be displayed. It may be necessary ' \
        'to use the skip row button if datetime column date starts later in the file. ' )

        st.title("Raw Data Preview:")

        skiprows = st.number_input("Number of Rows to Skip:", min_value=0, step=1)
        if selected_sheet is not None:
            df_display = self.read_display_preview(self.file, skiprows=skiprows, sheet_name=selected_sheet)
        else:
            df_display = self.read_display_preview(self.file, skiprows=skiprows)

        st.dataframe(df_display, hide_index=True)

        if selected_sheet is not None:
            df_raw = self.read_detection_preview(self.file, skiprows=skiprows, sheet_name=selected_sheet)
        else:
            df_raw = self.read_detection_preview(self.file, skiprows=skiprows)

        types = list(detect_types(df_raw))

        check1 = 'datetime' not in types
        check2 = not('date' in types and 'time' in types)
        if check1 and check2:
            st.warning('No DateTime or Date and Time column(s) detected.')
        else:
            if 'datetime' in types:
                dt_col_names = (df_raw.columns[types.index('datetime')], )
            elif 'date' in types and 'time' in types:
                dt_col_names = df_raw.columns[types.index('date')], df_raw.columns[types.index('time')]
            else:
                dt_col_names = (df_raw.columns[types.index('time')], )
            dt_col_indexes = [df_raw.columns.get_loc(name) for name in dt_col_names]

            float_cols = list(gen_float_cols(df_raw, dt_col_indexes))

            st.title("Import Data Preview:")

            st.write("Below presents a preview of the data to be imported. " \
            "Select specific columns if not all the data are required." )

            with st.expander("Select Specific Columns"):
                cols_to_keep = st.multiselect("Columns to Include:", float_cols, default=float_cols)
            cols_to_keep_indexes = [df_raw.columns.get_loc(col) for col in cols_to_keep]
            usecol_indexes = sorted(list(dt_col_indexes) + cols_to_keep_indexes)

            # Create a mapping from old indices to new indices based on columns_to_use
            index_mapping = {old_idx: new_idx for new_idx, old_idx in enumerate(usecol_indexes)}
            # Update selected columns based on the new indices
            dt_col_indexes = [index_mapping[col] for col in dt_col_indexes if col in index_mapping]

            # Preview the preprocessed data
            if len(dt_col_indexes) == 1:       
                if selected_sheet is not None:
                    df_preview = self.read_preview_with_datetime_column(self.file, *dt_col_indexes, usecols=usecol_indexes, skiprows=skiprows, sheet_name=selected_sheet)
                else:
                    df_preview = self.read_preview_with_datetime_column(self.file, *dt_col_indexes, usecols=usecol_indexes, skiprows=skiprows)
            else:
                if selected_sheet is not None:
                    df_preview = self.read_preview_with_date_and_time_column(self.file, *dt_col_indexes, usecols=usecol_indexes, skiprows=skiprows, sheet_name=selected_sheet)
                else:
                    df_preview = self.read_preview_with_date_and_time_column(self.file, *dt_col_indexes, usecols=usecol_indexes, skiprows=skiprows)

            st.dataframe(df_preview, hide_index=True)

            st.write("**IMPORTANT:** " \
                     "It is not possible to detect timezone information automatically at present. " \
                    "Set the timezone of the incoming data manually here. It will be converted to " \
                    "the timezone of the server on import. "\
                    "Please ensure that the timezone is correct before proceeding. " \
)

            tz = st.radio("Timezone:",("Europe/London", "UTC"))

            st.session_state.parameters = (self.file, skiprows, dt_col_indexes, usecol_indexes, tz)


@st.dialog("Import Sensor Readings", width="large")
def uploader_modal():
    ''' Function to display the modal for confirming the attachment of sensor readings '''
    
    if 'parameters' not in st.session_state:
        st.session_state.parameters = None
    st.title('Select File to Load and Preview')
    file = st.file_uploader("Select the File to Load - Preferred File Types .CSV and.TXT", 
                            type=['.csv', '.xlsx', '.xls', '.txt'], accept_multiple_files=False)
    if file is not None:
        if file.name.endswith(('.csv', '.txt', '.CSV', '.TXT')):
            file_reader = FileReaderGUI(file, CSVReaderBehaviours)
        elif file.name.endswith(('.xlsx', '.xls', '.XLSX', '.XLS')):
            file_reader = FileReaderGUI(file, ExcelReaderBehaviours)
        else:
            st.warning("Unsupported file format. Please provide a CSV, TXT or Excel file.")
            st.session_state.parameters = None
            file_reader =  None
        
        if file_reader is not None:
            file_reader.start()

        if st.session_state.parameters is not None:
            file, skiprows, dt_col_indexes, usecol_indexes, tz = st.session_state.parameters
            if len(usecol_indexes) > len(dt_col_indexes):
                if st.button("Confirm"):
                    with st.spinner("Interpreting Full File..."):
                        df = file_reader.read_full(file, *dt_col_indexes, usecols=usecol_indexes, skiprows=skiprows)
                        df['datetime'] = df['datetime'].dt.tz_localize(tz)
                        st.session_state.imported_file = df
                        st.rerun()

