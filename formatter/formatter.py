import numpy
import argparse
import json
import csv


class SyncFormatter:

    MILLISECONDS = 1000.

    def __init__(self, data_file, labels_file, event_types_file=None, tps=512.):
        # ticks per second and conversion
        self.ticks_per_second = tps
        self.conversion = self.MILLISECONDS / tps
        # parse json
        parsed_labels = self.parse_json(labels_file)
        # save data/labels ...?
        self._data_file = data_file
        self._parsed_labels = parsed_labels
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
        # get label times
        self.label_times = self.parse_labels(parsed_labels)

    def parse_csv(self, data_file):
        signals = {}
        with open(data_file, newline='') as csv_file:
            data_reader = csv.reader(csv_file)
            for line in data_reader:
                if len(line) > 0:
                    token, dimensions = self.parse_line(line, self.conversion)
                    if token is not None and dimensions is not None:
                        if token not in signals:
                            signals[token] = []
                        signals[token].append(dimensions)
        return signals

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


    @staticmethod
    def parse_line(line, conversion):
        # TODO: add further checks, like in the original VAT
        token = line[0]
        line[1] = str(conversion * int(line[1]))  # do conversion, if needed
        dimensions = line[1:]
        return token, dimensions

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


def parse_args(_args=None):
    parser = argparse.ArgumentParser(description='Format that data!')
    parser.add_argument('data', help='file containing data')
    parser.add_argument('labels', help='file containing labels')
    parser.add_argument('--event_types', '-e', help='the event_types.json file')
    if _args is None:
        return parser.parse_args()
    return parser.parse_args(_args)


if __name__ == '__main__':
    args = parse_args()
    formatter = SyncFormatter(args.data, args.labels, args.event_types)
    print("offset:", formatter.offset)
    print("event-name-map", formatter.event_names)
    print("label times", formatter.label_times)
