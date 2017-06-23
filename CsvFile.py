# -*- coding: utf-8 -*-
"""
Created on Fri Apr 07 14:46:38 2017

@author: Jesse Trinity (Coleman Lab)
"""

import csv as csv

class CsvFile:
    def __init__(self, filename):
        self.filename = filename
        self.settings = dict()
        self.timestamps = list()
        
    def open_csv(self):
        with open(self.filename, 'rb') as csvfile:
            rows = list()
            reader = csv.reader(csvfile, delimiter = ',')
            for row in reader:
                rows.append(row)
            self.settings = dict(zip(rows[0], rows[1]))
            self.timestamps = rows[2:]

if __name__ == '__main__':
    f = CsvFile('C:/Users/jesse/Desktop/VLdata/SRP34_py_45d_d2.csv')
    f.open_csv()