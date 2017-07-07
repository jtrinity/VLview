# -*- coding: utf-8 -*-
"""
Created on Thu Jun 08 11:34:33 2017

@author: Jesse Trinity (Coleman Lab)

math functions to work on stim and experiment data
"""
import numpy as np
import Experiment
from matplotlib import pyplot as plt
import pickle as pickle



file_names = list()
stim_names = list()
experiments = dict()
names = dict()

#gets min within [lower, upper) bounds
#gets min of series if no bounds given
def min_from_window(data, **kwargs):
    lower = 0
    upper = len(data)
    if 'lower' in kwargs:
        lower = kwargs['lower']
    if 'upper' in kwargs:
        upper = kwargs['upper']

    minimum = data[lower:upper].min(axis=0)
    arg_minimum = data[lower:upper].argmin() + lower
    return arg_minimum, minimum

#gets max within [lower, upper) bounds
#gets max of series if no bounds given
def max_from_window(data, **kwargs):
    lower = 0
    upper = len(data)
    if 'lower' in kwargs:
        lower = kwargs['lower']
    if 'upper' in kwargs:
        upper = kwargs['upper']
    maximum = data[lower:upper].max(axis=0)
    arg_maximum = data[lower:upper].argmax() + lower
    return arg_maximum, maximum

#called by VEPview when csv files are selected - opens csv and bin files
def open_file(filename):
        binfile = filename[0:-4] + "_data.bin"
        exp = Experiment.Experiment(binfile, filename)
        experiments[filename[0:-4]] = exp
        names.update(exp.stim_names)

def amplitude(data, **kwargs):
    return data.max[1] - data.min[1]
    
#Gives combined data
def combine(data, **kwargs):
    return Experiment.CombinedStim("view", data, **kwargs)

def save(filename, data):
    pickle.dump(data, open(filename, "wb"))

if __name__ == "__main__":
    files = ['C:/Users/jesse/Desktop/VLdata/SRP29_16cm_45d_yellow_d2_data.bin',
    'C:/Users/jesse/Desktop/VLdata/SRP29_16cm_45d_yellow_d2.csv']
    file_list = list(files)
    csvfiles = [name for name in file_list if name[-4:] == ".csv"]
    binfiles = [name for name in file_list if name[-4:] == ".bin"]
    if len(csvfiles) != 1 and len(binfiles) != 1:
        print "please select a .bin file and a .csv file"
    else:
        exp = Experiment.Experiment(binfiles[0], csvfiles[0])
    mins = list()
    maxes = list()
    plt.figure(1)
    for stim in exp.stims:
        if stim.type in ["flip","flop"]:
            min_x, min_y = min_from_window(stim.signal, lower = 25, upper = 100)
            mins.append((min_x, min_y))
            max_x, max_y = max_from_window(stim.signal, lower = 100, upper = 200)
            maxes.append((max_x, max_y))
            #plt.plot(stim.signal)
            plt.plot([max_x],[max_y],marker='+', mew = 5, ms = 20)
    
    gray_indices = [i for i in range(len(exp.stims)) if exp.stims[i].type == "gray"]
    blocks = [[gray_indices[i],gray_indices[i+1]] for i in range(len(gray_indices)-1)]
    flipBlocks = list()
    flopBlocks = list()
    for i in range(len(blocks)):
        interval = blocks[i]
        flips = [exp.stims[j] for j in range(interval[0]+1, interval[1]) if exp.stims[j].type == "flip"]
        flops = [exp.stims[j] for j in range(interval[0]+1, interval[1]) if exp.stims[j].type == "flop"]
        flipBlocks.append(Experiment.CombinedStim("Flip Block " + str(i), flips, method = "average"))
        flopBlocks.append(Experiment.CombinedStim("Flop Block " + str(i), flops, method = "average"))
    
    plt.figure(2)
    #flips = [stim for stim in exp.stims if stim.type == "flip"]
    #flops = [stim for stim in exp.stims if stim.type == "flop"]
    
    #flipAvgs = Experiment.CombinedStim("flip averages",flips, method = "average")
    #flopAvgs = Experiment.CombinedStim("flop averages", flops)
    #combinedAvg = Experiment.CombinedStim("combined averages", [flipAvgs, flopAvgs])
    
    for block in flipBlocks:
        plt.plot(block.signal)
    
    plt.figure(3)
    
    for block in flopBlocks:
        plt.plot(block.signal)
    
    flipGrandAverage = Experiment.CombinedStim("Flip Grand Average", flipBlocks)
    flopGrandAverage = Experiment.CombinedStim("Flop Grand Average", flopBlocks)
    GrandAverage = Experiment.CombinedStim("Grand Average", [flipGrandAverage, flopGrandAverage])

#print min_from_window(trial_avgs)