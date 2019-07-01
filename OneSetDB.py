#Browse to the folder containing the Files
from tkinter import Tk, filedialog
import os
from PDD_Module import *
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

Device = buttonbox(msg="Which Chamber was used?",title='Select Chamber', choices=('Giraffe [1]', 'StingRay [1]','Bragg Peak [1]'), cancel_choice = '') #Pop up box to select device used. This must match the file type.

# These three if loops ensure the filetype matches the selected Device
if Device == 'Giraffe [1]':
    if os.listdir(dir)[0].endswith('.csv') != True:
        msgbox("Device does not match filetype. Please re run the code and select the correct device/folder", "Device/File Type Error")
        exit()

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

if os.listdir(dir)[0].endswith('.mcc'):
    TEST_Dict['TEST'],TE,TD,GA = ReadTank(os.path.join(dir,os.listdir(dir)[0]))

if os.listdir(dir)[0].endswith('.csv'):
    TEST_Dict['TEST'],TD = ReadGiraffe(os.path.join(dir,os.listdir(dir)[0]))

    #The ReadGiraffe doesn't produce gantry angle because it's not in the header. This requires user input
    GA = enterbox("Enter Measurement Gantry Angle", "Gantry Angle during acquisition", ('270'))
    try: # Ensure entered GA value is a sensible entry
        float(GA)
    except ValueError:
        msgbox("Please re-run the program and enter an appropriate value for the Gantry Angle", title="Gantry Angle Value Error")
        exit()

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

    if filename.endswith('.mcc'): # Water tank files end with .mcc
        Data_Dict[name], E, D, GA = ReadTank(os.path.join(dir,filename)) # This function is in the PDD module and reads MCC files.

    if filename.endswith('.csv'): # Giraffe data is saved as a csv
        Data_Dict[name], D = ReadGiraffe(os.path.join(dir,filename)) # This function is in the PDD module and reads csv files produced by the giraffe.

        try: # Giraffe files don't have energy in the header, it is taken from the file name
            float(name)
        except ValueError:
            msgbox("Files must be labelled with the energy of the bragg peak, please rename files", title="File Name Error")
            exit()

        E=float(name) # For Giraffe Files, the energy is taken from the filename of the data, it's not in the data

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


conn.commit() # The commit line locks in the entry.


    # with open('C:/Users/cgillies/Desktop/Python_3/GIT Some/TwoDataSets-PDD/DataBaseFormat.xlsx',"a") as csvfile:
    #     writer=csv.writer(csvfile)
    #     writer.writerow([Subset])







# print(Energy, Date, GantryAngle)


# sheets_dict = {float(old_key): val for old_key, val in Data_Dict.items()} #Converts the Energy keys from strings to floats so they can be sorted numerically

# writer = ExcelWriter(os.path.join(dir,"Analysed Ref Data.xlsx"), engine = 'xlsxwriter') #Sets up the tool "writer" that will put results into excel


# for key in sorted(set(sheets_dict)): #Cycles through all energies in the spreadsheet in ascending order (Tab titles)
#     sheets_dict[key][0] += OffSet #Adds any offset present in the measurement defined by the user above
#     (Data_Props) = OnePDD(DataFrame.from_dict([sheets_dict[key][0],sheets_dict[key][1]]).values.T.tolist(), key) #Run the scripts to perform peak analysis and gamma analysis
#     print(Date)
#     wDate = Date.index(str(key)
#     print(wDate)

    # print(Data_Props.__dict__)

#     sheets_dict[key]['Measured Properties'] = '' #Creates new empty key to insert results into dictionary
#     sheets_dict[key]["Results"] = '' #Creates new empty key to insert results into dictionary
#     for x in range (0,len(list(Data_Props.__dict__.keys()))): # Cycle through the results and paste them into the dictionary
#         sheets_dict[key]["Measured Properties"][x] = list(Data_Props.__dict__.keys())[x] # Inputting the Titles
#         sheets_dict[key]["Results"][x] = list(Data_Props.__dict__.values())[x] # Inputting the Data 1 results
#
#     DF = DataFrame.from_dict(sheets_dict[key]) # Convert data of the key enery into a dataframe to write to excel
#     DF.update(DF.iloc[0:11,2:4].sort_values("Measured Properties").reset_index(drop=True)) # Reorder the results section
#     DF.to_excel(writer, sheet_name=str(key)) # Paste results dataframe into excel
#     worksheet = writer.sheets[str(key)] # Open key energy worksheet to paste image into
#
#     # Following lines set the widths of the columns to tidy up a bit.
#     worksheet.set_column('A:A', 3.29)
#     worksheet.set_column('B:C', 11.14)
#     worksheet.set_column('D:D', 19.29)
#     worksheet.set_column('E:E', 11.29)
#
# writer.save() # Saves results workbook

msgbox("Code has finished running", title="All Energies Completed")
