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
def open_file(filename, trigger):
        binfile = filename[0:-4] + "_data.bin"
        exp = Experiment.Experiment(binfile, filename, trigger)
        experiments[filename[0:-4]] = exp
        names.update(exp.stim_names)

def amplitude(data, **kwargs):
    return data.max[1] - data.min[1]
    
#Gives combined data
def combine(data, **kwargs):
    return Experiment.CombinedStim("view", data, **kwargs)

def save(filename, data):
    try:
        pickle.dump(data, open(filename, "wb"))
    #ignore empy file name
    except IOError:
        pass
    
def get_amplitude_data(data):
    try:
        #recursive case
        amplitudes = {data[stim].name: {"amplitude":data[stim].amplitude,
                      "min":data[stim].min,
                      "max":data[stim].max,
                      "stims":get_amplitude_data(data[stim].stims),
                      "signal":data[stim].signal} for stim in data}
    except AttributeError:
        #base case
        return {data[stim].name: {"amplitude":data[stim].amplitude,
                      "min":data[stim].min,
                      "max":data[stim].max,
                      "signal":data[stim].signal} for stim in data}
    return amplitudes

