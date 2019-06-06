import os.path
import numpy as np
import tkinter as tk
from tkinter import filedialog
from pandas import read_excel, ExcelWriter, DataFrame
from easygui import multenterbox, buttonbox, enterbox, msgbox
from shutil import copy


NIST = np.array([(70,40.75),(75,46.11),(80,51.76),(85,57.69),(90,63.89),(95,70.35),(100,77.07),(105,84.05),(110,91.28),(115,98.75),(120,106.50),(125,114.40),(130,122.60),(135,131.00),(140,139.60),(145,148.50),(150,157.60),(155,166.80),(160,176.30),(165,186.00),(170,195.90),(175,206.00),(180,216.30),(185,226.70),(190,237.40),(195,248.30),(200,259.30),(205,270.50),(210,281.90),(215,293.40),(220,305.20),(225,317.10),(230,329.10),(235,341.30),(240,353.70),(245,366.30),(250,379.00)])

def DistalDepthSeeker(Dose,datax,datay): # Define a formula to find x for a given y in the distal fall off
        np.warnings.filterwarnings('ignore') # Prevents the "NaN" error message in the python display
        index = np.argmax((np.asarray(list(reversed(datay))))>Dose) # Find the first value that exceeds the "Dose" value approaching from greatest x value
        y0 = (datay[len(datay)-index-1]) # These 4 lines fetch the points either side of the value
        y1 = (datay[len(datay)-index])
        x0 = (datax[len(datax)-index-1])
        x1 = (datax[len(datax)-index])
        slope = ((y1-y0)/(x1-x0)) # calculate the gradient - note a linear interpolation is performed
        intercept = y0-(slope*x0) # calculate the theoretical intercept
        distal = (Dose-intercept)/slope # finds x value for given Dose level
        return distal; # Output the value for later use

def ProximalDepthSeeker(Dose,datax,datay): # same as previous formula but approaching data from the front
        np.warnings.filterwarnings('ignore') # Prevents the "NaN" error message in the python display
        index = np.argmax((np.asarray(datay))>Dose)
        y0 = (datay[index-1])
        y1 = (datay[index])
        x0 = (datax[index-1])
        x1 = (datax[index])
        slope = ((y1-y0)/(x1-x0)) # calculate the gradient - note a linear interpolation is performed
        intercept = y0-(slope*x0) # calculate the theoretical intercept
        proximal = (Dose-intercept)/slope # finds x value for given Dose level
        return proximal; #Out put the value for use later

class PeakProperties:
    def __init__(self, NISTRange, Prox80, Prox90, Dist90, Dist80, Dist20, Dist10, PTPR):
        self.NISTRange = NISTRange
        self.Prox80 = Prox80
        self.Prox90 = Prox90
        self.Dist90 = Dist90
        self.Dist80 = Dist80
        self.Dist80 = Dist80
        if NISTRange == "Out Of Range": #Catches if energies are outside the hardcoded NIST data
            self.NISTDiff = "N/A"
        else:
            self.NISTDiff = self.Dist80 - NISTRange
        self.Dist20 = Dist20
        self.Dist10 = Dist10
        self.PTPR = PTPR
        self.FallOff = self.Dist20 - self.Dist80
        self.PeakWidth = self.Dist80 - self.Prox80



def OnePDD(Data, Energy):
    if Energy<70: #Only uses NIST values if within the range hardcoded at the beginning
        NISTRange = "Out Of Range"
    elif Energy>250: #Only uses NIST values if within the range hardcoded at the beginning
        NISTRange = "Out Of Range"
    else:
        NISTRange = np.interp(Energy,NIST[:,0],NIST[:,1]) #Performs linear interpolation between NIST data points if Energy isn't available
    datax = np.asarray([x[0] for x in Data]) # Collects X data
    datay = np.asarray([y[1] for y in Data]) # Collects Y data
    maxy = max(datay) # Find the maximum value in the y data
    datay = 100*datay/maxy # Convert all values to percentages with dmax = 100%

    Plateaux = np.interp(25,datax,datay)
    PTPR = 100/Plateaux # Calcualtes peak to plateau ratio

    Data_Props = PeakProperties(NISTRange, ProximalDepthSeeker(80,datax,datay), ProximalDepthSeeker(90,datax,datay), DistalDepthSeeker(90,datax,datay), DistalDepthSeeker(80,datax,datay), DistalDepthSeeker(20,datax,datay), DistalDepthSeeker(10,datax,datay), PTPR)

    return (Data_Props)


######################
#Open and read-in an excel file with defined format and save a copy
######################

root = tk.Tk()
root.withdraw() #Hides the tk Pop-up window

filename = filedialog.askopenfilename() #Asks user to select preprepared excel file with Data in desired format
if filename == "": #Catch error of not inputting a file
    msgbox("Please re-run the program and select a file", title="No File Selected")
    exit()

foldername = os.path.dirname(os.path.abspath(filename))

try:
    copy(filename,os.path.join(foldername,"Analysed Ref Data.xlsx")) #Creates a copy of the input file and saves as "Analysed"
except OSError: # Catches if analysed file is open
    msgbox("Please close the analysed file and re-run the program")
    exit()

copy(filename,os.path.join(foldername,"Analysed Ref Data.xlsx")) #Creates a copy of the input file and saves as "Analysed"

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

sheets_dict = read_excel(filename, sheet_name=None) #Creates a dictionary that has Energy as the main key, then a sub dictionary with Data titles as keys (Measured X, Measured Y etc.)

sheets_dict = {float(old_key): val for old_key, val in sheets_dict.items()} #Converts the Energy keys from strings to floats so they can be sorted numerically

######################
# Run analysis script "TwoPDDs" for each energy in spreadsheet
######################

writer = ExcelWriter(os.path.join(foldername,"Analysed Ref Data.xlsx"), engine = 'xlsxwriter') #Sets up the tool "writer" that will put results into excel


for key in sorted(set(sheets_dict)): #Cycles through all energies in the spreadsheet in ascending order (Tab titles)

    sheets_dict[key]['Measured X'] += OffSet #Adds any offset present in the measurement defined by the user above

    (Data_Props) = OnePDD(DataFrame.from_dict([sheets_dict[key]['Measured X'],sheets_dict[key]['Measured Y']]).values.T.tolist(), key) #Run the scripts to perform peak analysis and gamma analysis
    sheets_dict[key]["Measured Properties"] = '' #Creates new empty key to insert results into dictionary
    sheets_dict[key]["Results"] = '' #Creates new empty key to insert results into dictionary
    for x in range (0,len(list(Data_Props.__dict__.keys()))): # Cycle through the results and paste them into the dictionary
        sheets_dict[key]["Measured Properties"][x] = list(Data_Props.__dict__.keys())[x] # Inputting the Titles
        sheets_dict[key]["Results"][x] = list(Data_Props.__dict__.values())[x] # Inputting the Data 1 results

    DF = DataFrame.from_dict(sheets_dict[key]) # Convert data of the key enery into a dataframe to write to excel
    DF.update(DF.iloc[0:11,2:4].sort_values("Measured Properties").reset_index(drop=True)) # Reorder the results section
    DF.to_excel(writer, sheet_name=str(key)) # Paste results dataframe into excel
    worksheet = writer.sheets[str(key)] # Open key energy worksheet to paste image into

    # Following lines set the widths of the columns to tidy up a bit.
    worksheet.set_column('A:A', 3.29)
    worksheet.set_column('B:C', 11.14)
    worksheet.set_column('D:D', 19.29)
    worksheet.set_column('E:E', 11.29)

writer.save() # Saves results workbook

msgbox("Code has finished running", title="All Energies Completed")
