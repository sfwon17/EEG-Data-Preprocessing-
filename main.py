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

# Configurations
patient_info = pd.read_excel('patients.xlsx', sheet_name='Seizure Information')

# signals choice
eeg = ['C3', 'F7', 'F4', 'C4', 'Fz', 'Cz', 'Pz', 'Fp1', 'P3', 'Fp2', 'P4', 'F3', 'F8', 'O1', 'O2', 'T3', 'T4', 'T5', 'T6'] # these eegs are the common choice used in seizure detection studies. 

# frequency filter
low_bp = 0.1
high_bp = 60
notch = 50 

# Frequency in Hz
freq = 250

# Make sure your EEG recordings are in EDF format and replace the file path 
# loop through all the patients
for file in glob.glob("./data/*.edf"):
  for file in pat[:]:
    print(file)
    tmp, rawData, feature_list = read_eeg_data(file, eeg, notch, low_bp, high_bp, freq) 
        
    # extract time information 
    data_with_time = extract_time_length(rawData,tmp,freq )

    # extract seizure information 
    data_with_seizure = extract_seizure_time(data_with_time, patient_info,file)

    # segment data 
    segmented_data,segmented_labels = EEG_segmentation(data_with_seizure, size = 1000)
    
    # save eeg data
    filename = file.split("\\")[-1] if "\\" in file else file.split("/")[-1]
    base_name_without_extension = filename.split(".")[0]
        
    np.savez("EEG_data/" + base_name_without_extension +' complete', eeg_data= segmented_data, eeg_labels= segmented_labels)        
    print("Extraction complete")
