#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A python tool to ensure that all HQPGAC aircraft have the same dat variable
values as specified in the HQPGAC Tracker on Google Drive.

Place this folder in the working or release folder.

Then download the HQPGAC Tracker to an excel file and put in the same location.
"""

def import_dat(filepath):
    if os.path.isfile(filepath) is False:
        print("Unable to find: {}".format(filepath))
        return list()
    
    with open(filepath, mode='r') as dat_file:
        data = dat_file.readlines()
        
    output = list()
    for i in data:
        output.append(i.rstrip())
        
    return data

def write_dat(filepath, lines):
    if os.path.isfile(filepath) is False:
        print("Unable to save to file")
        return
    
    with open(filepath, mode='w') as dat_file:
        dat_file.writelines(lines)


# Import Modules
import pandas as pd
import os

# Get release folder directory
cwd = os.getcwd()

# Get the HQPGAC Tracker
filepath = os.path.join(cwd, 'HQPGAC Tracker.xlsx')

# Import relevant sheets from HQPGAC Tracker file
Tracker = pd.ExcelFile(filepath)
sheet_names = ['Current', 'JET DATs', 'PROP DATs']

# Define the boolean column names
bool_cols = ['CTLLDGEA', 'CTLBRAKE', 'CTLABRNR', 'CTLATVGW', 'HASSPOIL', 'RETRGEAR', 'VARGEOMW','BOMBINBAY']

aircraft_df = pd.read_excel(Tracker, sheet_name='Current', header=0)
jet_df = pd.read_excel(Tracker, sheet_name='JET DATs', header=0)
prop_df = pd.read_excel(Tracker, sheet_name='PROP DATs', header=0)

# Drop columns used to help calculate things and not part of the DAT Variables
bad_cols = ['# MACHINE\nGUNS', 'Damage/\nSecond', 'Firing\nTime', 'AB Time', 'MIL Time']
jet_df.drop(columns=[col for col in jet_df if col in bad_cols], inplace=True)
prop_df.drop(columns=[col for col in prop_df if col in bad_cols], inplace=True)

# Extract the units from the dfs and then delete from the dataframe.
jet_units = jet_df.iloc[0,:].values.tolist()
prop_units = prop_df.iloc[0,:].values.tolist()
jet_units = jet_units[1:]
prop_units = prop_units[1:]
jet_df.drop(axis=0, index=0, inplace=True)
prop_df.drop(axis=0, index=0, inplace=True)

# Set the Model as the index name for easier handling.
jet_df.set_index(keys=['Model'], inplace=True)
prop_df.set_index(keys=['Model'], inplace=True)

# Replace NAN values with zero
aircraft_df.fillna(0, inplace=True)
jet_df.fillna(0, inplace=True)
prop_df.fillna(0, inplace=True)

# iterate over the current aircraft df
for idx, row in aircraft_df.iterrows():
    
    # Only proccess aircraft if they are part of the current pack
    if row['Status'] != 'Current':
        continue
    
    # Extract information from the aircraft_df
    dat_filepath = os.path.join(cwd, row['Folder'], row['DAT'])
    dat_model = row['DAT Class']
    substname = row['Substname']
    identify = row['New Name (green=renamed already on Decaff Computer)']
    print(idx, '    ', identify)
    
    # Get the DAT information.
    if dat_model in jet_df.index:
        dat_values = jet_df.loc[dat_model]
        units = jet_units
    elif dat_model in prop_df.index:
        dat_values = prop_df.loc[dat_model]
        units = prop_units
    else:
        print("Unable to find DAT Class: {} for Aircraft: {}".format(dat_model, identify))
        
    # IDENTIFY and SUBSTNAM variables need to be difference because they will 
    # have the values in quotation marks as opposed to normal values.
    dat_lines = import_dat(dat_filepath)
    identify_index = 0
    variable_list = dat_values.index.tolist()
    for idx, line in enumerate(dat_lines):
        
        # Skip lines that are too short or blank
        if len(line) < 8:
            dat_lines[idx] = '\n'
            continue
        
        # Get the dat var at the front of the line
        var = line[:8]
        
        # Skip comment lines
        if line.startswith("REM"):
            dat_lines[idx] = line 
            continue

        elif var.isspace() or len(line) < 3:
            dat_lines[idx] = '\n'
            continue
        
        elif line.startswith("IDENTIFY"):
            dat_lines[idx] = 'IDENTIFY "{}"\n'.format(identify)
            identify_index = idx
        elif line.startswith("SUBSTNAM"):
            dat_lines[idx] = 'SUBSTNAM "{}"\n'.format(substname)
            identify_index = -1
        elif var in dat_values.index:
            # Build up a new line to replace the old one
            if "#" in line:
                ending = "#" + line.split("#")[-1]
            else:
                ending = "\n"
            
            unit = units[variable_list.index(var)]
            
            if var in bool_cols:
                if dat_values.loc[var] == 0:
                    dat_lines[idx] = var + " " + 'FALSE' + ' ' * 10 + ending
                else:
                    dat_lines[idx] = var + " " + 'TRUE' + ' ' * 10 + ending
            else:
                if isinstance(unit, str):
                    dat_lines[idx] = var + " " + str(dat_values.loc[var]) + unit + ' ' * 10 + ending
                else:
                    dat_lines[idx] = var + " " + str(dat_values.loc[var]) + ' ' * 10 + ending
            
    # Handle the substnam line
    if identify_index >= 0:
        # We did not find the substname line and must make one now.
        dat_lines.insert(identify_index + 1, 'SUBSTNAM "{}"\n'.format(substname))
    
    # Save the changes to file.
    write_dat(dat_filepath, dat_lines)
