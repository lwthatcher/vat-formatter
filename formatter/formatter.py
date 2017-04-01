import numpy
import argparse
import json
import csv


class SyncFormatter:

    MILLISECONDS = 1000.

    def __init__(self, data_file, labels_file, tps=512.):
        self.ticks_per_second = tps
        self.conversion = self.MILLISECONDS / tps
        self.data_file = data_file
        self.labels_file = labels_file
        data_flash = int(self.red_flash__data(data_file) * self.conversion)
        label_flash = int(self.red_flash__labels(labels_file) * self.MILLISECONDS)
        self.offset = label_flash - data_flash

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
    def red_flash__labels(labels_file):
        with open(labels_file) as json_file:
            parsed_labels = json.loads(json_file.read())
        for label in parsed_labels:
            if label['name'] == 'First Red Flash':
                return float(label['time'])


def parse_args(_args=None):
    parser = argparse.ArgumentParser(description='Format that data!')
    parser.add_argument('data', help='file containing data')
    parser.add_argument('labels', help='file containing labels')
    if _args is None:
        return parser.parse_args()
    return parser.parse_args(_args)


if __name__ == '__main__':
    args = parse_args()
    formatter = SyncFormatter(args.data, args.labels)
    print("offset:", formatter.offset)
