import argparse
import csv
import numpy as np

MILLISECONDS = 1000.

def get_conversion(tps):
    return MILLISECONDS / tps


def parse_csv(data_file, sensors=('A', 'G'), tps=512.):
        signals = {}
        conversion = get_conversion(tps)
        for sensor in sensors:
            signals[sensor] = []
        with open(data_file, newline='') as csv_file:
            data_reader = csv.reader(csv_file)
            for line in data_reader:
                if len(line) > 0:
                    if line[0] in signals and len(line) == 5:
                        token = line[0]
                        dimensions = [int(i) for i in line[1:]]
                        dimensions[0] = int(dimensions[0] conversion)
                        signals[token].append(dimensions)
        return [np.array(signals[dim]) for dim in sensors]

class DataPreFormatter:

    def __init__(self):
        pass


def parse_args(_args=None):
    parser = argparse.ArgumentParser(description='Formatting for data without labels')
    # parse arguments
    if _args is None:
        __args = parser.parse_args()
    else:
        __args = parser.parse_args(_args)
    # return results
    return __args

if __name__ == '__main__':
    args = parse_args()