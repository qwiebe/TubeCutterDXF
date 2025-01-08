import ezdxf
from ezdxf import units
from math import pi
from prettytable import PrettyTable
import matplotlib.pyplot as plt
import os
from datetime import datetime
from time import sleep
import numpy as np
from pick import pick
from colorama import Fore, Back, Style
import json

SOFTWARE_NAME = 'TubeCutterDxf' 
VERSION = '1.0'

PRECISION = 0.000001
ROUND = 6

MM = 1
M = 1000
INCH = 25.4
FEET = INCH * 12

def overflow(val, max=2*pi):
    temp = val % max
    
    return temp if temp > 0 else temp + max

class CutSpiral:
    def __init__(self, OD, offsetX, offsetA, cutLength, unCutLength, pitch, instances, variableCutLength=False, cutIncrease=0, unCutIncrease=0, continuous=False, CW=True):
        self.type = 'CutSpiral'
        self.OD = OD
        self.offsetX = offsetX
        self.offsetA = offsetA
        self.cutLength = cutLength
        self.unCutLength = unCutLength
        self.variableCutLength = variableCutLength
        self.cutIncrease = cutIncrease
        self.unCutIncrease = unCutIncrease
        self.pitch = pitch
        self.instances = instances
        self.continuous = continuous

        self.lines = list()

        # Normalized from 0 to 1
        # offsetA_n = round((overflow(self.offsetA, 360) if not continuous else self.offsetA) / 360, ROUND)
        offsetA_n = round(self.offsetA / 360, ROUND)
        cutLength_n = round(self.cutLength / 360, ROUND)
        cutSpace_n = round(self.unCutLength / 360, ROUND)
        cutIncrease_n = round(self.cutIncrease / 360, ROUND)
        cutSpaceIncrease_n = round(self.unCutIncrease / 360, ROUND)

        # Normalized from 0 to c (the circumference of the tube)
        self.c = round(self.OD * pi, ROUND)
        offsetA_c = round(self.c * offsetA_n, ROUND)
        cutLength_c = round(self.c * cutLength_n, ROUND)
        cutSpace_c = round(self.c * cutSpace_n, ROUND)
        cutIncrease_c = round(self.c * cutIncrease_n, ROUND)
        cutSpaceIncrease_c = round(self.c * cutSpaceIncrease_n, ROUND)

        x_d = (1 if CW else -1)
        y_d = (1 if pitch > 0 else -1) * x_d

        x_start = round(offsetX, ROUND)
        x_end = round(x_start + cutLength_n * pitch, ROUND)
        y_start = round(offsetA_c, ROUND)
        # y_end = (y_start + cutLength_c) % self.c

        y_end = y_start + cutLength_c * y_d
        if not continuous:
            y_start = overflow(y_start, self.c)
            y_end = overflow(y_end, self.c)

        # y_end = round((y_start + cutLength_c * d) % (self.c if not continuous else 1), ROUND)

        for i in range(0, instances):
            '''
            Use Right Hand rule with thumb pointing distally (-x direction; or to the left)
            / == Clockwise (CW)
            \ == Counterclockwise (CCW, CW ==)
            S / E - y_s < y_e & x_s < x_e --- wrap around: y_s > y_e & x_s < x_e
            E / S - y_s > y_e & x_s > x_e --- wrap around: y_s < y_e & x_s > x_e
            S \ E - y_s > y_e & x_s < x_e --- wrap around: y_s < y_e & x_s < x_e
            E \ S - y_s < y_e & x_s > x_e --- wrap around: y_s > y_e & x_s > x_e

            Y = y_s < y_e
            X = x_s < x_e
            WA = wrap around necessary

            TYPE  | CW | Y | X | WA | - [(X XOR Y) XOR CW]
            S / E   T    T   T   F    F      F      T
            E / S   T    T   F   T    T      T      F
            S / E   T    F   T   T    T      T      F
            E / S   T    F   F   F    F      F      T
            S \ E   F    T   T   T    T      F      F
            E \ S   F    T   F   F    F      T      T
            S \ E   F    F   T   F    F      T      T
            E \ S   F    F   F   T    T      F      F
            
            '''
            # if ((y_start > y_end) and not continuous):
            if (not (((y_start < y_end) != (x_start < x_end)) != CW)):
                if y_d == 1:
                    percentOver = y_end / cutLength_c
                    y_end_temp = self.c
                    y_start_temp = 0
                elif y_d == -1:
                    percentOver = (self.c - y_end) / cutLength_c
                    y_end_temp = 0
                    y_start_temp = self.c

                x_end_temp = x_end - (x_end - x_start) * percentOver

                if (abs(y_end - y_start) > PRECISION):
                    # if y_end > 3.14:
                    #     print(i)
                    self.lines.append(((x_start, y_start), (x_end_temp, y_end_temp)))
            
                x_start = x_end_temp
                y_start = y_start_temp
            
            if (abs(y_end - y_start) > PRECISION):
                # if y_end > 3.14:
                #     print(i)
                self.lines.append(((x_start, y_start), (x_end, y_end)))

            if (self.variableCutLength):
                cutLength_n += cutIncrease_n
                cutLength_c = self.c * cutLength_n

                cutSpace_n += cutSpaceIncrease_n
                cutSpace_c = self.c * cutSpace_n

            x_start = x_end + cutSpace_n * pitch
            x_end = x_start + cutLength_n * pitch
            y_start = y_end + cutSpace_c * y_d
            y_end = y_start + cutLength_c * y_d

            if (not continuous):
                y_start = round(overflow(y_start, self.c), ROUND)
                y_end = round(overflow(y_end, self.c), ROUND)
                # y_start = round(y_start % self.c, ROUND)
                # y_end = round(y_end % self.c, ROUND)
        
        self.xNext = x_start
        self.yNext = y_start
    
    def dumpConfig(self):
        return {
            'type': self.type,
            'OD': self.OD,
            'offsetX': self.offsetX,
            'offsetA': self.offsetA,
            'cutLength': self.cutLength,
            'unCutLength': self.unCutLength,
            'variableCutLength': self.variableCutLength,
            'cutIncrease': self.cutIncrease,
            'unCutIncrease': self.unCutIncrease,
            'pitch': self.pitch,
            'instances': self.instances,
            'continuous': self.continuous
        }

    def plot(self):
        color = np.random.rand(3)
        for start, end in self.lines:
            plt.plot([start[0], end[0]], [start[1], end[1]], color=color)

    def draw(self, doc):
        msp = doc.modelspace()

        for start, end in self.lines:
            msp.add_line(start, end, dxfattribs={"layer": "MyLayer"})
            # print("start: ", start)
            # print("end ", end, "\n")

class CutBrick:
    def __init__(self, OD, offsetX, offsetA, cutLength, numRadialCuts, spacingA, pitch, instances, variableCutLength=False, cutIncrease=0, variablePitch=False, continuous=False):
        self.type = 'CutBrick'
        self.OD = OD
        self.offsetX = offsetX
        self.offsetA = offsetA
        self.cutLength = cutLength
        self.variableCutLength = variableCutLength
        self.cutIncrease = cutIncrease
        self.numRadialCuts = numRadialCuts
        self.spacingA = spacingA
        self.pitch = pitch
        self.variablePitch = variablePitch
        self.instances = instances
        self.continuous = continuous

        self.cutSpace = (360 / self.numRadialCuts) - self.cutLength

        self.c = self.OD * pi
        self.offsetA_c = self.offsetA / 360 * self.c
        self.cutLength_c = self.cutLength / 360 * self.c
        self.cutSpace_c = self.cutSpace / 360 * self.c
        self.cutIncrease_c = self.cutIncrease / 360 * self.c
        self.spacingA_c = self.spacingA / 360 * self.c

        self.lines = []

        x = self.offsetX
        y_start = self.offsetA_c
        y_end = (y_start + self.cutLength_c) % self.c

        for i in range(0, self.instances):
            for j in range(0, self.numRadialCuts):

                if y_start > y_end:
                    self.lines.append(((x, y_start), (x, self.c)))
                    y_start = 0
                
                self.lines.append(((x, y_start), (x, y_end)))

                y_start = y_end + self.cutSpace_c
                y_end = y_start + self.cutLength_c

                if (not self.continuous):
                    y_start = y_start % self.c
                    y_end = y_end % self.c
                
            if (self.variableCutLength):
                # self.cutLength += self.cutIncrease
                # self.cutLength_c = self.cutLength_c = self.cutLength / 360 * self.c

                # self.cutSpace = (360 / self.numRadialCuts) - self.cutLength
                # self.cutSpace_c = self.cutSpace_c = self.cutSpace / 360 * self.c
                self.cutLength_c += self.cutIncrease_c
                self.cutSpace_c = (self.c / self.numRadialCuts) - self.cutLength_c
            
            x += self.pitch

            y_start = y_start + self.spacingA_c
            y_end = y_start + self.cutLength_c

            if (not self.continuous):
                y_start = y_start % self.c
                y_end = y_end % self.c
            
            if (self.variablePitch):
                print("TBD")
    
    def dumpConfig(self):
        return {
            'type': self.type,
            'OD': self.OD,
            'offsetX': self.offsetX,
            'offsetA': self.offsetA,
            'cutLength': self.cutLength,
            'variableCutLength': self.variableCutLength,
            'cutIncrease': self.cutIncrease,
            'numRadialCuts': self.numRadialCuts,
            'spacingA': self.spacingA,
            'pitch': self.pitch,
            'variablePitch': self.variablePitch,
            'instances': self.instances,
            'continuous': self.continuous,
        }

    def plot(self):
        for start, end in self.lines:
            plt.plot([start[0], end[0]], [start[1], end[1]])

    def draw(self, doc):
        msp = doc.modelspace()

        for start, end in self.lines:
            msp.add_line(start, end, dxfattribs={"layer": "MyLayer"})
            # print("start: ", start)
            # print("end ", end, "\n")
    
class CutPartline:
    def __init__(self, OD, offsetX = 0):
        self.type = 'CutPartline'
        self.OD = OD
        self.c = OD * pi
        self.offsetX = offsetX
        self.lines = [((self.offsetX, 0), (self.offsetX, self.c))]
    
    def dumpConfig(self):
        return {
            'type': self.type,
            'OD': self.OD,
            'offsetX': self.offsetX,
        }

    def plot(self):
        for start, end in self.lines:
            plt.plot([start[0], end[0]], [start[1], end[1]])

    def draw(self, doc):
        msp = doc.modelspace()

        for start, end in self.lines:
            msp.add_line(start, end, dxfattribs={"layer": "MyLayer"})

class CutPattern:
    def __init__(self):
        self._cuts = []
        self._dxf = ezdxf.new()
        self._dxf.units = units.MM

    def add(self, cut):
        self._cuts.append(cut)

    def remove(self, cutIdx):
        self._cuts.pop(cutIdx)

    def draw(self):
        for cut in self._cuts:
            cut.draw(self._dxf)

    def save(self, filename):
        # Save DXF
        self._dxf.saveas(f'./output/{filename}.dxf')

        # Save Config File
        header = {SOFTWARE_NAME: {'Version': VERSION, 'Date': str(datetime.now())}}
        data = {}
        i = 0
        for cut in self._cuts:
            data[cut.type + str(i)] = cut.dumpConfig()
            i += 1
        
        header['config'] = data

        with open(f'./output/{filename}.json', 'w') as f:
            json.dump(header, f)

    def getCuts(self):
        return self._cuts
    
    def preview(self):
        self.plot()
        plt.show()

    def plot(self):
        for cut in self._cuts:
            cut.plot()

    def printCutTable(self):
        table = PrettyTable(['Cut #', 'Start X', 'Instances', 'Pitch'])
        table.align['Start X'] = 'l'
        table.align['Instances'] = 'r'
        table.align['Pitch'] = 'r'

        i = 1
        for cut in self.getCuts():
            offsetX = cut.offsetX or ''
            instances = cut.instances or ''
            pitch = cut.pitch or ''

            table.add_row([i, offsetX, instances, pitch])
            i += 1

        print(table)