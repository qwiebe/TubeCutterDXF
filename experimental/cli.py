import os
import matplotlib.pyplot as plt
from tubecutterdxf import CutPattern, CutBrick, CutSpiral, CutPartline
from time import sleep

def clearConsole():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def main(argv):
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
                pattern.draw()
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
    main(argv)
