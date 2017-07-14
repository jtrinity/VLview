# -*- coding: utf-8 -*-
"""
Opens and interprets experiment files

Created on Fri Apr 07 16:07:47 2017

@author: Jesse Trinity (Coleman Lab)
"""

import BinFile as BF
import CsvFile as CF
import numpy as np
import itertools
from os import path as path

class Experiment:
    def __init__(self, binfilename, csvfilename, trigger):
        self.start_time = 0
        self.signal_channel = 0
        self.timing_channel = 2
        self.threshold = 0.5
        self.sampling_frequency = 1000
  
        self.binfilename = binfilename
        self.csvfilename = csvfilename
        
        self.short_name = path.split(csvfilename)[1]
        self.signal, self.timing = self.channels_from_trigger(binfilename, csvfilename)
        self.bin_timestamps, self.csv_timestamps = self.get_timestamps(self.signal, self.timing, trigger)
        #self.flip_times, self.flop_times, self.flips, self.flops, self.flip_avgs, self.flop_avgs, self.trial_avgs = self.get_reversal_times(self.signal, self.bin_timestamps, self.csv_timestamps)
        self.stims = self.get_stims(self.signal, self.bin_timestamps, self.csv_timestamps)
        self.stims.sort()
        #stims stored in dictionary acording to filename - cluttered structures, trim down tree?
        self.stim_names = {stim.name: stim for stim in self.stims}
        self.root = self.build_stim_tree(self.stims)
        
    def set_threshold(self, t):
        try:
            assert(type(t)) == float
            self.threshold = t
        except AssertionError:
            print "threshold must be a float"

    def set_sampling_frequency(self, f):
        try:
            assert(type(f)) == float
            self.sampling_frequency = f
        except AssertionError:
            print "sampling frequency must be a float"
        
        
    #cuts off signal and timestamp channels from falling edge of trigger
    def channels_from_trigger(self, binfilename, csvfilename):
        self.binfile = BF.BinFile(binfilename)
        self.binfile.open_bin()
        self.csvfile = CF.CsvFile(csvfilename)
        self.csvfile.open_csv()
        
        trigger_off = 0

        for i in range(1, len(self.binfile.data[0])):
            if self.binfile.data[2][i] < self.threshold and self.binfile.data[2][i-1] > self.threshold:
                trigger_off = i
                break
        
                
        signal = self.binfile.data[self.signal_channel][trigger_off:]
        timing = self.binfile.data[self.timing_channel][trigger_off:]
        
        self.start_time = trigger_off
        
        return signal, timing
    
    
    #gets rising edge sample points. returns signal timestamps and csv file timestamps
    def get_timestamps(self, signal, timing, trigger):
        
        #cut off 500ms at ends
        buffer_samples = int(self.sampling_frequency / 2.0)
        bin_timestamps = list()
        
        #get onsets (singal LOW-> HIGH)
        for i in range(buffer_samples, len(timing)-buffer_samples):
            if timing[i+1] >= self.threshold and timing[i] < self.threshold:
                bin_timestamps.append(i)
            #get trigger (HIGH -> LOW as well if trigger type is continuous)
            if trigger == 1 and timing[i+1] <= self.threshold and timing[i] > self.threshold:
                bin_timestamps.append(i)
        #Ignore offset on last trigger
#        if trigger == 1:
#            bin_timestamps.pop()
            
        
#        print "deviant lengths"
        lengths = list()
        for i in range(1,len(bin_timestamps)):
            lengths.append(bin_timestamps[i]-bin_timestamps[i-1])
        
        csv_timestamps = list()
        
        for i in range(len(self.csvfile.timestamps)):
            csv_timestamps.append((int(float(self.csvfile.timestamps[i][0])*self.sampling_frequency - self.start_time), self.csvfile.timestamps[i][1], self.csvfile.timestamps[i][2]))
        
        return bin_timestamps, csv_timestamps
        
    #returns a list of stim objects containing signal segments and event data
    def get_stims(self, signal, bin_timestamps, csv_timestamps):
        
        event_list = [x[1] for x in csv_timestamps]
        
        print "csv " + str(len(event_list)) + " bin " +str(len(bin_timestamps)) 
        assert(len(event_list) == len(bin_timestamps))

        #start_padding = signal[0:bin_timestamps[0]]
        #end_padding = signal[bin_timestamps[-1]:signal[-1]]
        stims = [Stim("Stim "+str(i).zfill(4) + " "+self.short_name, signal[bin_timestamps[i]:bin_timestamps[i+1]], bin_timestamps[i], bin_timestamps[i+1], csv_timestamps[i]) for i in range(len(bin_timestamps)-1)]
        stims.append(Stim("Start "+self.short_name, signal[0:bin_timestamps[0]], 0, bin_timestamps[0], (0, 'gray', '0')))
        stims.append(Stim("End "+ self.short_name, signal[bin_timestamps[-1]:len(signal)-1], bin_timestamps[-1], len(signal)-1, csv_timestamps[-1]))

        return stims
    
    def build_stim_tree(self, stims):
        #find relaxations intervals and separate stims into blocks
        gray_indices = [i for i in range(len(self.stims)) if self.stims[i].type == ('gray', '0')]
        blocks = [[gray_indices[i],gray_indices[i+1]] for i in range(len(gray_indices)-1)]
        
        #make list of unique stim types + orientations
        stim_types = self.stim_types()
        try:
            stim_types.remove('gray')
        except:
            pass
        #add reversal 'stim type' if flip flops detected
        if 'flip' in stim_types and 'flop' in stim_types:
            stim_types.append('flip-flop')
            
        #remove integer zero orientation (gray/interstim interval)
        orientations = self.orientations()
        orientations.remove('0')
        
        unique_stims = list(itertools.product(stim_types, orientations))
        stimBlocks = {stim:list() for stim in unique_stims}
        for i in range(len(blocks)):
            interval = blocks[i]
            for stim_type in stimBlocks:
                stims = [self.stims[j] for j in range(interval[0]+1, interval[1]) if self.stims[j].type == stim_type]
                #if reversal type...
                if stim_type[0] == 'flip-flop':
                    stims_flip = [self.stims[j] for j in range(interval[0]+1, interval[1]) if self.stims[j].type == ('flip',stim_type[1])]
                    stims_flop = [self.stims[j] for j in range(interval[0]+1, interval[1]) if self.stims[j].type == ('flop',stim_type[1])]
                    stims_flip.sort()
                    stims_flop.sort()
                    stims = [CombinedStim('flip-flop '+a.name[0:9]+'-'+b.name, [a,b], method = "average") for (a,b) in zip(stims_flip, stims_flop)]
                    self.stim_names.update({stim.name:stim for stim in stims})
                    
                #if scanned block contains any stim of selected type
                if len(stims) > 0:
                    currentBlock = CombinedStim(' '.join([str(w) for w in stim_type]) + " Block " + str(i).zfill(4) + " " + self.short_name, stims, method = "average")
                    stimBlocks[stim_type].append(currentBlock)
                    self.stim_names[currentBlock.name] = currentBlock
        
        print stimBlocks
        grand_averages = [CombinedStim(' '.join([str(w) for w in stim_type]) + " Grand Average " + self.short_name, stimBlocks[stim_type]) for stim_type in stimBlocks]
        

        for average in grand_averages:
            self.stim_names[average.name] = average
        return {avg.name: avg for avg in grand_averages}
        
    def stim_types(self):
        return list(set([x[1] for x in self.csv_timestamps]))
    
    def orientations(self):
        return list(set([x[2] for x in self.csv_timestamps]))

#Stim class contains raw signal with associated event properties  
class Stim:
    def __init__(self, name, signal, onset, offset, event, **kwargs):
        self.name = name
        self.signal = signal
        self.mean = np.average(signal, axis = 0)
                
        self.min=(signal.argmin(), signal.min(axis=0))
        self.max=(signal.argmax(), signal.max(axis=0))
        self.amplitude = self.max[1] - self.min[1]
        
        self.onset = onset
        self.offset = offset
        self.event = event
        #todo: review event signature for grating and led VEPS
        self.type = (event[1],event[2])
    
    def __cmp__(self, other):
        return cmp(self.onset, other.onset)

#Combined stims keep given signal with associated stim sets
#stims are trimmed to length of shortest given stim
class CombinedStim(Stim):
    def __init__(self, name, stims, **kwargs):
        stims.sort()
        self.stims = {stim.name: stim for stim in stims}
        
        valid_methods = ["average"]
        if "method" in kwargs:
            method = kwargs["method"]
            assert(method in valid_methods)
        else:
            method = "average"
        
        if "baseline" in kwargs:
            baseline = kwargs["baseline"]
        else:
            baseline = 10
            
        
        if method == "average":
            min_len = min([len(stim.signal) for stim in stims])
            #print min_len
            signal = np.average([(stim.signal[0:min_len] - np.average(stim.signal[0:baseline])) for stim in stims], axis = 0)

        
        onset = stims[0].onset
        offset = stims[-1].offset
        event = stims[0].event
        Stim.__init__(self, name, signal, onset, offset, event)
    
        
        
    
        
        
        
        
        
        