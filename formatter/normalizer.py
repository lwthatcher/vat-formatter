"""Module for normalizing sensor data, to make it easier to learn"""
import numpy as np


class Normalizer:

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


if __name__ == '__main__':
    pass
