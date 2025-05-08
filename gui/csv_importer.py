# Original Code by: Mary Dutton, MSc Data Science 2024/25 Project Group 4
# Purpose: CSV File Importer - included in the Trial Maker UI
 
import pandas as pd
import streamlit as st

@st.dialog("Readings Importer", width="large")
def run_csv_importer():
    ########################### Selection of file to import ###########################
    st.title('Select File to Load and Preview') 

    file=st.file_uploader("Select the File to Load - Preferred File Types .CSV and.TXT", type=['.csv', '.xlsx', '.xls', '.txt'], accept_multiple_files=False)

    if file is not None:
        if file.name.endswith(('.csv', '.txt')):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xlsx','.xls')):
            df = pd.read_excel(file)
        else:
            # If the file is not as specified
            raise ValueError("Unsupported file format. Please provide a CSV, TXT or Excel file.")
        
        # Preview the raw data
        st.write("Preview of the Raw Data:")
        st.write(df.head(10))  # Show the first 10 rows for a quick preview


    ########################### Selection of rows to exclude ###########################
        st.title('Select Rows to Exclude and Preview')
        
        # Allow the user to input the number of rows to skip
        st.write("Specify Rows to Skip after the Header (Any Additional Header Rows that are not Required):")

        rows_to_skip_after_header = st.number_input("Number of Rows to Skip after the Header (default is 0):", 
                                                    min_value=0,            # The min value that can be entered 
                                                    max_value=len(df)-1,    # Ensure it doesn't exceed total rows
                                                    value=0,                # The default value; the increment amount 
                                                    step=1)                 # The increment amount 
        
        # Reload the file with the specified number of rows to skip
        if file.name.endswith(('.csv', '.txt')):
            # Loading the file again was causing error, this resets the buffer
            file.seek(0)
            df2 = pd.read_csv(file, skiprows=range(1, rows_to_skip_after_header + 1), header=0)
        elif file.name.endswith(('.xlsx', '.xls')):
            # Loading the file again was causing error, this resets the buffer
            file.seek(0)
            df2 = pd.read_excel(file, skiprows=range(1, rows_to_skip_after_header + 1), header=0)
        else:
            # If the file is not as specified
            raise ValueError("Unsupported File Format. Please Provide a CSV, TXT or Excel file.")
        
        # Show the updated data preview after skipping rows
        st.write("Updated Data Preview (after skipping specified rows):")
        st.write(df2.head(4))

    ######################### Selection of columns to exclude #########################
        st.title('Select Columns to Exclude')
        
        # Exclude columns from the loaded data to process
        Exclude_Columns = st.multiselect("Select Columns to Exclude", list(df2.columns))

        if Exclude_Columns:
            # New dataframe excluding the specified columns
            df2 = df2.drop(columns=Exclude_Columns)

            st.write('Preview of Data After Excluding Columns', df2.head(4))
        # st.write('Excluded Columns:', Exclude_Columns)


    ###### A function to print a preview of the final data after the import and ######
    ######################### datetime creation or selection #########################
        def preview_final_data(df2):
            # Specify the first column of the final dataframe
            first_column_name = 'datetime'
            
            # Rearrange dataFrame with the specified column first
            df2 = df2[[first_column_name] + [col for col in df2.columns if col != first_column_name]]
            
            # Print a preview of the final data
            st.title('Final Data for Trial Maker')
            st.write(df2.head(4))
            return df2 
        

    ########################### Creation of DateTime Column ###########################
        # Creation of the Required DateTime Format
        st.title('Select or Create DateTime Column')

        # Define the expected datetime format
        expected_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%m/%d/%Y %H:%M:%S',  # Month first
            '%d/%m/%Y %H:%M:%S',  # Day first
            '%m/%d/%y %H:%M:%S',
            '%d/%m/%y %H:%M:%S'
        ]
        
        # Function to parse date with multiple formats
        def parse_datetime(value, formats):
            for fmt in formats:
                try:
                    return pd.to_datetime(value, format=fmt)
                except ValueError:
                    continue
            return None  # Return None if no format matches
        
        # Initialize datetime to None
        datetime = None
        # Placeholder for dropping original columns with datatypes datetime, separate date and time columns
        drop_columns = []


    #### Section to process the data when there is a DateTime variable in the data ####
        # Select DateTime column
        dt_column = st.selectbox('Choose a DateTime Column:', [None] + list(df2.columns))
    
        
    ################ Processes the data when there is a DateTime column ################
        if dt_column is not None:
            try:
                # Convert the column to datetime format
                df2[dt_column] = pd.to_datetime(df2[dt_column])
                
                # Check if all values match the expected format
                df2['formatted_check'] = df2[dt_column].apply(lambda x: parse_datetime(x, expected_formats))
                
                datetime = 'datetime'
                
                if (df2['formatted_check'] == df2[dt_column].astype(str)).all():
                    df2.rename(columns={dt_column: 'datetime'}, inplace=True) 
                    st.write('Resulting DateTime column:')
                    st.write(df2[[datetime]].head(4)) 

                    tz = st.radio("Timezone:",("Europe/London", "UTC"))

                    # Drop the formatted_check column
                    df2.drop(columns=['formatted_check'], inplace=True)

                    # Print a preview of the final data
                    preview_final_data(df2)

                    if st.button("Confirm", key='confirm_1'):
                        df2['datetime'] = df2['datetime'].dt.tz_localize(tz)
                        st.session_state.imported_file = df2
                        st.rerun()

                # If not the expected format print a message   
                else:
                    st.write('Selected column is not in the correct DateTime format.')
                
            except ValueError:
                st.error('Selected column is not in the correct DateTime format.')

        
    ################ Processes the data when there is no DateTime column ################
    ################## Provide options to select Date and Time columns ##################
        elif datetime is None:
            default_option = 'None'
            d_column = st.selectbox('Choose a Date Column (If no DateTime Data Available):', [default_option] + list(df2.columns))
            t_column = st.selectbox('Choose a Time Column (If no DateTime Data Available):', [default_option] + list(df2.columns))

            # Check if valid columns are selected
            if d_column != default_option and t_column != default_option:
                # Check if the selected columns can be converted to datetime
                try:
                    df2['datetime'] = pd.to_datetime(df2[d_column] + ' ' + df2[t_column])
                # Error message publish incorrect variables are selected for date and time  
                except TypeError:
                    st.error('Could not create a DateTime column. Please check the format of the selected columns.')
                    quit()

                # If correct variables are selected for date and time proceed with running the rest of the code  
                try:
                    # Check if all values match the expected format
                    df2['formatted_check'] = df2['datetime'].apply(lambda x: parse_datetime(x, expected_formats))
                    if (df2['formatted_check'] == df2['datetime'].apply(lambda x: parse_datetime(x, expected_formats))).all():
                        Datetime = 'datetime'
                        st.write('Resulting DateTime column:')
                        st.write(df2[[Datetime]].head(4))
                        
                        tz = st.radio("Timezone:",("Europe/London", "UTC"))
                    
                        # Drop the formatted_check column and the original date and time columns 
                        # if they were used to create the new Datetime colum
                        df2.drop(columns=[d_column, t_column,'formatted_check'], inplace=True)

                        # Print a preview of the final data
                        preview_final_data(df2)

                        if st.button("Confirm", key='confirm_2'):
                            df2['datetime'] = df2['datetime'].dt.tz_localize(tz)
                            st.session_state.imported_file = df2
                            st.rerun()
                    # If date is not the expected format print a message   
                    else:
                        st.write('Could not create a DateTime column. Please check the format of the selected columns.')
                except ValueError:
                    st.error('Could not create a DateTime column. Please check the format of the selected columns.')
                    quit()
        else:
            st.write('No DateTime column selected or created.') 

        
