# -*- coding: utf-8 -*-


import argparse


class ArgParseFormatter(argparse.ArgumentDefaultsHelpFormatter,
                        argparse.RawDescriptionHelpFormatter):
    """
    Combines argparse formatter with default values output with
    raw description formatter
    """
    pass