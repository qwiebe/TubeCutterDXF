import ezdxf
from ezdxf import units
from math import pi
from prettytable import PrettyTable
import matplotlib.pyplot as plt
import os
from time import sleep
import numpy as np
from pick import pick
from colorama import Fore, Back, Style
import json

# doc = ezdxf.new()
# doc.units = units.MM

# msp = doc.modelspace()
# msp.add_line((0,0), (1,0), dxfattribs={"layer": "MyLayer"})

# doc.saveas("new_dxf.dxf")

PRECISION = 0.000001
ROUND = 6

def clearConsole():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

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
                percentOver = y_end / cutLength_c
                x_end_temp = x_end - (x_end - x_start) * percentOver

                # if (abs(self.c - y_start) > PRECISION):
                if (abs(y_end - y_start) > PRECISION):
                    if y_end > 3.14:
                        print(i)
                    self.lines.append(((x_start, y_start), (x_end_temp, self.c)))
            
                x_start = x_end_temp
                y_start = 0
            
            if (abs(y_end - y_start) > PRECISION):
                if y_end > 3.14:
                    print(i)
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
                y_start = round(y_start % self.c, ROUND)
                y_end = round(y_end % self.c, ROUND)
        
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
                self.cutLength_c += self.cutIncrease_c
            
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

    def draw(self, filename):
        doc = ezdxf.new()
        doc.units = units.MM
        msp = doc.modelspace()

        for start, end in self.lines:
            msp.add_line(start, end, dxfattribs={"layer": "MyLayer"})
            print("start: ", start)
            print("end ", end)

        doc.saveas(filename)
    
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
    _cuts = []
    _dxf = ezdxf.new()

    def __init__(self):
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
        self._dxf.saveas(filename)

        # Save Config File
        data = {}
        i = 0
        for cut in self._cuts:
            data[cut.type + i] = cut.dumpConfig()
            i += 1
        
        with open(f'./output/{filename}.json', 'w') as f:
            json.dump(data, f)

    def getCuts(self):
        return self._cuts
    
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
            table.add_row([i, cut.offsetX, cut.instances, cut.pitch])
            i += 1

        print(table)



def main():
    # Create the Pattern container
    pattern = CutPattern()

    # Specify some general parameters
    OD = 1
    continuous = False

    # Define the cut pattern
    cutSpiralF = CutSpiral(OD, 24*25.4, 0, 85, 17.857, 0.178, 10, continuous=continuous)
    cutSpiralB = CutSpiral(OD, 24*25.4, 360-17.857, 85, 17.857, -0.178, 4, continuous=continuous)

    # Add the cut patterns to the Pattern container
    pattern.add(cutSpiralF)
    pattern.add(cutSpiralB)

    # Print table
    pattern.printCutTable()

    # Draw and Save the pattern to a file
    pattern.draw()
    pattern.save("./output/test.dxf")


def main_old():

    doc = ezdxf.new()
    doc.units = units.MM

    OD = 1

    continuous = False

    # cutPartline = CutPartline(OD)
    # cutSpiral1 = CutSpiral(OD, 5, 0, 85, 17.857, 0.178, 294, continuous=continuous)
    # cutSpiral2 = CutSpiral(OD, cutSpiral1.xNext, cutSpiral1.yNext / cutSpiral1.c * 360, 85, 17.857, 0.178, 950, True, -0.085, 0.085, continuous=continuous)
    # cutSpiral3 = CutSpiral(OD, 24*25.4, 360-17.857, 85, 17.857, -0.178, 4, True, -0.038, 0.038, continuous=continuous)
    # cutSpiral4 = CutSpiral(OD, 24*25.4, 0, 85, 17.857, 0.178, 4004, continuous=continuous)
    # cutSpiral5 = CutSpiral(OD, cutSpiral4.xNext, cutSpiral4.yNext / cutSpiral4.c * 360, 85, 17.857, 0.178, 1995, True, -0.038, 0.038, continuous=continuous)

    cutSpiralF = CutSpiral(OD, 24*25.4, 0, 85, 17.857, 0.178, 10, continuous=continuous)
    cutSpiralB = CutSpiral(OD, 24*25.4, 360-17.857, 85, 17.857, -0.178, 4, continuous=continuous)
    cutSpiralF.draw(doc)
    cutSpiralB.draw(doc)
    # cutPartline.draw(doc)
    # cutSpiral1.draw(doc)
    # cutSpiral2.draw(doc)
    # cutSpiral3.draw(doc)
    # cutSpiral4.draw(doc)
    # cutSpiral5.draw(doc)
    
    doc.saveas("test12.dxf")

def cmdUImain(argv):
    plt.ion()

    # Create the Pattern container
    pattern = CutPattern()
    pattern.add(CutSpiral(1, 1, 0, 30, 60, 0.5, 5))

    exit = False

    clearConsole()
    print(f'+------------------------------------+')
    print(f'|      WELCOME TO {Fore.CYAN}TubeCutterDXF{Fore.WHITE}      |')
    print(f'|           by {Fore.LIGHTBLUE_EX}four{Fore.WHITE}+{Fore.MAGENTA}one{Fore.WHITE}              |')
    print(f'+------------------------------------+')
    # print('Set the OD for this project')
    try:
        OD = float(input('OD (mm): '))
    except ValueError:
        print('Invalid entry for OD')

    print('')

    while (not exit):
        clearConsole()
        pattern.printCutTable()
        pattern.plot()

        print('\t[0] Add Cut')
        print('\t[1] Delete Cut')
        print('\t[2] Save')
        print('')

        try:
            cmd = int(input('Command: '))
            # option, cmd = pick(['Add Cut', 'Delete Cut', 'Save'], 'Command:', indicator='>', clear_screen=False)

            if cmd == 0:
                # cutType, index = pick(['Brick', 'Spiral', 'Partingline'], 'Select Cut Type: ', indicator='>', clear_screen=False)
                cutType = input('Brick [B] or Spiral [S] or PartingLine [P]: ')
                if cutType in ['Brick', 'B']:
                    offsetX = float(input('offsetX: '))
                    offsetA = float(input('offsetA: '))
                    cutLength = float(input('cutLength: '))
                    numRadialCuts = int(input('numRadialCuts: '))
                    spacingA = float(input('spacingA: '))
                    pitch = float(input('pitch: '))
                    variableCutLength = int(input('variable Cut Length? [1/0]: '))
                    cutIncrease = float(input('cutIncrease: '))
                    instances = int(input('instances: '))
                    pattern.add(CutBrick(OD, offsetX, offsetA, cutLength, numRadialCuts, spacingA, pitch, instances, variableCutLength, cutIncrease))

                elif cutType in ['Spiral', 'S']:
                    offsetX = float(input('offsetX: '))
                    offsetA = float(input('offsetA: '))
                    cutLength = float(input('cutLength: '))
                    unCutLength = float(input('unCutLength: '))
                    variableCutLength = int(input('variable Cut Length? [1/0]: '))
                    cutIncrease = float(input('cutIncrease: '))
                    unCutIncrease = float(input('unCutIncrease: '))
                    pitch = float(input('pitch: '))
                    instances = int(input('instances: '))
                    pattern.add(CutSpiral(OD, offsetX, offsetA, cutLength, unCutLength, pitch, instances, variableCutLength, cutIncrease, unCutIncrease))

                elif cutType in ['Partingline', 'P']:
                    offsetX = float(input('offsetX: '))
                    pattern.add(CutPartline(OD, offsetX))

            elif cmd == 1:
                Idx = int(input('Cut #: '))
                pattern.remove(Idx - 1)

            elif cmd == 2:
                filename = input('Filename: ')
                pattern.save(f'./output/{filename}.dxf')
            
            else:
                print(f'{cmd} is not a valid command')
                sleep(1)

        except Exception as e:
            print(e)
            sleep(1)


if __name__ == '__main__':
    import getopt, sys

    argv = sys.argv[1:]
    # cmdUImain(argv)
    main()