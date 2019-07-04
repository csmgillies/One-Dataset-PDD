#Browse to the folder containing the Files
from tkinter import Tk, filedialog
import os
from PDD_Module2 import *
from easygui import multenterbox, buttonbox, enterbox, msgbox, choicebox
from pandas import ExcelWriter, DataFrame
from datetime import date
from openpyxl import workbook, load_workbook
import csv
import pypyodbc

root = Tk() #Open TK for a File Dialog
root.withdraw() #Hides the tk Pop-up window

dir = filedialog.askdirectory() #Asks user to select folder containing data in MCC or CSV format
if dir == None:
    exit()

Data_Dict={} # Create empty dictionary to insert X and Y data with Energy as the key
TEST_Dict={} # Empty dictionary required to get the date for the database key
BadName = [] # Create empty array to alert users if any filnames don't match the acquired energy
Operators = [] # Empty list to fetch names of operators from the databse

Gantry = buttonbox(msg="Which room were the measurements performed in?",title='Select Room', choices=('Gantry 1', 'Gantry 2','Gantry 3','Gantry 4'), cancel_choice = '') #Pop up box to choose absolute or relative gamma

if Gantry == None: # This section ensures a button is selected
    msgbox("Please re-run the code and select a room")
    exit()

Device = buttonbox(msg="Which Chamber was used?",title='Select Chamber', choices=('StingRay [1]','Bragg Peak [1]'), cancel_choice = '') #Pop up box to select device used. This must match the file type.

# These if loops ensure the filetype matches the selected Device

if Device == 'StingRay [1]':
    if os.listdir(dir)[0].endswith('.mcc') != True:
        msgbox("Device does not match filetype. Please re run the code and select the correct device/folder", "Device/File Type Error")
        exit()

if Device == 'Bragg Peak [1]':
    if os.listdir(dir)[0].endswith('.mcc') != True:
        msgbox("Device does not match filetype. Please re run the code and select the correct device/folder", "Device/File Type Error")
        exit()

if Device == None: # This section ensures a button is selected
    msgbox("Please re-run the code and select a device")
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

OffSet=float(OffSet) # OffSet is entered as a string - this converts it to a float

# pypyodbc is a library allowing you to connect to an SQL database. This is some code that I copied from google,
# The important bit is the DBQ= bit where you put the location of the database back end.
conn = pypyodbc.connect(
        r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};'
        r'DBQ=C:/Users/cgillies/Desktop/Python_3/GIT Some/TwoDataSets-PDD/AssetsDatabase_beCG.accdb;'
        r'PWD=1234;'
        )
cursor = conn.cursor()
cursor.execute('select * from Operators') #This line adds the "operators" table to the cursor

for row in cursor.fetchall(): # This Fetches the data from the cursor
    Operators.append(row[2]) # This fetches the names and appends them to the operators list.

Operator = choicebox("Who performed the measurements?", "Operator", Operators) # This allows user to select from the database list of operators

####################
# In order to write to the database, two tables need to be filled.
# One table needs to be filled in first and it requires the date and gantry angle.
# Unfortunately it needs to happen before the following data extraction loop.
# It still has to test the filetype and extract all the data, but the code only needs the TD or "Test Date"
####################

TEST_Dict['TEST'],TE,TD,GA = ReadTank(os.path.join(dir,os.listdir(dir)[0]))

#This is the first write to the database as a session the table is called MLICenergy and requires the inputs listed below
sql1 =       ('''
                    INSERT INTO MLICenergy (ADate, Dev, Machine, Gantry_Angle, Operator)
                    VALUES(?,?,?,?,?)

                ''')
# The execute function writes the values????? as the inputs below.
cursor.execute(sql1,[TD,Device,Gantry,int(float(GA)),Operator])

####################
# Major loop to extract data from files
####################

for filename in os.listdir(dir): # Loop through each file in the directory
    file = os.path.basename(filename) # Splits file into the location and:
    name = os.path.splitext(file)[0] # Extracts filename without extension (should be the energy)

    ####################
    #Go through file, check file type and extract Data
    ####################

    Data_Dict[name], E, D, GA = ReadTank(os.path.join(dir,filename)) # This function is in the PDD module and reads MCC files.

    if float(name) != float(E): # Checks title names against data names (mainly for MCC files as for giraffe files, E is taken from name)
        BadName.append([name,E]) # Creates list of files which are incorrectly labelled
        continue

    (Data_Props) = OnePDD(Data_Dict[name], E) #Run the scripts to perform peak analysis

    Subset = [D,Device,Gantry,int(float(GA)),E,round(float(Data_Props.Dist10),2),round(float(Data_Props.Dist20),2),round(float(Data_Props.Dist80),2),round(float(Data_Props.Dist90),2),round(float(Data_Props.Prox80),2),round(float(Data_Props.Prox90),2)]

    sql2 =       ('''
                        INSERT INTO MLICenergyRdgs (ADate, Dev, Machine, Gantry_Angle, Energy, D10, D20, D80, D90, P90, P80)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?)

                    ''')

    cursor.execute(sql2,Subset)


if BadName != []:
    msgbox("The following files were incorrectly labelled please correct the files and re-run. No data was written to the database:"+str(BadName))
    exit()

conn.commit() # The commit line locks in the database entry.

msgbox("Code has finished running", title="All Energies Completed")
