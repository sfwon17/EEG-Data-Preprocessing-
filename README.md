# EEG-Data-Preprocessing
This Repo contains the code for preprocessing EEG data for training and evaluating Deep Learning models. 

## Things To Note
1. The EEG recordings are segmented by time only.
2. Minimal denoising and filtering of EEG signals.
3. Raw EEG data are extracted with international 10 - 20 standards format.
4. There is no feature engineering.
5. There is no window overlap to reduce class imbalance.
6. Refer to the Excel file for column headers, which are used for preprocessing. Please note that patient data is not included due to privacy reasons. The provided Excel file is intended to help users clean their data to ensure compatibility with the script. Publicly available EEG datasets often use Excel or text files to store seizure information, such as the start and end times of seizure events.
