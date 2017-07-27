# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 14:07:57 2016

@author: Jesse Trinity (Coleman Lab)

gui for viewing VisualLight files
"""

import Tkinter as tk
import tkFileDialog
import VEPdata as VEPdata

import matplotlib
#matplotlib.use("TkAgg", warn=False)

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib import style
from matplotlib import pyplot as plt
import numpy as np

import platform



style.use("bmh")

#-----WIDGETS-----
#Generic window framework
class Window(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.bind("<FocusIn>", self.parent.on_focus_in)
        
        if ('title' in kwargs):
            self.title(kwargs['title'])
            
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    #kill root when this window is closed
    def on_closing(self):
        self.parent.destroy()
        

#Generic *gridded* button framework
class Button(tk.Button):
    def __init__(self, container, name, command, position):
        button = tk.Button(container, text = name, command = command)
        button.grid(row = position[0], column = position[1], padx = 5, pady  = 5, sticky = tk.N+tk.S+tk.E+tk.W)
        
     
#-----Main Application-----
class MainApp(tk.Tk):
    def __init__(self, master = None, *args, **kwargs):
        tk.Tk.__init__(self, master, *args, **kwargs)
        self.title("Main Window")
        
        #populate windows by (class, name)
        self.windows = dict()
        for (C, n) in ((ExperimentWindow,"Experiments"), (GraphWindow,"Graph")):
            window = C(self, title = n)
            self.windows[n] = window
        
        self.bind("<FocusIn>", self.on_focus_in)
                
        #create windows by name
#        window_names = ("window1", "window2")
#        windows = {name:Window(self.root, title = name) for name in window_names}
               
        #-----class widgets-----
        #labels
        self.title_frame= tk.Frame(self)
        self.title_frame.pack(side = "top")
             
        #ROW 1
        #Buttons
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side = "top")
        
        self.load_button = Button(self.button_frame, "Load Files", self.load, (1,0))
        
        self.button1 = Button(self.button_frame, "Combine Selected", self.combine_selected, (1,1))
        self.amplitudes = Button(self.button_frame, "Amplitudes", self.on_amplitude_press, (1, 2))
        self.latencies = Button(self.button_frame, "Latencies" , self.default_onclick, (1, 3))
        self.save = Button(self.button_frame, "Save" , self.on_save, (1, 4))

            
        self.slider_max = 500
        
        #ROW 2
        #sliders for min and max window selection
        self.min_label = tk.Label(self.button_frame, text="window min").grid(row =2, column = 0)
        self.min_slider = tk.Scale(self.button_frame, from_=0, to=self.slider_max, orient=tk.HORIZONTAL)
        self.min_slider.bind("<ButtonRelease-1>", self.on_slider_move)
        self.min_slider.set(25)
        self.min_slider.grid(row = 2, column = 1)
        
        self.max_label = tk.Label(self.button_frame, text="window max").grid(row =2, column = 2)
        self.max_slider = tk.Scale(self.button_frame, from_=0, to=self.slider_max, orient=tk.HORIZONTAL)
        self.max_slider.bind("<ButtonRelease-1>", self.on_slider_move)
        self.max_slider.set(250)
        self.max_slider.grid(row = 2, column = 3)
        
        stim_length_label = tk.Label(self.button_frame, text = "stim length")
        stim_length_label.grid(row = 2, column = 4)
        self.stim_length_slider = tk.Scale(self.button_frame, from_=100, to=1000, orient = tk.HORIZONTAL)
        self.stim_length_slider.grid(row = 2, column = 5)
        self.use_manual_length = tk.IntVar()
        self.use_manual_length_box = tk.Checkbutton(self.button_frame, text="set stim length", variable = self.use_manual_length).grid(row = 2, column =6)
        
        #ROW 3
        #trigger type selection
        trigger_label = tk.Label(self.button_frame, text = "trigger type:")
        trigger_label.grid(row  = 3, column = 0)
        self.trigger_type_var = tk.IntVar()
        self.trigger_type_var.set(0)
        self.pulse_trigger = tk.Radiobutton(self.button_frame, text = "pulse", variable = self.trigger_type_var, value = 0)
        self.pulse_trigger.grid(row = 3, column = 1)
        self.pulse_trigger = tk.Radiobutton(self.button_frame, text = "continuous", variable = self.trigger_type_var, value = 1)
        self.pulse_trigger.grid(row = 3, column = 2)
        
        
        #-----end widgets-----

        #variables
        self.view = "file"

        #raw signal graph
       
        #figure and canvas
        self.figure = Figure(figsize = (10,0.5), dpi = 100)
        self.subplot = self.figure.add_subplot(111)

        #self.subplot.set_aspect('auto')
        
#        toolbar_frame = tk.Frame(self.title_frame)
#        toolbar_frame.pack(side = tk.TOP)
        
        self.canvas = FigureCanvasTkAgg(self.figure, self.title_frame)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side = tk.TOP, padx = 10, pady = 10, fill = tk.BOTH)
        
#        toolbar = NavigationToolbar2TkAgg(self.canvas, toolbar_frame)
#        toolbar.update()
        self.canvas._tkcanvas.pack(side = tk.BOTTOM)
        
        self.canvas._tkcanvas.pack(side = tk.BOTTOM)
        self.plot([[0 for i in range(500)]])
        
        #set root window position (needs to happen last to account for widget sizes)
        self.update()
        self.hpos =  self.winfo_screenwidth()/2 - self.winfo_width()/2
        self.vpos = 0
        self.geometry("+%d+%d" % (self.hpos, self.vpos))
        
        self.mainloop()
    
    #Dummy command function
    def default_onclick(self):
        print "widget pressed"
    
    #Dummy event function
    def default_on_event(self):
        print "event detected"
        
    def on_focus_in(self, event):
        self.lift()
        for win in self.windows:
            self.windows[win].lift()
    
    def on_amplitude_press(self):
        selection = self.windows["Experiments"].get_selection(self.windows["Experiments"].file_list)
        self.windows["Graph"].show_amplitudes([VEPdata.experiments[name] for name in selection])
    
    def on_latency_press(self):
        selection = self.windows["Experiments"].get_selection(self.windows["Experiments"].file_list)
        self.windows["Graph"].show_amplitudes([VEPdata.experiments[name] for name in selection])
    
    #Open a file dialog and record selected filenames to self.file_names
    def load(self):
        files = tkFileDialog.askopenfilenames()
        if len(files) > 0:
            self.windows["Experiments"].add_files(files)
        
            self.plot([VEPdata.experiments[VEPdata.experiments.keys()[0]].timing])
    
    def plot(self, data):
        self.subplot.clear()
        
        for datum in data:
            self.subplot.plot(datum, zorder = 0)
        self.subplot.set_yticklabels([])
        self.subplot.set_xticklabels([])
        self.subplot.set_axis_off()
        
        self.figure.tight_layout()

        self.canvas.draw()
    
    def file_trace(self, onsets, offsets):
        onsets.sort()
        offsets.sort()
        self.subplot.clear()

        self.plot([VEPdata.experiments[VEPdata.experiments.keys()[0]].timing])
        
        for (onset, offset) in zip(onsets, offsets):
            self.subplot.axvspan(onset, offset, alpha=0.5, color='red', zorder = 10)
            
        self.canvas.draw()
    
    def combine_selected(self):
        w = self.windows["Experiments"]
        if self.view == "file":
            return
        elif self.view == "type":
            highlight = w.get_selection(w.type_list)
        elif self.view == "stim":
            highlight = w.get_selection(w.stim_list)
        else:
            return
        
        combined = VEPdata.combine([VEPdata.names[name] for name in highlight])
        self.windows["Graph"].plot([combined])
    
    def on_slider_move(self, evt):
        if self.max_slider.get() <= self.min_slider.get():
            self.min_slider.set(25)
            self.max_slider.set(100)
        self.windows["Graph"].plot(self.windows["Graph"].last_plots)
        pass
    
    def on_save(self):
        fn = tkFileDialog.asksaveasfilename(filetypes = [('pickle','.p')])
        if fn is not None:
            to_save = {VEPdata.experiments[exp].short_name:{"raw signal":VEPdata.experiments[exp].signal,
            "bin timestamps":VEPdata.experiments[exp].bin_timestamps,
            "csv timestamps":VEPdata.experiments[exp].csv_timestamps,
            "timestamp signal":VEPdata.experiments[exp].timing,
            "stims":VEPdata.get_amplitude_data(VEPdata.experiments[exp].root)} for exp in VEPdata.experiments}
            VEPdata.save(fn, to_save)
        
              
#-----Windows-----
#Left Window
class window_one(Window):
    def __init__(self, parent, *args, **kwargs):
        Window.__init__(self, parent, *args, **kwargs)
        #self.title("Window One")
        #Set window position (needs to happen last to account for widget sizes)
        #self.geometry("+%d+%d" % (0, 0))
        self.update()
        self.hpos = 0
        self.vpos = self.winfo_screenheight()/2 - self.winfo_height()/2
        self.geometry("+%d+%d" % ( self.hpos, self.vpos))

#Experiment window contains list of processed files and associated stims
class ExperimentWindow(Window):
    def __init__(self, parent, *args, **kwargs):
        Window.__init__(self, parent, *args, **kwargs)

        #stim lists
        list_frame = tk.Frame(self)
        list_frame.pack(side = tk.RIGHT)
        
        file_frame = tk.Frame(list_frame)
        file_frame.pack(anchor = 'ne')
        
        type_frame = tk.Frame(list_frame)
        type_frame.pack(anchor = 'ne')
        
        stim_frame = tk.Frame(list_frame)
        stim_frame.pack(side = tk.RIGHT)
        
        #events
        self.file_list = tk.Listbox(file_frame, selectmode="extended", exportselection=0, width = 50, height=5)
        self.file_list.pack(side = tk.TOP, padx = 10, pady = 10)
        self.file_list.bind('<<ListboxSelect>>', self.on_file_select)

        self.type_list = tk.Listbox(type_frame, selectmode="extended", exportselection=0, width = 50, height=5)
        self.type_list.pack(side = tk.TOP, padx = 10, pady = 10)
        self.type_list.bind('<<ListboxSelect>>', self.on_type_select)
        
        self.stim_list = tk.Listbox(stim_frame, selectmode="extended", exportselection=0, width = 50, height=30)
        self.stim_list.pack(side = tk.TOP, padx = 10, pady = 10)
        self.stim_list.bind('<<ListboxSelect>>', self.on_stim_select)
        if platform.system() == 'Mac':
            self.stim_list.bind('<Button-2>', self.on_stim_right_select)
        else:
            self.stim_list.bind('<Button-3>', self.on_stim_right_select)

        
        
        #set window position (needs to happen last to account for widget sizes)
        #self.geometry("+%d+%d" % (0, 0))
        self.update()
        self.hpos =  self.winfo_screenwidth() - self.winfo_width()
        self.vpos = self.winfo_screenheight()/2 - self.winfo_height()/2
        self.geometry("+%d+%d" % (self.hpos, self.vpos))
    
    #select and load csv files - bin files are matched to csv filenames
    def add_files(self, files):
        
        for fn in files:
            if fn[-4:] == ".csv":
                VEPdata.open_file(fn, int(self.parent.trigger_type_var.get()))
        self.file_list.delete(0, tk.END)
        for key in VEPdata.experiments:
            self.file_list.insert(tk.END, key)
    
    #callback for file_list
    def on_file_select(self, evt):
        self.parent.view = "file"
        self.file_select()
    
    #gets selected item of tk listox as python list
    def get_selection(self, list_name):
        
        selection = list_name.curselection()
        selection = [list_name.get(item) for item in selection]
        return selection
        
    #when a filename is selected in the Experiment window
    def file_select(self):
        #clear stim list and fill with stims from selected file
        self.type_list.delete(0, tk.END)
        selection = self.get_selection(self.file_list)
        
        self.parent.windows["Graph"].plot([VEPdata.experiments[filename] for filename in selection])
        for filename in selection:
            for stim in VEPdata.experiments[filename].root:
                self.type_list.insert(tk.END, VEPdata.experiments[filename].root[stim].name)
    

    #callback for type_list
    def on_type_select(self, evt):
        self.parent.view = "type"
        self.type_select()
    
    #
    def type_select(self):
        self.stim_list.delete(0, tk.END)
                
        selection = self.get_selection(self.type_list)
        
        #graph selected stims
        self.parent.windows["Graph"].plot([VEPdata.names[name] for name in selection])
                
        to_insert = list()
        
        #populate stim list
        for name in selection:
            keys = VEPdata.names[name].stims.keys()
            for key in keys:
                to_insert.append(key)
        
        to_insert.sort()
        for item in to_insert:
            self.stim_list.insert(tk.END, item)
            
        pass
    
    def on_stim_select(self, evt):
        self.parent.view = "stim"
        self.stim_select()

    #graph selected stim in stim wondow
    def stim_select(self):
        
        selection = self.get_selection(self.stim_list)
        
        onsets = [VEPdata.names[name].onset for name in selection]
        offsets = [VEPdata.names[name].offset for name in selection]
        
        self.parent.file_trace(onsets, offsets)
        
        self.parent.windows["Graph"].plot([VEPdata.names[name] for name in selection])
        
        pass
    
    #changes view between blocks and individual stims
    def on_stim_right_select(self, evt):
        self.parent.view = "stim"
        selection = self.get_selection(self.stim_list)
        
        if len(selection) > 0 and "Block" in selection[0]:
            self.stim_list.delete(0, tk.END)
            
            to_insert = list()
            for name in selection:
                keys = VEPdata.names[name].stims.keys()
                keys.sort()
                for key in keys:
                    to_insert.append(key)
                    
            to_insert.sort()
            for item in to_insert:
                self.stim_list.insert(tk.END, item)
        elif len(selection) > 0 and "Stim" in selection[0]:
            self.type_select()
            pass
        
        

#window for displaying the fraph
class GraphWindow(Window):
    def __init__(self, parent, *args, **kwargs):
        Window.__init__(self, parent, *args, **kwargs)
        
        #frames
        center_anchor = tk.Frame(self)
        center_anchor.pack(anchor = 'center')
        
        toolbar_frame = tk.Frame(center_anchor)
        toolbar_frame.pack(side = tk.TOP)
        graph_frame = tk.Frame(center_anchor)
        graph_frame.pack(side = tk.TOP)
        
        #figure and canvas
        self.last_plots = list()
        self.figure = Figure(figsize = (10,5), dpi = 100)
        self.subplot = self.figure.add_subplot(111)
        self.subplot.plot([0 for i in range(500)])

        self.canvas = FigureCanvasTkAgg(self.figure, graph_frame)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side = tk.TOP, padx = 10, pady = 10, fill = tk.BOTH)
        
        toolbar = NavigationToolbar2TkAgg(self.canvas, toolbar_frame)
        toolbar.update()
        self.canvas._tkcanvas.pack(side = tk.BOTTOM)
        
        cid = self.figure.canvas.mpl_connect('button_press_event', self.mouse_select)
        
        #shw window in center of screen
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        self.geometry("+%d+%d" % ( (w)/2 - 500, (h)/2-200))
    
    #get matplotlib x and y cooridnates on mouse click
    def mouse_select(self, evt):
        mouse_x = evt.xdata
        mouse_y = evt.ydata
        if type(mouse_x) == None or type(mouse_y) == None:
            return
        print mouse_x, mouse_y
    
    def show_amplitudes(self, data):
        self.subplot.clear()
        for experiment in data:
            amps = [stim.amplitude for stim in experiment.stims]
            bins=np.arange(min(amps), max(amps) + 0.01, 0.01)
            plt.hist(amps, bins=bins)
        self.canvas.draw()
    
    def show_latencies(self, data):
        self.subplot.clear()
        for experiment in data:
            mins = [stim.min[0] for stim in experiment.stims]
            bins=np.arange(min(mins), max(mins) + 0.01, 0.01)
            plt.hist(mins, bins=bins)
        self.canvas.draw()
            
    def plot(self, data):
        self.subplot.clear()
        self.last_plots = data
        
        wmin = self.parent.min_slider.get()
        wmax = self.parent.max_slider.get()
        
            
        for datum in data:
            datum.min = VEPdata.min_from_window(datum.signal, lower = wmin, upper = wmax)
            datum.max = VEPdata.max_from_window(datum.signal, lower = datum.min[0], upper = wmax)
            datum.amplitude = datum.max[1] - datum.min[1]
            
            #plt.plot(stim.signal)
            self.subplot.plot(datum.min[0],datum.min[1],marker='+', mew = 5, ms = 20, color='green')
            self.subplot.plot(datum.max[0],datum.max[1],marker='+', mew = 5, ms = 20, color='red')
            self.subplot.plot(datum.signal)

        self.canvas.draw()
        
        
app = MainApp()
