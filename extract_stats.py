# imports
import sys
sys.path.append("bin")
import tabula # tabula-py
import pandas as pd
import re
import numpy as np
from math import nan
import math
import os
import fitz  # PyMuPDF


#============================HELPER FUNCTIONS=================================================
# TODO: MOVE THIS TO ANOTHER FILE

def get_pdf_list():
    '''
    Gets a list of all files in the PDFs folder

    Args:
        None
    Returns:
        list(str): a list of pdf paths in PDFs folder

    '''
    # get the root directory
    root = os.path.abspath(os.curdir)
    # make a list of the files in the pdfs directory
    file_list = os.listdir("PDFs")
    out = []
    out_dict = {'fname': []}
    # get the file path for each pdf
    for pdf in file_list:
        # make sure they're all pdfs
        if not pdf.endswith('.pdf'):
            raise SystemError(f'Expected only pdfs. Got {pdf}')
        path = root + "\\PDFs\\" + pdf
        out.append(path)
        out_dict["fname"].append(pdf)
    return out, out_dict


def enter_values(keys, values, out_dict, idx):
    """
    Helper function to append values to dict or add 
    if they dont already exist. Modifies out_dict in
    place

    Args:
        keys (list(str)): A list of keys for the output dictionary
        values (list(any)): A list of values corresponding to the keys
        out_dict: dictionary to be modified
        idx: the index of the document
        

    Returns:

    """
    assert(len(keys) == len(values))
    nfiles = len(out_dict['fname'])
    for key, value in zip(keys, values):
        # if we don't have an entry yet, intialize the row
        if key not in out_dict:
            out_dict[key] = [nan] * nfiles

        out_dict[key][idx] = value


def values_to_float(values):
    """
    Helper function to clean data and convert to float. 
    NOTE: Turns percentages to ints (e.g. 25% -> 25)
    
    Args:
        values (list(str/float)): A list of values to be processed
    
    Returns:
        list(float): Preprocessed list of values
    
    """
    out = []
    for v in values:
        if type(v) == float:
            out.append(v)
        elif type(v) == str:
            # Check if there is a number in the string
            num_str = re.search("\d+\.?\d*", v)
            if num_str:
                # if there is, save that value
                out.append(float(num_str[0]))
            else:
                # otherwise output nan
                out.append(nan)
        elif type(v) == np.float64:
            out.append(float(v))
        else:
            raise TypeError(f"Expected a float or str. Received {type(v)}")
    
    return out


def str_to_float(s):
    '''
    Helper function to convert strings to floats
    Args
        s(str): string to be converted to float
    Returns
        float: float of string or nan if contains no number
    '''
    if re.search("\d+\.?\d*", s):
        return float(s)
    else:
        return nan


def split_column(column):
    """
    Split strings in a column

    Args:
        column (list(str/nan)): A list of strings of format "float float"

    Returns:
        list(float): A list of the separated values
    """
    out = []
    # Split each item in column
    for v in column:
        if type(v) == str:
            out.append([str_to_float(x) for x in v.split()])
        elif math.isnan(v):
            out.append([nan, nan])
        else:
            raise TypeError(f"Expected a str or nan. Received {type(v)}")

    return out


#===============================INDIVIDUAL FIELD PROCESSING====================================
# TODO: MOVE THIS TO ANOTHER FILE
def extract_text_between_headings(pdf_path, start_heading, end_heading):
    ''' 
    Pulls text between start_heading and end_heading, only for the first occurrence.
    Note this is a pretty slow/inefficient way to do this because we load in the pdf
    individually for each field. May also need to add in flexibility for variety in field
    headers.

    Args:
        pdf_path(str): the path to the pdf to be read
        start_heading(str): The string to match before the field of interest
        end_heading(str): the string to match after the field of interest

    Returns:
        str: the text of the field of interest
    '''
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    
    text = ""
    found_start = False
    found_end = False

    # Iterate through each page
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        page_text = page.get_text("text")
        
        if found_start and not found_end:
            # Find the end position of the heading only if start heading has been found
            end_pos = page_text.find(end_heading)
            if end_pos != -1:
                # Extract text up to the end heading
                text += page_text[:end_pos]
                found_end = True
                break
            else:
                # Collect text from where start heading was found
                text += page_text
        else:
            # Find the start and end positions of the headings
            start_pos = page_text.find(start_heading)
            end_pos = page_text.find(end_heading)
            
            if start_pos != -1:
                # If end heading is found on the same page after start heading
                if end_pos != -1 and end_pos > start_pos:
                    text += page_text[start_pos + len(start_heading):end_pos]
                    found_end = True
                    break
                else:
                    # Collect text from the start heading to the end of the page
                    text += page_text[start_pos + len(start_heading):]
                    found_start = True

    # If start heading is found but end heading is not found by the end of the document
    if found_start and not found_end:
        text += page_text
    
    return text.strip()


def remove_pg_header(text):
    ''' 
    Should remove the doc id, date, etc
    
    Args
        text(str): A string to be cleaned
    
    Returns
        str: the cleaned string
    '''
    regex = "( \n)*.*\n\d{1,2}\/\d{1,2}\/\d{2,4} \n \nPage \d* of \d*"
    return re.sub(regex, '', text)

def get_individual_headers_var_names():
    # TODO: FIX THE STANDARD POLYSOMNOGRAM: #CHANNELS WITHIN PARENTHESES
    pdf_headers = ["Name:",
        "Study Date:",
        "Date of Birth:",
        "Hospital No:",
        "Encounter:",
        "Ordering MD:",
        "Verified By:",
        "Study No:",
        "Start Time:",
        "Lights Off Time:",
        "End Time:",
        "Lights On Time:",
        "File Name:",
        "INTRODUCTION",
        "STANDARD POLYSOMNOGRAM",
        "EEG  (",
        "Muscle tone  (",
        "Eye movements (",
        "Leg movements (",
        "Cardiac rhythm and rate (",
        "Airflow:",
        "Respiratory sounds:",
        "Effort:",
        "Oxygen saturation (SaO2):",
        "SpO2 signal reliability:",
        "End Tidal CO2:",
        "Appearance/behavior:",
        "INTERPRETATION",
        "SLEEP ARCHITECTURE",
        "POSITION:",
        "BREATHING PATTERN/RESPIRATORY EVENTS",
        "GAS EXCHANGE",
        "EKG \n",
        "MOVEMENTS",
        "IMPRESSION:",
        "COMMENT:",
        "SLEEP PARAMETERS"]
    
    var_names = ["name",
               "study_date",
               "birth_date",
               "hospital_number",
               "encounter",
               "ordering_name",
               "verified_name",
               "study_number",
               "start_time",
               "lights_off_time",
               "end_time",
               "lights_on_time",
               "file_name",
               "introduction",
               "eeg_channel_count",
               "muscle_tone",
               "eye_movements",
               "leg_movements",
               "cardiac_rhythm_rate",
               "airflow",
               "respiratory_sounds",
               "effort",
               "saO2:",
               "spO2_signal_reliability:",
               "end_tidal_CO2",
               "appearance_behavior",
               "sleep_architecture_report",
               "position_report",
               "breathing_pattern_events",
               "gas_exchange",
               "ekg",
               "movements",
               "impression_report",
               "comment"]
    
    return pdf_headers, var_names

#===============================TABLE PROCESSING FUNCTIONS=====================================
# TODO: MOVE THIS TO ANOTHER FILE
# N.B. I realize hardcoding this is messy but hopefully if something goes wrong it will break and alert the user
def extract_sleep_params(pdf_path, out_dict, idx):
    pdf_headers = [
    "Time in Bed (TIB):",
    "Sleep Period (Sleep Onset to Final Wakening):",
    "Total Sleep Time (TST):",
    "Waking After Sleep Onset (WASO):",
    "Sleep Efficiency (TST/TIB):",
    "Sleep Maintenance (TST/SPT): ",
    "Sleep Latency:",
    "STAGE DISTRIBUTION "]

    field_names = [ 
    'time_in_bed',
    'sleep_period',
    'total_sleep_time',
    'wake_after_sleep_onset',
    'sleep_efficiency',
    'sleep_maintenance_efficiency',
    'sleep_latency'
    ]

    exclude = []
    values = []

    for i in range(len(pdf_headers) - 1):
        if not (i in exclude):
            txt = extract_text_between_headings(pdf_path, pdf_headers[i], pdf_headers[i+1])
            values.append(txt)

    values = values_to_float(values)
    enter_values(field_names, values, out_dict, idx)
    return out_dict

def extract_stage_dist(table_list, out_dict, idx):
    field_names = [
    # stage distribution
    'time_stage_n1', 'percentage_stage_n1', 'latency_stage_n1',
    'time_stage_n2', 'percentage_stage_n2', 'latency_stage_n2',
    'time_stage_3', 'percentage_stage_3', 'latency_stage_3',
    'time_stage_4', 'percentage_stage_4', 'latency_stage_4',
    'time_stage_n3', 'percentage_stage_n3', 'latency_stage_n3',
    'time_stage_rem', 'percentage_stage_rem', 'latency_stage_rem',
    'time_stage_nrem', 'percentage_stage_nrem',
    'time_stage_wake'
    ]

    df = table_list[0]
    values = list(df.iloc[:,1:].values.flatten())
    del values[20]
    del values[21]
    del values[21]
    values = values_to_float(values)
    
    enter_values(field_names, values, out_dict, idx)
    return out_dict


def extract_arousals(table_list, out_dict, idx):
    field_headers = [   
    # arousals
    'number_arousals', 'number_arousals_rem', 
    'number_arousals_nrem', 
    'index_arousals', 
    'index_arousals_rem', 
    'index_arousals_nrem'
    ]

    field_names = ['total_' + v for v in field_headers] + ['apnea_hypopnea_' + v for v in field_headers] + ['resp_dist_' + v for v in field_headers]

    df = table_list[1]

    values = df.iloc[::2,1:].values
    values = np.delete(values, 4, 1)
    values = np.delete(values, 5, 1)
    values = list(values.flatten())
    enter_values(field_names, values, out_dict, idx)
    return out_dict


def extract_leg_mvmts(table_list, out_dict, idx):
    field_names = [
    # periodic leg movements
    'number_periodic_limb_movements', 'index_periodic_limb_movements',
    'number_periodic_limb_movements_arousal', 'index_periodic_limb_movements_arousal'
    ]

    df = table_list[2]
    values = list(df.iloc[:,1:].values.flatten())
    enter_values(field_names, values, out_dict, idx)
    return out_dict


def extract_resp_analysis(table_list, out_dict, idx):
    field_names = [    
    # minutes sleep/body position
    'time_supine', 'percent_supine', 'time_non_supine', 'percent_non_supine',
    'time_supine_rem', 'percent_supine_rem', 'time_non_supine_rem', 'percent_non_supine_rem',
    'time_supine_nrem', 'percent_supine_nrem', 'time_non_supine_nrem', 'percent_non_supine_nrem'
    ]
    df = table_list[3]
    df.iloc[1:, 1:3].values
    a = df.iloc[1:, 1:3].values
    b = np.array(split_column(df.iloc[1:, 3].values))
    values = np.concatenate((a, b), axis=1)
    values = values_to_float(list(values.flatten()))

    enter_values(field_names, values, out_dict, idx)
    return out_dict

def extract_baseline_ranges(table_list, out_dict, idx):
    field_headers = ["oxygen_saturation",
                 "respiratory_rate",
                 "tcCO2",
                 "heart_rate"
                 ]

    field_names = ['room_air_rem_' + v for v in field_headers] + ['room_air_nrem_' + v for v in field_headers] + ['cpap_o2_rem_' + v for v in field_headers] + ['cpap_o2_nrem_' + v for v in field_headers]
    df = table_list[4]
    a = df.iloc[1:, 1:3].values
    b = np.array(split_column(df.iloc[1:, 3].values))
    values = np.concatenate((a, b), axis=1)
    values = list(values.flatten())

    enter_values(field_names, values, out_dict, idx)
    return out_dict

def extract_spo2_ranges_sleep(table_list, out_dict, idx):
    field_names = [# SpO2 RANGES IN SLEEP
    'time_sleep_spo2_96_100', 'percent_sleep_spo2_96_100', 'time_sleep_gteq_spo2_96_100', 'percent_sleep_gteq_spo2_96_100',
    'time_sleep_spo2_92_96', 'percent_sleep_spo2_92_96', 'time_sleep_gteq_spo2_92_96', 'percent_sleep_gteq_spo2_92_96',
    'time_sleep_spo2_88_92', 'percent_sleep_spo2_88_92', 'time_sleep_gteq_spo2_88_92', 'percent_sleep_gteq_spo2_88_92',
    'time_sleep_spo2_82_88', 'percent_sleep_spo2_82_88', 'time_sleep_gteq_spo2_82_88', 'percent_sleep_gteq_spo2_82_88',
    'time_sleep_spo2_75_82', 'percent_sleep_spo2_75_82', 'time_sleep_gteq_spo2_75_82', 'percent_sleep_gteq_spo2_75_82',
    'time_sleep_spo2_60_75', 'percent_sleep_spo2_60_75', 'time_sleep_gteq_spo2_60_75', 'percent_sleep_gteq_spo2_60_75',
    'time_sleep_spo2_50_60', 'percent_sleep_spo2_50_60', 'time_sleep_gteq_spo2_50_60', 'percent_sleep_gteq_spo2_50_60',
    'time_sleep_spo2_0_50', 'percent_sleep_spo2_0_50', 'time_sleep_gteq_spo2_0_50', 'percent_sleep_gteq_spo2_0_50',
    # 'time_sleep_spo2_excluded_lt_60_gt_110', 'percent_sleep_spo2_excluded_lt_60_gt_110'
    ]
    
    df = table_list[5]
    values = df.iloc[2:, 1:].values
    values = values_to_float(list(np.stack(values).flatten()))
    enter_values(field_names, values, out_dict, idx)
    return out_dict


def extract_resp_events(table_list, out_dict, idx):
    field_headers = [   
    # respiratory events
    'min_length',
    'max_length',
    'usual_desaturations',
    'greatest_desaturation'
    ]

    field_names = [v + '_rem' for v in field_headers] + [v + '_nrem' for v in field_headers]
    field_names = [v + '_obs' for v in field_names] + [v + '_cent' for v in field_names]

    field_names = list(np.array(field_names).reshape(4,4).T.flatten())
    df = table_list[6]
    a = np.array(split_column(df.iloc[1:, 1].values))
    b = np.array(split_column(df.iloc[1:, 2].values))

    values = list(np.concatenate((a, b), axis=1).flatten())
    
    enter_values(field_names, values, out_dict, idx)
    return out_dict
    

def extract_desat_table(table_list, out_dict, idx):
    field_headers = [   
    # respiratory events
    'avg_o2_saturation',
    'total_num_desaturation',
    'o2_desat_index',
    'avg_lowest_osat_desat',
    'nadir_sao2',
    'time_sat_below_90'
    ]

    field_names = [v + '_wake' for v in field_headers] + [v + '_nrem' for v in field_headers] + [v + '_rem' for v in field_headers] + [v + '_total' for v in field_headers]  
    field_names = list(np.array(field_names).reshape(4,6).T.flatten())
    
    df = table_list[8]
    rows_to_get = [1,3,4,6,7,9]
    values = df.iloc[:,1:].values
    values = list(np.take(values, rows_to_get, axis=0).flatten())
    
    enter_values(field_names, values, out_dict, idx)
    return out_dict
    
def extract_etco2_vals(table_list, out_dict, idx):
    field_names = [
    'time_wake_tcco2_20_30', 'percent_wake_tcco2_20_30', 'time_nrem_tcco2_20_30', 'percent_nrem_tcco2_20_30', 'time_rem_tcco2_20_30', 'percent_rem_tcco2_20_30', 'time_total_tcco2_20_30', 'percent_total_tcco2_20_30',
    'time_wake_tcco2_30_45', 'percent_wake_tcco2_30_45', 'time_nrem_tcco2_30_45', 'percent_nrem_tcco2_30_45', 'time_rem_tcco2_30_45', 'percent_rem_tcco2_30_45', 'time_total_tcco2_30_45', 'percent_total_tcco2_30_45',
    'time_wake_tcco2_45_50', 'percent_wake_tcco2_45_50', 'time_nrem_tcco2_45_50', 'percent_nrem_tcco2_45_50', 'time_rem_tcco2_45_50', 'percent_rem_tcco2_45_50', 'time_total_tcco2_45_50', 'percent_total_tcco2_45_50',
    'time_wake_tcco2_50_55', 'percent_wake_tcco2_50_55', 'time_nrem_tcco2_50_55', 'percent_nrem_tcco2_50_55', 'time_rem_tcco2_50_55', 'percent_rem_tcco2_50_55', 'time_total_tcco2_50_55', 'percent_total_tcco2_50_55',
    'time_wake_tcco2_55_60', 'percent_wake_tcco2_55_60', 'time_nrem_tcco2_55_60', 'percent_nrem_tcco2_55_60', 'time_rem_tcco2_55_60', 'percent_rem_tcco2_55_60', 'time_total_tcco2_55_60', 'percent_total_tcco2_55_60',
    'time_wake_tcco2_60_65', 'percent_wake_tcco2_60_65', 'time_nrem_tcco2_60_65', 'percent_nrem_tcco2_60_65', 'time_rem_tcco2_60_65', 'percent_rem_tcco2_60_65', 'time_total_tcco2_60_65', 'percent_total_tcco2_60_65',
    'time_wake_tcco2_lt_20_gt_65', 'percent_wake_tcco2_lt_20_gt_65', 'time_nrem_tcco2_lt_20_gt_65', 'percent_nrem_tcco2_lt_20_gt_65', 'time_rem_tcco2_lt_20_gt_65', 'percent_rem_tcco2_lt_20_gt_65', 'time_total_tcco2_lt_20_gt_65', 'percent_total_tcco2_lt_20_gt_65'
    ]
    df = table_list[9]
    
    rows_to_get = [3,4,5,6,7,8,10]
    values = df.iloc[:,1:].values
    values = list(np.take(values, rows_to_get, axis=0).flatten())
    
    enter_values(field_names, values, out_dict, idx)
    return out_dict
    

def extract_resp_events_stage(table_list, out_dict, idx):
    field_headers = [   
    # respiratory events
    'total_obst',
    'obs_apnea',
    'obs_hypopnea',
    'total_rera',
    'total_cent',
    'cen_apnea',
    'cen_hypopnea',
    'total_mixed'
    ]

    field_names = [v + '_num' for v in field_headers] + [v + '_idx' for v in field_headers]
    field_names = [v + '_total' for v in field_names] + [v + '_rem' for v in field_names] + [v + '_nrem' for v in field_names]

    field_names = list(np.array(field_names).reshape(6,8).T.flatten())
    
    df = table_list[11]
    values = values_to_float(list(df.iloc[1:,2::2].values.flatten()))
    enter_values(field_names, values, out_dict, idx)
    return out_dict
    
def extract_resp_events_body_position(table_list, out_dict, idx):
    field_headers = [   
    # respiratory events
    'total_obst',
    'obs_apnea',
    'obs_hypopnea',
    'total_rera',
    'total_cent',
    'cen_apnea',
    'cen_hypopnea',
    'total_mixed'
    ]

    field_names = [v + '_num' for v in field_headers] + [v + '_idx' for v in field_headers]
    field_names = [v + '_total' for v in field_names] + [v + '_sup' for v in field_names] + [v + '_nsup' for v in field_names]

    field_names = list(np.array(field_names).reshape(6,8).T.flatten())
    
    df = table_list[12]
    values = values_to_float(list(df.iloc[1:,2::2].values.flatten()))
    enter_values(field_names, values, out_dict, idx)
    return out_dict
    
def extract_resp_events_stage_pos(table_list, out_dict, idx):
    field_headers = [   
    # respiratory events
    'total_obst',
    'obs_apnea',
    'obs_hypopnea',
    'total_rera',
    'total_cent',
    'cen_apnea',
    'cen_hypopnea',
    'total_mixed'
    ]

    field_names = [v + '_num' for v in field_headers] + [v + '_idx' for v in field_headers]
    field_names = [v + '_sup' for v in field_names] + [v + '_nsup' for v in field_names]
    field_names = [v + '_rem' for v in field_names] + [v + '_nrem' for v in field_names]

    field_names = list(np.array(field_names).reshape(8,8).T.flatten())
    
    df = table_list[13]
    values = values_to_float(list(df.iloc[2:,3::2].values.flatten()))
    enter_values(field_names, values, out_dict, idx)
    return out_dict
    
def extract_summary_table(table_list, out_dict, idx):
    field_names = [
    'number_total_respiratory_events', 'index_total_respiratory_events', 'minimum_length_total_respiratory_events', 'maximum_length_total_respiratory_events',
    'number_obstructive_respiratory_events', 'index_obstructive_respiratory_events', 'minimum_length_obstructive_respiratory_events', 'maximum_length_obstructive_respiratory_events',
    'number_obstructive_rem_respiratory_events', 'index_obstructive_rem_respiratory_events', 'minimum_length_obstructive_rem_respiratory_events', 'maximum_length_obstructive_rem_respiratory_events',
    'number_obstructive_nrem_respiratory_events', 'index_obstructive_nrem_respiratory_events', 'minimum_length_obstructive_nrem_respiratory_events', 'maximum_length_obstructive_nrem_respiratory_events',
    'number_obstructive_supine_respiratory_events', 'index_obstructive_supine_respiratory_events', 'minimum_length_obstructive_supine_respiratory_events', 'maximum_length_obstructive_supine_respiratory_events',
    'number_obstructive_non_supine_respiratory_events', 'index_obstructive_non_supine_respiratory_events', 'minimum_length_obstructive_non_supine_respiratory_events', 'maximum_length_obstructive_non_supine_respiratory_events',
    'number_obstructive_rem_supine_respiratory_events', 'index_obstructive_rem_supine_respiratory_events', 'minimum_length_obstructive_rem_supine_respiratory_events', 'maximum_length_obstructive_rem_supine_respiratory_events',
    'number_obstructive_rem_non_supine_respiratory_events', 'index_obstructive_rem_non_supine_respiratory_events', 'minimum_length_obstructive_rem_non_supine_respiratory_events', 'maximum_length_obstructive_rem_non_supine_respiratory_events',
    'number_obstructive_nrem_supine_respiratory_events', 'index_obstructive_nrem_supine_respiratory_events', 'minimum_length_obstructive_nrem_supine_respiratory_events', 'maximum_length_obstructive_nrem_supine_respiratory_events',
    'number_obstructive_nrem_non_supine_respiratory_events', 'index_obstructive_nrem_non_supine_respiratory_events', 'minimum_length_obstructive_nrem_non_supine_respiratory_events', 'maximum_length_obstructive_nrem_non_supine_respiratory_events',

    'number_rera_respiratory_events', 'index_rera_respiratory_events', 'minimum_length_rera_respiratory_events', 'maximum_length_rera_respiratory_events',
    'number_rera_rem_respiratory_events', 'index_rera_rem_respiratory_events', 'minimum_length_rera_rem_respiratory_events', 'maximum_length_rera_rem_respiratory_events',
    'number_rera_nrem_respiratory_events', 'index_rera_nrem_respiratory_events', 'minimum_length_rera_nrem_respiratory_events', 'maximum_length_rera_nrem_respiratory_events',
    'number_rera_supine_respiratory_events', 'index_rera_supine_respiratory_events', 'minimum_length_rera_supine_respiratory_events', 'maximum_length_rera_supine_respiratory_events',
    'number_rera_non_supine_respiratory_events', 'index_rera_non_supine_respiratory_events', 'minimum_length_rera_non_supine_respiratory_events', 'maximum_length_rera_non_supine_respiratory_events',
    'number_rera_rem_supine_respiratory_events', 'index_rera_rem_supine_respiratory_events', 'minimum_length_rera_rem_supine_respiratory_events', 'maximum_length_rera_rem_supine_respiratory_events',
    'number_rera_rem_non_supine_respiratory_events', 'index_rera_rem_non_supine_respiratory_events', 'minimum_length_rera_rem_non_supine_respiratory_events', 'maximum_length_rera_rem_non_supine_respiratory_events',
    'number_rera_nrem_supine_respiratory_events', 'index_rera_nrem_supine_respiratory_events', 'minimum_length_rera_nrem_supine_respiratory_events', 'maximum_length_rera_nrem_supine_respiratory_events',
    'number_rera_nrem_non_supine_respiratory_events', 'index_rera_nrem_non_supine_respiratory_events', 'minimum_length_rera_nrem_non_supine_respiratory_events', 'maximum_length_rera_nrem_non_supine_respiratory_events',

    'number_central_respiratory_events', 'index_central_respiratory_events', 'minimum_length_central_respiratory_events', 'maximum_length_central_respiratory_events',
    'number_central_rem_respiratory_events', 'index_central_rem_respiratory_events', 'minimum_length_central_rem_respiratory_events', 'maximum_length_central_rem_respiratory_events',
    'number_central_nrem_respiratory_events', 'index_central_nrem_respiratory_events', 'minimum_length_central_nrem_respiratory_events', 'maximum_length_central_nrem_respiratory_events',
    'number_central_supine_respiratory_events', 'index_central_supine_respiratory_events', 'minimum_length_central_supine_respiratory_events', 'maximum_length_central_supine_respiratory_events',
    'number_central_non_supine_respiratory_events', 'index_central_non_supine_respiratory_events', 'minimum_length_central_non_supine_respiratory_events', 'maximum_length_central_non_supine_respiratory_events',

    'number_mixed_respiratory_events', 'index_mixed_respiratory_events', 'minimum_length_mixed_respiratory_events', 'maximum_length_mixed_respiratory_events',
    'number_mixed_rem_respiratory_events', 'index_mixed_rem_respiratory_events', 'minimum_length_mixed_rem_respiratory_events', 'maximum_length_mixed_rem_respiratory_events',
    'number_mixed_nrem_respiratory_events', 'index_mixed_nrem_respiratory_events', 'minimum_length_mixed_nrem_respiratory_events', 'maximum_length_mixed_nrem_respiratory_events',
    'number_mixed_supine_respiratory_events', 'index_mixed_supine_respiratory_events', 'minimum_length_mixed_supine_respiratory_events', 'maximum_length_mixed_supine_respiratory_events',
    'number_mixed_non_supine_respiratory_events', 'index_mixed_non_supine_respiratory_events', 'minimum_length_mixed_non_supine_respiratory_events', 'maximum_length_mixed_non_supine_respiratory_events',
    ]
    
    df = table_list[14]
    a = df.iloc[2:28, 2:]
    merged_row = np.array(split_column(df.iloc[28, 2:].values)).T
    b = df.iloc[29:, 2:]
    values = values_to_float(list(np.concatenate((a, merged_row, b), axis=0).flatten()))
    
    enter_values(field_names, values, out_dict, idx)
    return out_dict
    
def extract_periodic_breathing(table_list, out_dict, idx):
    field_headers = [   
    # periodic breathing
    'periodic_breathing_entire_study',
    'periodic_breathing_rem',
    'periodic_breathing_nrem'
    ]

    field_names = [v + '_total_time_min' for v in field_headers] + [v + '_total_time_perc' for v in field_headers]

    field_names = list(np.array(field_names).reshape(2,3).T.flatten())
    
    df = table_list[15]
    values = list(np.take(df.values, [2,4], axis=1)[0, :]) + list(np.array(split_column(np.take(df.values, [2,4], axis=1)[1, :])).flatten())
    values = values_to_float(values)
    
    enter_values(field_names, values, out_dict, idx)
    return out_dict

def extract_min_o2(table_list, out_dict, idx):
    field_names = [
    'min_o2_sat_entire_study',
    'min_o2_sat_rem',
    'min_o2_sat_nrem'
    ]
    
    df = table_list[16]
    values = []
    values.append(df.iloc[0,1])
    values.append(df.iloc[1,1])
    values.append(df.iloc[3,1])
    
    enter_values(field_names, values, out_dict, idx)
    return out_dict


#===============================PROCESS PDF====================================================

def get_individual_fields(path, out_dict, idx):
    '''
    Gets all data from individual fields

    Args:
        path (str): The path to the pdf
        out_dict: a dictionary to store the output data
    Returns:
        dict(str, any): the modified output dictionary
    '''

    pdf_headers, var_names = get_individual_headers_var_names()
    exclude = [14, 27]
    values = []
    # get all the field values
    for i in range(len(pdf_headers) - 1):
        if not (i in exclude):
            txt = extract_text_between_headings(path, pdf_headers[i], pdf_headers[i+1])
            txt = remove_pg_header(txt)
            values.append(txt)
    
    enter_values(var_names, values, out_dict, idx)
    return out_dict




def get_compound_fields(path, out_dict, idx):
    '''
    Gets all data from tables

    Args:
        path (str): The path to the pdf
        out_dict(dict(str, any)): a dictionary to store the output data
        idx (int): doc index
    Returns:
        dict(str, any): the modified output dictionary
    '''
    table_list = tabula.read_pdf(path, pages=[4,5,6,7,8])
        
    out_dict = extract_sleep_params(path, out_dict, idx)
    out_dict = extract_stage_dist(table_list, out_dict, idx)
    out_dict = extract_arousals(table_list, out_dict, idx)
    out_dict = extract_leg_mvmts(table_list, out_dict, idx)
    out_dict = extract_resp_analysis(table_list, out_dict, idx)
    out_dict = extract_baseline_ranges(table_list, out_dict, idx)
    out_dict = extract_spo2_ranges_sleep(table_list, out_dict, idx)
    out_dict = extract_resp_events(table_list, out_dict, idx)
    out_dict = extract_desat_table(table_list, out_dict, idx)
    out_dict = extract_etco2_vals(table_list, out_dict, idx)
    out_dict = extract_resp_events_stage(table_list, out_dict, idx)
    out_dict = extract_resp_events_body_position(table_list, out_dict, idx)
    out_dict = extract_resp_events_stage_pos(table_list, out_dict, idx)
    out_dict = extract_summary_table(table_list, out_dict, idx)
    out_dict = extract_periodic_breathing(table_list, out_dict, idx)
    out_dict = extract_min_o2(table_list, out_dict, idx)
    
    return out_dict




def process_pdf(path, out_dict, idx):
    '''
    Gets all data from pdf at path and inputs it in out_dict
    Args:
        path (str): The path to the pdf
        out_dict: a dictionary to store the output data
    Returns:
        dict(str, any): the modified output dictionary
    '''
    
    out_dict = get_individual_fields(path, out_dict, idx)
    out_dict = get_compound_fields(path, out_dict, idx)
    
    return out_dict

#===============================OUTPUT=========================================================
def save_spreadsheet(out_dict):
    '''
    Saves output dictionary as a spreadsheet (.csv)

    Args: 
        out_dict (dict(str, any)): the data to be saved
    Returns:
        None
    '''
    
    df = pd.DataFrame.from_dict(out_dict)
    df.to_csv('out.csv')
#===============================MAIN FUNTION===================================================
def main():
    '''
    Main function. Processes all pdfs in PDFs folder
    '''

    # Get list of pdfs in pdfs folder
    pdf_list, out_dict = get_pdf_list()
    print(out_dict)
    # Process each pdf
    for i, path in enumerate(pdf_list):
        print(f'Processing pdf {i+1}/{len(pdf_list)}. \n Path: {path} \n')
        assert path.lower().endswith('.pdf')
        process_pdf(path, out_dict, i)
    
    save_spreadsheet(out_dict)



if __name__=="__main__":
    main()