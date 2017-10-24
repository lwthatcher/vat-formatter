import argparse
import csv
import numpy as np

MILLISECONDS = 1000.

def get_conversion(tps):
    return MILLISECONDS / tps

# TODO: remove code duplication
def parse_csv(data_file, sensors=('A', 'G'), tps=512.):
        signals = {}
        # TODO: auto-infer tps rate based on format
        conversion = get_conversion(tps)
        # TODO: auto-infer sensors if not specified
        for sensor in sensors:
            signals[sensor] = []
        with open(data_file, newline='') as csv_file:
            data_reader = csv.reader(csv_file)
            for line in data_reader:
                if len(line) > 0:
                    if line[0] in signals and len(line) == 5:
                        token = line[0]
                        dimensions = [int(i) for i in line[1:]]
                        dimensions[0] = int(dimensions[0] * conversion)
                        signals[token].append(dimensions)
        return [np.array(signals[dim]) for dim in sensors]

class DataPreFormatter:

    def __init__(self, data_file, sensors=('A', 'G'), tps=512.):
        self.data = parse_csv(data_file, sensors, tps)
        print('loaded data')

    @property
    def examples(self):
        return [len(x) for x in self.data]

    @property
    def features(self):
        return [x.shape[1] - 1 for x in self.data]
    
    def convert(self):
        # can only use this format type if all signals are of equal length
        if not all([len(x) == len(y) for x in self.data for y in self.data]):
            print("cannot use this format if signals are not of the same length")
            return None
        # create matrix
        rows = np.max(self.examples)
        cols = np.sum(self.features)
        result = np.zeros((rows, cols))
        # add x,y,z for each signal
        j = 0
        for i, f in enumerate(self.features):
            result[:, j:j+f] = self.data[i][:, 1:]
            j = (i+1) * f
        return result


def parse_args(_args=None):
    parser = argparse.ArgumentParser(description='Formatting for data without labels')
    parser.add_argument('data', help='data file to convert')
    parser.add_argument('--output', '-O', help='the output file to save to')
    # parse arguments
    if _args is None:
        __args = parser.parse_args()
    else:
        __args = parser.parse_args(_args)
    # return results
    return __args


if __name__ == '__main__':
    args = parse_args()
    formatter = DataPreFormatter(args.data)
    result = formatter.convert()
    out = args.output or 'output.npy'
    np.save(out, result)
