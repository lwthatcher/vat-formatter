import numpy
import argparse


def parse_args(_args=None):
    parser = argparse.ArgumentParser(description='Format that data!')
    if _args is None:
        return parser.parse_args()
    return parser.parse_args(_args)

if __name__ == '__main__':
    args = parse_args()
    print(args)
