from numpy import warnings,argmax,asarray, interp
import datetime

NIST = asarray([(70,40.75),(75,46.11),(80,51.76),(85,57.69),(90,63.89),(95,70.35),(100,77.07),(105,84.05),(110,91.28),(115,98.75),(120,106.50),(125,114.40),(130,122.60),(135,131.00),(140,139.60),(145,148.50),(150,157.60),(155,166.80),(160,176.30),(165,186.00),(170,195.90),(175,206.00),(180,216.30),(185,226.70),(190,237.40),(195,248.30),(200,259.30),(205,270.50),(210,281.90),(215,293.40),(220,305.20),(225,317.10),(230,329.10),(235,341.30),(240,353.70),(245,366.30),(250,379.00)])

def ReadGiraffe(filename):
    file = open(filename,'r')
    FullData=[]
    for line in file:
        FullData.append((line.rstrip().lstrip()))
    XData = FullData[1+FullData.index('Curve depth: [mm]')].split(';')
    YData = FullData[1+FullData.index('Curve gains: [counts]')].split(';')

    Data=[XData,YData]
    Data=asarray(Data)
    # print(Data)
    Data = (Data.astype(float)).transpose()

    maxy = max(Data[1]) # Find the maximum value in the y data
    Data[1] = 100*Data[1]/maxy # Convert all values to percentages with dmax = 100%

    DATE = FullData[1][6:16]
    DATE = datetime.datetime.strptime(DATE,'%Y-%m-%d').strftime('%d/%m/%Y')



    return Data, DATE

def ReadTank(filename):
    file = open(filename,'r')
    FullData=[]
    for line in file:
        FullData.append((line.rstrip().lstrip()))
        # print(line.rstrip().lstrip())

    BEGIN_DATA = 1+FullData.index('BEGIN_DATA')
    END_DATA = FullData.index('END_DATA')

    ENERGY_Index = [i for i, elem in enumerate(FullData) if 'ENERGY' in elem]
    ENERGY = FullData[ENERGY_Index[0]][7:]
    ENERGY = float(ENERGY)

    DATE_Index = [i for i, elem in enumerate(FullData) if 'MEAS_DATE' in elem]
    DATE = FullData[DATE_Index[0]][10:-9]
    DATE = datetime.datetime.strptime(DATE,'%d-%b-%Y').strftime('%d/%m/%Y')

    GantryAngle_index = [i for i, elem in enumerate(FullData) if 'GANTRY=' in elem]
    GantryAngle = FullData[GantryAngle_index[0]][7:]

    Data=[]
    for i in range(BEGIN_DATA,END_DATA,1):
        Data.append(FullData[i].split())
    Data = asarray(Data)
    Data = (Data.astype(float))
    maxy = max(Data[1]) # Find the maximum value in the y data
    Data[1] = 100*Data[1]/maxy # Convert all values to percentages with dmax = 100%
    # print(Data)
    return Data, ENERGY, DATE, GantryAngle

def ProximalDepthSeeker(Dose,datax,datay): # same as previous formula but approaching data from the front
        warnings.filterwarnings('ignore') # Prevents the "NaN" error message in the python display
        index = argmax((asarray(datay))>Dose)
        y0 = (datay[index-1])
        y1 = (datay[index])
        x0 = (datax[index-1])
        x1 = (datax[index])
        slope = ((y1-y0)/(x1-x0)) # calculate the gradient - note a linear interpolation is performed
        intercept = y0-(slope*x0) # calculate the theoretical intercept
        proximal = (Dose-intercept)/slope # finds x value for given Dose level
        return proximal; #Out put the value for use later

def DistalDepthSeeker(Dose,datax,datay): # Define a formula to find x for a given y in the distal fall off
        warnings.filterwarnings('ignore') # Prevents the "NaN" error message in the python display
        index = argmax((asarray(list(reversed(datay))))>Dose) # Find the first value that exceeds the "Dose" value approaching from greatest x value
        y0 = (datay[len(datay)-index-1]) # These 4 lines fetch the points either side of the value
        y1 = (datay[len(datay)-index])
        x0 = (datax[len(datax)-index-1])
        x1 = (datax[len(datax)-index])
        slope = ((y1-y0)/(x1-x0)) # calculate the gradient - note a linear interpolation is performed
        intercept = y0-(slope*x0) # calculate the theoretical intercept
        distal = (Dose-intercept)/slope # finds x value for given Dose level
        return distal; # Output the value for later use

class PeakProperties:
    def __init__(self, NISTRange, Prox80, Prox90, Dist90, Dist80, Dist20, Dist10, PTPR):
        self.NISTRange = NISTRange
        self.Prox80 = Prox80
        self.Prox90 = Prox90
        self.Dist90 = Dist90
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
        NISTRange = interp(Energy,NIST[:,0],NIST[:,1]) #Performs linear interpolation between NIST data points if Energy isn't available
    datax = asarray([x[0] for x in Data]) # Collects X data

    datay = asarray([y[1] for y in Data]) # Collects Y data
    maxy = max(datay) # Find the maximum value in the y data
    datay = 100*datay/maxy # Convert all values to percentages with dmax = 100%

    Plateaux = interp(25,datax,datay)
    PTPR = 100/Plateaux # Calcualtes peak to plateau ratio

    Data_Props = PeakProperties(NISTRange, ProximalDepthSeeker(80,datax,datay), ProximalDepthSeeker(90,datax,datay), DistalDepthSeeker(90,datax,datay), DistalDepthSeeker(80,datax,datay), DistalDepthSeeker(20,datax,datay), DistalDepthSeeker(10,datax,datay), PTPR)

    return (Data_Props)
