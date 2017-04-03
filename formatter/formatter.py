import numpy as np
import argparse
import json
import csv


class SyncFormatter:

    MILLISECONDS = 1000.

    def __init__(self, data_file, labels_file, event_types_file=None, tps=512., sensors=('A', 'G'),
                 format_type="simple"):
        # ticks per second and conversion
        self.ticks_per_second = tps
        self.conversion = self.MILLISECONDS / tps
        # parse json
        parsed_labels = self.parse_json(labels_file)
        # save data/labels ...?
        self._data_file = data_file
        self._parsed_labels = parsed_labels
        self._sensors = sensors
        # get event-name-map
        if event_types_file:
            parsed_event_types = self.parse_json(event_types_file)
            self.event_names = self.label_name_map(parsed_event_types)
        else:
            self.event_names = self.label_name_map(parsed_labels)
        # get offset
        data_flash = int(self.red_flash__data(data_file) * self.conversion)
        label_flash = int(self.red_flash__labels(parsed_labels) * self.MILLISECONDS)
        self.offset = label_flash - data_flash
        # parse labels
        self.label_times = np.array(self.parse_labels(parsed_labels))
        # parse data
        self.data = self.parse_csv(data_file, sensors)

    def parse_csv(self, data_file, sensors):
        signals = {}
        for sensor in sensors:
            signals[sensor] = []
        with open(data_file, newline='') as csv_file:
            data_reader = csv.reader(csv_file)
            for line in data_reader:
                if len(line) > 0:
                    if line[0] in signals and len(line) == 5:
                        token = line[0]
                        dimensions = [int(i) for i in line[1:]]
                        dimensions[0] = int(dimensions[0] * self.conversion)
                        signals[token].append(dimensions)
        return [np.array(signals[dim]) for dim in sensors]

    def parse_labels(self, parsed_labels):
        lbl_times = []
        for label in parsed_labels:
            if label['name'] != 'First Red Flash':
                start = int(label['time'] * self.MILLISECONDS) - self.offset
                if 'subEventTypes' in label:
                    for i, sub_event in enumerate(label['subEventSplits']):
                        end = int(sub_event * self.MILLISECONDS) - self.offset
                        name = label['name'] + '--' + label['subEventTypes'][i]
                        lbl_times.append([start, end, self.event_names[name]])
                        start = end
                    name = label['name'] + '--' + label['subEventTypes'][len(label['subEventSplits'])]
                else:
                    name = label['name']
                end = int(label['endTime'] * self.MILLISECONDS) - self.offset
                lbl_times.append([start, end, self.event_names[name]])
        return lbl_times

    def format_simple(self):
        # can only use this format type if all signals are of equal length
        if not all([len(x) == len(y) for x in self.data for y in self.data]):
            print("cannot use this format if signals are not of the same length")
            return None
        feature_names = self.get_feature_names(self._sensors)
        # create matrix
        result = np.zeros((self.num_examples, self.num_features+1))
        # add x,y,z for each signal
        for i in range(len(self.data)):
            j = i * 3
            result[:, j:j+3] = self.data[i][:, 1:]
        # figure out labels
        Δt = self.data[0][:, 0].reshape(self.num_examples, 1)  # ticks (taken from first sensor)
        λ = np.where((Δt >= self.label_times[:, 0]) & (Δt <= self.label_times[:, 1]))  # λ[0] = indices, λ[1] = values
        result[λ[0], -1] = self.label_times[λ[1], 2]  # applies λ's label values as last column
        return result, feature_names

    @property
    def num_features(self):
        return len(self._sensors) * 3

    @property
    def num_examples(self):
        return len(self.data[0])

    @staticmethod
    def red_flash__data(data_file):
        with open(data_file, newline='') as csv_file:
            data_reader = csv.reader(csv_file)
            for line in data_reader:
                if len(line) > 0:
                    if line[0] == "D" and line[1] == 'Time:0ms':
                        return 0
                    if line[0] == "S" and line[2] == 'LED Sync':
                        return int(line[1])

    @staticmethod
    def red_flash__labels(parsed_labels):
        for label in parsed_labels:
            if label['name'] == 'First Red Flash':
                return float(label['time'])

    @staticmethod
    def parse_json(labels_file):
        with open(labels_file) as json_file:
            parsed_labels = json.loads(json_file.read())
        return parsed_labels

    @staticmethod
    def label_name_map(parsed_labels):
        result = {}
        n = 1
        for label in parsed_labels:
            if label['name'] != 'First Red Flash':
                if 'subEventTypes' in label:
                    for sub_event in label['subEventTypes']:
                        name = label['name'] + '--' + sub_event
                        if name not in result:
                            result[name] = n
                            n += 1
                else:
                    name = label['name']
                    if name not in result:
                            result[name] = n
                            n += 1
        return result

    @staticmethod
    def get_feature_names(sensors):
        feature_names = []
        for dim in sensors:
            feature_names.append(dim + ".x")
            feature_names.append(dim + ".y")
            feature_names.append(dim + ".z")
        return feature_names


def parse_args(_args=None):
    parser = argparse.ArgumentParser(description='Format that data!')
    parser.add_argument('--data', '-d', help='file containing data')
    parser.add_argument('--labels', '-l', help='file containing labels')
    parser.add_argument('--output', '-out', help='the output file to save to')
    parser.add_argument('--normalize_range', '-N', nargs='*', default='false',
                        help='If flag, normalizes the data with automatic range finding.'
                             'If values specified, denotes the max-value to normalize by for each sensor.')
    parser.add_argument('--event_types', '-E', help='the event_types.json file')
    parser.add_argument('--folder', '-F', help='the folder containing the data/labels files')
    parser.add_argument('-e', action='store_true',
                        help='if folder is specified, '
                             'this flag signifies that there is an event_types.json file in the folder')
    parser.add_argument('-o', action='store_true',
                        help='if folder is specified, this flag sets to save output to the same folder')
    parser.add_argument('--ticks_per_second', '-tps', type=int, default=512,
                        help='the number of ticks per second the data file uses')
    if _args is None:
        __args = parser.parse_args()
    else:
        __args = parser.parse_args(_args)
    if __args.folder:
        __args.data = __args.folder + "/data.csv"
        __args.labels = __args.folder + "/labels.json"
        if __args.e:
            __args.event_types = __args.folder + "/event_types.json"
        if __args.o:
            __args.output = __args.folder + "/output.csv"
    return __args


if __name__ == '__main__':
    args = parse_args()
    print('Normalization:', args.normalize_range)
    formatter = SyncFormatter(args.data, args.labels, args.event_types, tps=args.ticks_per_second)
    r, f = formatter.format_simple()
    f.append('label')
    header = ', '.join(f)
    np.savetxt(args.output, r, delimiter=',', fmt='%6i', header=header)
    print(r)
