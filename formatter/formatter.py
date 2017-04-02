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

    # def format_simple(self):
    #     # can only use this format type if all signals are of equal length
    #     if all([len(x) == len(y) for x in self.data for y in self.data]):
    #         print("cannot use this format if signals are not of the same length")
    #         return None
    #     feature_names = self.get_feature_names(self._sensors)


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
    parser.add_argument('data', help='file containing data')
    parser.add_argument('labels', help='file containing labels')
    parser.add_argument('--event_types', '-e', help='the event_types.json file')
    parser.add_argument('--ticks_per_second', '-tps', type=int, default=512,
                        help='the number of ticks per second the data file uses')
    if _args is None:
        parsed_args = parser.parse_args()
    parsed_args = parser.parse_args(_args)
    return parsed_args


if __name__ == '__main__':
    args = parse_args()
    formatter = SyncFormatter(args.data, args.labels, args.event_types, tps=args.ticks_per_second)
    print("offset:", formatter.offset)
    print("event-name-map", formatter.event_names)
    print("label times", formatter.label_times)
