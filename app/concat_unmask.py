import os
import subprocess
import time
import yaml
import argparse

"""
Given a directory of PAN20 formatted datasets, runs `unmask.py run` on
all of them.
Inputs:
- job.yml with <output_dir> and <transcription> placeholders
- path to directory with PAN20 formatted datasets
"""


def now(): return time.strftime("%Y-%m-%d_%H-%M-%S")


def main():
    parser = argparse.ArgumentParser(
        prog="concat_unmask",
        description="Automate unmasking for multiple datasets",
        add_help=True)
    parser.add_argument('--input',
                        '-i',
                        help='Path to directory of PAN20 formatted datasets')
    args = parser.parse_args()

    directory = [d for d in os.scandir(args.input)]
    print(f'Found {len(directory)} PAN20 data files.')
    output_folder = f'unmasking_curves_{now()}/'

    for i, dir_entry in enumerate(directory):
        print(f'Unmasking {dir_entry.name}... ({i+1}/{len(directory)})')
        # Workaround, as there is no --input option for `unmask.py run`
        with open(os.path.join('app', 'job.yml')) as f:
            doc = yaml.load(f, Loader=yaml.FullLoader)

        doc['job%']['input']['parser']['parameters']['corpus_path'] = dir_entry.path

        with open(os.path.join('app', 'temp_job.yml'), 'w') as f:
            yaml.dump(doc, f)

        # Trigger Unmasking
        subprocess.run(['./unmask', 'run',
                        '-o', os.path.join('..',
                                           'data',
                                           output_folder,
                                           dir_entry.name),
                        os.path.join('app', 'temp_job.yml')])

    os.remove(os.path.join('app', 'temp_job.yml'))


if __name__ == "__main__":
    main()
