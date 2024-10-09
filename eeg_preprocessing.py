import json
from pyedflib import highlevel
import pyedflib as plib
import numpy as np
import matplotlib.pyplot as plt
import yasa
import mne
from mne.io import read_raw_edf
import glob
import pandas as pd
from datetime import datetime, timedelta,date

# read montage pairs from json 
def read_montage_pairs(file_path='montage_pairs.json'):
    with open(file_path, 'r') as f:
        montage_pairs = json.load(f)
    return montage_pairs

# read and keep relevant channels
def montage(raw, montage_file='montage_pairs.json'):
    # Read montage pairs from the specified file
    montage_pairs = read_montage_pairs(montage_file)
    
    # Apply bipolar montage using the pairs
    for bipolar_label, (anode, cathode) in montage_pairs.items():
        if anode in raw.info['ch_names'] and cathode in raw.info['ch_names']:
            raw = mne.set_bipolar_reference(raw, anode=anode, cathode=cathode, 
                                            ch_name=bipolar_label, drop_refs=False, 
                                            verbose="ERROR")
        else:
            print(f"Skipping channel pair {bipolar_label} for this patient because {anode} or {cathode} is missing.")
    
    # Keep only channels that are present in the montage pairs
    channels_to_keep = [ch for ch in raw.ch_names if ch in montage_pairs]
    raw.pick_channels(channels_to_keep)
    
    return raw

# check and replace channels
def check_channels_number(df, montage_file='montage_pairs.json'):
    # Read montage pairs from the JSON file
    montage_pairs = read_montage_pairs(montage_file)
    
    # Extract the order from the keys of the montage pairs
    order = list(montage_pairs.keys())
    
    # Reindex DataFrame columns to match the specified order, filling missing channels with zeros
    return df.reindex(columns=order, fill_value=0)

# remove noise
def read_eeg_data(file, eeg, notch, low_bp, high_bp, freq):
    
    raw = mne.io.read_raw_edf(file, preload=True, verbose = "ERROR")
    raw.pick_channels(eeg)

    # filter notch and filter frequnecy 0.1 - 60
    raw.notch_filter(freqs=50, fir_design='firwin',verbose = "ERROR")
    raw = raw.filter(l_freq=0.1, h_freq=60, verbose = 'ERROR')
    
    # resample
    if raw.info['sfreq'] != freq:
        raw = raw.resample(freq)
    # rename channel, change to bipolar, remove unnessary channel
    raw = montage(raw, montage_file='montage_pairs.json')
    
    tmp = raw.to_data_frame()
    tmp = tmp.drop('time', axis = 1)
    tmp = check_channels_number(tmp, montage_file='montage_pairs.json')
    # extract features name 
    feature_list = tmp.columns.tolist()
    
    return tmp, raw, feature_list

# extract the time of eeg recordings
def extract_time_length(rawData,data,freq):
    initial_time = 0
    end_time = data.shape[0]
    recording_list = [rawData.info['meas_date'].strftime("%H:%M:%S")]*freq
    second = 1
    while len(recording_list) != end_time:
        new_time_list = []
        new_time = (rawData.info['meas_date'] + timedelta(seconds = second)).strftime("%H:%M:%S")
        new_time_list.append(new_time)
        recording_list.extend(new_time_list*freq)
        second = second + 1
    
    data['Time'] = recording_list
    return data

# extarct segments with seizure
def extract_seizure_time(data_with_time, patient_info,file):

    data_with_time['Seizure'] = 0
    data_with_time['Time']= pd.to_datetime(data_with_time['Time'], format='%H:%M:%S')
    patient_seizure_time = patient_info[patient_info['New Study ID No.'] == file.split("/")[2].split(".")[0]]

    for index, row in patient_seizure_time.iterrows():
        start_seizure = pd.to_datetime(row['Seizure Start'], format='%H:%M:%S')
        print(start_seizure)
        end_seizure = pd.to_datetime(row['Seizure End'], format='%H:%M:%S')
        print(end_seizure)
        seizure_event = (data_with_time['Time'] >= start_seizure) & (data_with_time['Time'] < end_seizure)
        data_with_time.loc[seizure_event, 'Seizure'] = 1
      
    return data_with_time
  
# eeg segmentation
def EEG_segmentation(df, size = 1000): # 1 sec = 250. 
    # convert df to values
    events = df['Seizure'].values
    
    data = df.drop(columns = ['Time','Seizure']).values
    
    # Check if the data length is divisible by 1000
    num_samples = data.shape[0]
    remainder = num_samples % size
    
    if remainder != 0:
        # Drop the remainder to make it divisible by 1000
        data = data[:-remainder]
    
    # do similar but check for seizure
    num_samples = events.shape[0]
    remainder = num_samples % size
    
    
    if remainder != 0:
        # Drop the remainder to make it divisible by 250
        events = events[:-remainder]
        
    # reshape the eeg data
    segmented_data = data.reshape(-1, size, data.shape[1])
    
    # Reshape the seizure data to shape (-1, 1000)
    segmented_seizure = events.reshape(-1, size)

    # If any value in a segment is 1 for seizure , label it as 1, else 0
    segmented_labels = np.any(segmented_seizure == 1, axis=1).astype(int)
    
    # remove first 5 second due to noise
    #segmented_data = segmented_data[5:]
    #segmented_labels = segmented_labels[5:]
    return segmented_data,segmented_labels
