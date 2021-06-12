import glob
import os
import subprocess
import time
import argparse

"""
Given a directory of unmasking curve results
(e.g. "unmasking_curves_2021-06-12_13-23-07") runs
`classify.py crossval` on all of them.
TODO: Add k for specifying nr of folds
"""


def now(): return time.strftime("%Y-%m-%d_%H-%M-%S")


def main():
    parser = argparse.ArgumentParser(
        prog="concat_crossval",
        description="Automate cross-validation for multiple sets of unmasking curves",
        add_help=True)
    parser.add_argument('--input',
                        '-i',
                        help='Path to directory of unmasking results (containing'
                             ' one directory for each unmasked dataset)')
    args = parser.parse_args()

    directory = [d for d in os.scandir(args.input)]
    print(f'Found {len(directory)} unmasking results.')
    output_folder = f'crossval_results_{now()}/'

    for i, dir_entry in enumerate(directory):
        print(f'Cross-validating {dir_entry.name}... ({i + 1}/{len(directory)})')

        # Assuming there's only one job_DDDDD... file
        # Get file: out/folder/job_*/CurveAverageAggregator.*
        path_to_json = glob.glob(os.path.join(dir_entry.path,
                                              'job_*',
                                              'CurveAverageAggregator.*'))[0]

        subprocess.run(['./classify', 'crossval', path_to_json,
                        '-c', 'app/job_meta.yml',
                        '-o', os.path.join('..',
                                           'data',
                                           output_folder,
                                           dir_entry.name)])


if __name__ == "__main__":
    main()
