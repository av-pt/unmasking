import os, sys, glob, yaml, subprocess

# Goes through unmask out/ folder and calculates crossval results for
# all unmasking results
# TODO: Add k for specifying nr of folds
path = 'out_finished'
out_folders = [f.name for f in os.scandir(path) if f.is_dir()]

# If output already exists, do not calculate crossval again
existing_folders = [f.name for f in os.scandir('out_meta') if f.is_dir()]
out_folders = [f for f in out_folders if f not in existing_folders]

print('Computing crossval for:', out_folders)

for folder in out_folders:

    # Assuming there's only one job_DDDDD... file
    # Get file: out/folder/job_*/CurveAverageAggregator.*
    path_to_json = glob.glob(os.path.join(path, 
                                          folder, 
                                          'job_*', 
                                          'CurveAverageAggregator.*'))[0]

    # Load job.yml
    with open('app/job_meta.yml') as f:
        doc = yaml.load(f, Loader=yaml.FullLoader)

    doc['job']['output_dir'] = os.path.join('..', 'out_meta', folder)
    
    with open('app/temp_job_meta.yml', 'w') as f:
        yaml.dump(doc, f)

    subprocess.run(['./classify', 'crossval', path_to_json, '-c', 'app/temp_job_meta.yml'])