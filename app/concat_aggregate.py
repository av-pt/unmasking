import glob
import os
import subprocess
import sys
import time
from collections import defaultdict

import yaml
import argparse

"""
Given a directory of unmasking results, aggregates the curves into one
result for each of the directories in the input
Inputs:
- List of unmasking_curves_YYYY-mm-dd-HH-MM-SS folders
"""


def now(): return time.strftime("%Y-%m-%d_%H-%M-%S")


def main():
    parser = argparse.ArgumentParser(
        prog="concat_aggregate",
        description="Automate aggregation for multiple curve sets",
        add_help=True)
    parser.add_argument('--input',
                        '-i',
                        nargs='+',
                        default=[],
                        help='Two or more paths to directories of '
                             'multiple unmasking results each each')
    args = parser.parse_args()

    if len(args.input) <= 1:
        sys.exit('2 or more input folders needed for aggregation')

    # Transpose inputs
    results = defaultdict(list)
    for unmasking_result_folder_name in args.input:
        directory = [d for d in os.scandir(unmasking_result_folder_name)]
        for dir_entry in directory:
            path_to_json = glob.glob(os.path.join(dir_entry.path,
                                                  'job_*',
                                                  'CurveAverageAggregator.*'))[0]
            results[dir_entry.name].append(path_to_json)

    print(results)

    # Run aggregations
    output_folder = f'unmasking_curves_agg_{now()}/'
    for transcription_system, curve_paths in results.items():
        print(f'Aggregating {transcription_system} with paths: {curve_paths}')
        subprocess.run(['./unmask', 'aggregate', *curve_paths,
                        '-o', os.path.join('data',
                                           output_folder,
                                           transcription_system)])


if __name__ == "__main__":
    main()
