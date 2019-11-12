from numpy import asarray, random, isnan
from PDD_Module2 import *
from tkinter import Tk, filedialog
import os
from easygui import multenterbox, buttonbox, enterbox, msgbox
import random as rnd
import pandas as pd
import xlsxwriter

NIST = asarray([(70,40.75),(75,46.11),(80,51.76),(85,57.69),(90,63.89),(95,70.35),(100,77.07),(105,84.05),(110,91.28),(115,98.75),(120,106.50),(125,114.40),(130,122.60),(135,131.00),(140,139.60),(145,148.50),(150,157.60),(155,166.80),(160,176.30),(165,186.00),(170,195.90),(175,206.00),(180,216.30),(185,226.70),(190,237.40),(195,248.30),(200,259.30),(205,270.50),(210,281.90),(215,293.40),(220,305.20),(225,317.10),(230,329.10),(235,341.30),(240,353.70),(245,366.30),(250,379.00)])

root = Tk() #Open TK for a File Dialog
root.withdraw() #Hides the tk Pop-up window

TestData={}
gammas={}
TestDataProps={}

dir2 = filedialog.askdirectory(title='Please Select Test Data') #Asks user to select folder containing data in MCC or CSV format
if dir2 == '':
    exit()

OffSet = enterbox("Enter WET Offset (mm)", "WET Offset", ('0')) #User inputs offset in terms of water equivalent thickness (due to tank wall chamber thickness etc.)

if OffSet == None:  #Ensure something was selected for WET thickness
    msgbox("Please re-run the program and enter an offset, even if it's 0.0", title="WET box closed without entry")
    exit()


try: # Ensure entered WET value is a sensible entry
    float(OffSet)
except ValueError:
    msgbox("Please re-run the program and enter an appropriate value for the WET offset", title="WET Value Error")
    exit()
OffSet=float(OffSet)

for filename in os.listdir(dir2): # Loop through each file in the directory
    file = os.path.basename(filename) # Splits file into the location and:
    if os.path.splitext(file)[1]==".mcc": # Selects only the MCC Files
        name = float(os.path.splitext(file)[0]) # Extracts filename without extension (should be the energy)
        TestData[name], E, D, GA = ReadTank(os.path.join(dir2,filename)) # This function is in the PDD module and reads MCC files.
        TestData[name][0] = TestData[name][0]+OffSet # This applies the entered WET offset to the data

writer = pd.ExcelWriter('TEST.xlsx',engine='xlsxwriter') # Defines the writer which is required to save the report as an excel file.

for key in sorted(TestData.keys()): # Loop through each energy supplied in the MCC files
    TestDataProps[key] = OnePDD(TestData[key], float(key)) # This function is in the PDD module and extracts the properties of a BPC
    TestDataXL  = pd.DataFrame({'Test Data Depth':TestData[key][0],'Test Data Dose':TestData[key][1]}) # Creates Dataframe for easy input to excel
    DataPropsXL = pd.DataFrame({'Property':list(TestDataProps[key].__dict__.keys()),'Test Data':list(TestDataProps[key].__dict__.values())}) # Creates Dataframe for easy input to excel

    TestDataXL.to_excel(writer,sheet_name=str(int(key)),index=False) # Writes DataFrame to Excel
    DataPropsXL.to_excel(writer,sheet_name=str(int(key)),index=False,startcol=3) # Writes DataFrame to Excel

    workbook = writer.book
    worksheet = writer.sheets[str(int(key))] # Directs to each sheet individually (referencing eacch energy)
    # Next section adjusts column widths
    worksheet.set_column('A:A', 14.43)
    worksheet.set_column('B:B', 13.43)
    worksheet.set_column('C:C', 5.0)
    worksheet.set_column('D:D', 11.0)
    worksheet.set_column('E:E', 12.0)

    chart = workbook.add_chart({'type': 'scatter'}) # Creates a chart object
    chart.add_series({'name': [str(int(key)),0,1],'categories': [str(int(key)),1,0,1+len(TestData[key][0]),0],'values': "='"+str(int(key))+"'!$B$2:$B$"+str(1+len(TestData[key][1])),'y2_axis':0}) # Selects the required data for the plot
    chart.set_y_axis({'min':0}) # Sets Y axis minimum
    chart.set_size({'width': 1300, 'height':650}) # Sets size of the chart object
    chart.set_title({'name': "PDD for %1.1f MeV"%key}) #Makes the title including the energy

    worksheet.insert_chart('D15', chart) # Inserts the chart into the worksheet
    print(str(key) +' Done') # Tracks how many Energies have been completed

writer.save()
