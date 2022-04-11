"""
Author: Trenz Electronic GmbH / Kilian Jahn 27.09.2019 - edited 25.02.2020
Edited within the Python version:   3.7.3

This module is part of the example on using the ADC of the Trenz modules TEI0015,
TEI0016 and TEI023.
Further explonations are available in the Trenz Electronic wiki.
"""


import serial  # Serial/Comport connection
from scipy.fftpack import fft # FFT 
import numpy as np # FFT window function generating data
from matplotlib import pyplot as plt  # Plotting of Graphs
import pandas as pd
import time





def downloadData(adcData):
    data = {'Time (ms)':adcData[0],'ADC Voltage (V)':adcData[1]}
    df = pd.DataFrame(data=data)
    todaysDate = time.strftime("%d-%m-%Y")
    excelfilename = todaysDate + " Input Voltage (" + adcData[2] + ") " +".xlsx"
   # df.to_excel(r'C:\Users\phia_\Documents\Capstone\AnalogDAQ3\VoltageData' + adcData[2] + '.xlsx', index = False)
    df.to_excel(excelfilename, index = False)
   

def downloadLIAData(adcData):
    data = {'Channels':adcData[0],'Magnitude (V)':adcData[1], 'Phase (rad)' :adcData[2]}
    df = pd.DataFrame(data=data)
    todaysDate = time.strftime("%d-%m-%Y")
    excelfilename = todaysDate + " LIA Output (" + adcData[3] + ") " +".xlsx"
   # df.to_excel(r'C:\Users\phia_\Documents\Capstone\AnalogDAQ3\VoltageData' + adcData[2] + '.xlsx', index = False)
    df.to_excel(excelfilename, index = False)

def getModuleId(comport):
    moduleId = 0 # Default error value
    try:# Timeouts, because this function is a "gate keeper" to the program
        handleComport = serial.Serial(comport, 115200, timeout = 0.5, write_timeout = 0.5)
        handleComport.reset_output_buffer()
        handleComport.reset_input_buffer()
        handleComport.write(bytearray("?", 'utf8'))        
        moduleId = int(handleComport.read())
        handleComport.close()
    except:
        print("Error determine module ID")
    return moduleId
        

def sendCommand(comport, command):
    try:
        handleComport = serial.Serial(comport, 115200)
        handleComport.reset_output_buffer()
        handleComport.write(bytearray(str(command),'utf8'))
        handleComport.close()
    except:
        print("Error send command")
    

# Collect the samples and convert them.
# Return values are: real measured Volts/floats, Normalized to +/- 1/floats
# and as steps in between +/- maximumum integer 
def dataCollect(comport, samples, target):
    # Function variables
    adcSamples = 16384
    #import time
    adcByteList = 0
    adcSignalVolt = []    
    adcSignalFloatNormalized = []
    adcSignedInteger = []
    # Connect to comport, clean buffer and get maximum sampling frequencie of the module
    handleComport = serial.Serial(comport, 115200)
    handleComport.reset_output_buffer()
    handleComport.write(bytearray("t",'utf8')) # Trigger the adc   
    # Collect the data
 #   t_end = time.time() + 3
        
 #   while time.time() < t_end:
    for i in range(1, samples, 16):
        try:
            handleComport.reset_input_buffer()
            handleComport.write(bytearray("*",'utf8')) # Read 16384 adc values 
            if target == 1: # Select the module according to target
                adcByteList = handleComport.read(5*adcSamples)
                dataConvertTEI0015(adcByteList, adcSamples, adcSignalVolt, adcSignalFloatNormalized, adcSignedInteger)
            elif target == 2 or target == 3:
                adcByteList = handleComport.read(4*adcSamples)
                dataConvertTEI0016(adcByteList, adcSamples, adcSignalVolt, adcSignalFloatNormalized, adcSignedInteger)
            elif target == 4:
                adcByteList = handleComport.read(5*adcSamples)
                dataConvertTEI0023(adcByteList, adcSamples, adcSignalVolt, adcSignalFloatNormalized, adcSignedInteger)
            adcByteList = 0
        except:
            print("ADC data not aquired, stored or processed")
    handleComport.close()
    
    return [adcSignalVolt, adcSignalFloatNormalized, adcSignedInteger]
    
    
# Separte binary data into single values and convert them to a voltage, integer and normalized list

# ADC = AD4003BCPZ-RL7 18-bit 2 MSps
def dataConvertTEI0015(adcByteList, adcSamples, adcSignalVolt, adcSignalFloatNormalized, adcSignedInteger):
    for adcSingleValue in range(0, adcSamples):
        adcSingleValue = ((adcSingleValue)*5) # 5 nibble = 20 > 18 bit
        # ADC resolution is 18bit, positive values reach from 0 to 131071, 
        # negatives values from 131072 to 262142        
        adcIntRaw = int(adcByteList[adcSingleValue:adcSingleValue+5], 16)
        if adcIntRaw > 131071:
            adcIntRaw = int(adcIntRaw - 262142)
        adcSignalVolt.append(float(adcIntRaw)*(2*4.096*1/0.4)/262142) # (2*Vref*ADCgain) / 2*maxInt
        adcSignalFloatNormalized.append(adcIntRaw/131071)
        adcSignedInteger.append(adcIntRaw)
        
        
# ADC = ADAQ7988, 16-bit 0.5 MSps
# ADC = ADAQ7980, 16-bit 1 MSps
def dataConvertTEI0016(adcByteList, adcSamples, adcSignalVolt, adcSignalFloatNormalized, adcSignedInteger):
    for adcSingleValue in range(0, adcSamples):
        adcSingleValue = ((adcSingleValue)*4)
        # ADC resolution  is 16bit, negative full scale is 0, 
        # mid scale is 0x8000 / 32768 and pos full scale is 0xffff / 65536
        adcIntRaw = int(adcByteList[adcSingleValue:adcSingleValue+4], 16)
        adcIntRaw = int(adcIntRaw - 65536 / 2)
        adcSignalVolt.append(float(-1*(adcIntRaw)*2*4*0.5*5.0/65536)) # (2*Vref*ADCgain) / 2*maxInt
        adcSignalFloatNormalized.append(adcIntRaw / 65536)
        adcSignedInteger.append(adcIntRaw)
        
        
# ADC = ADAQ4003BBCZ 18-bit 2 MSps
def dataConvertTEI0023(adcByteList, adcSamples, adcSignalVolt, adcSignalFloatNormalized, adcSignedInteger):
    for adcSingleValue in range(0, adcSamples):
        adcSingleValue = ((adcSingleValue)*5) # 5 nibble = 20 > 18 bit
        # ADC resolution is 18bit, positive values reach from 0 to 131071, 
        # negatives values from 131072 to 262142        
        adcIntRaw = int(adcByteList[adcSingleValue:adcSingleValue+5], 16)
        #adcIntRaw = int(adcByteList[adcSingleValue:adcSingleValue+5], 5)
        if adcIntRaw > 131071:
        #if adcIntRaw > 65:
            adcIntRaw = int(adcIntRaw - 262142)
            #adcIntRaw = int(adcIntRaw - 130)
        adcSignalVolt.append(float(adcIntRaw)*(2*5.0*1/0.45)/262142) # (2*Vref*ADCgain) / 2*maxInt 149
        #adcSignalVolt.append(float(adcIntRaw)*(2*5.0*1/0.45)/130) # (2*Vref*ADCgain) / 2*maxInt 149
        adcSignalFloatNormalized.append(adcIntRaw/131071)
        #adcSignalFloatNormalized.append(adcIntRaw/65)
        adcSignedInteger.append(adcIntRaw)
        
    
# Generate the FFT and ists Frequencye list
def performeFFTdbFS(samplerate, signal):    
    # Function variables
    frequencies = 0
    sampleLength = 0
    window = 0
    windowed = 0
    fftSignal = 0  
    
    # Generate list of frequencies for the x axis
    sampleLength = int(len(signal)/2+1)
    frequencies = np.linspace(0, samplerate/2, sampleLength, endpoint=True)
    # Generate windowed signal and perform Fourier transformation on it + some math
    window = np.hanning(len(signal))
    fftSignal = np.fft.fft(window*signal)
    # Convert to the usefull spectrum
    fftSignal = 2*np.abs(fftSignal[:sampleLength])/sampleLength
    # Convert to dbFS
    with np.errstate(divide='ignore', invalid='ignore'):
        fftSignal = 20 * np.log10(fftSignal)  
    
    return [frequencies/1000, fftSignal]   

# Plot the graphs
def plottingGraphs(mode, labelPlot, labelAxisX, labelAxisY, plotData, axisLimits):
    if(len(plotData) == 2):
        fig = plt.figure()
        plt.axes().grid(True)
        fig.suptitle(labelPlot, fontsize='13', fontweight='bold')
        plt.xlabel(labelAxisX)      
        plt.ylabel(labelAxisY)
        plt.plot(plotData[0], plotData[1])
        plt.ylim(axisLimits[2],axisLimits[3])    
        if mode == 0:        
            plt.xlim(axisLimits[0],axisLimits[1])
    else:
        fig = plt.figure()
        plt.axes().grid(True)
        fig.suptitle(labelPlot, fontsize='13', fontweight='bold')
        plt.xlabel(labelAxisX)      
        plt.ylabel(labelAxisY)
        plt.plot(plotData[0], plotData[1], label="Received")
    #    fig.show()
        plt.plot(plotData[0], plotData[2], label="Reference")
        plt.plot(plotData[0], plotData[3], label="Mixed")
        plt.plot(plotData[0], plotData[4], label="Mean")
        plt.legend()
        plt.ylim(axisLimits[2],axisLimits[3])    
        if mode == 0:        
            plt.xlim(axisLimits[0],axisLimits[1])
        
    fig.show()
    return fig
    
# Check if the data exceeds the ADC range too often
def signalLimitsExceed(signal, maxAbsValue):
    exceedCounter = 0    
    for element in signal:
        if abs(element) > maxAbsValue:
            exceedCounter += 1
    return exceedCounter
    
    
    