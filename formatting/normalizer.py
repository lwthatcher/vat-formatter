"""Module for normalizing sensor data, to make it easier to learn"""
import numpy as np


class Normalizer:

    def __init__(self):
        pass

    @staticmethod
    def max_per_sensor(data):
        # for now assume first 3 cols are A, second 3 are G
        cols = [3, 6]
        i = 0
        result = []
        for j in cols:
            result.append(np.max(abs(data[:, i:j])))
            i = j
        return result

    @staticmethod
    def mean_per_sensor(data):
        # for now assume first 3 cols are A, second 3 are G
        cols = [3, 6]
        i = 0
        result = []
        for j in cols:
            result.append(np.mean(abs(data[:, i:j])))
            i = j
        return result

    @staticmethod
    def normalize_per_sensor(data, norms):
        # for now assume first 3 cols are A, second 3 are G
        cols = [3, 6]
        i = 0
        for idx, j in enumerate(cols):
            data[:, i:j] = data[:, i:j] / norms[idx]
        return data

if __name__ == '__main__':
    print('not much to do here!')
