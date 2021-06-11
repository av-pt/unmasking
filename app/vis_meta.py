import json, os
from glob import glob
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Transcription systems ordered in descending alphabet size
# -> Not the same as vocab size. Make analysis for how much the vocab is
# normalized / lossy-compressed for each transcription!
transcriptions = [
    'original', # 26 + punctuation (is pct thrown out?)
    'ipa',      # 107 segm. letters + 44 diacritics
    'asjp',     # 41
    'refsoundex', # TODO: refined_soundex is not a valid transcription system
    'soundex',  # 26 (alphabet) + 9 (1..9)
    'dolgo',    # >10, <35
    'cv'        # 2
]

# Import data
path = 'out_meta'
data_folders = [f.name for f in os.scandir(path) if f.is_dir()]
print(data_folders)

data = {}
for folder in data_folders:
    path_to_json = glob(os.path.join(path, 
                                          folder,
                                          'job_*',
                                          'UnmaskingResult.*'))[0]
    with open(path_to_json) as f:
        data[folder] = json.load(f)

# Extract metrics, very hacky
metrics = list(data['dolgo']['meta']['results'].keys())

# Plot each metric
for metric in metrics:
    lps = []
    lp = []
    l = []
    no = []

    for t in transcriptions:
        lps.append(data[f'lps_{t}']['meta']['results'][metric]['mean'])
        lp.append(data[f'lp_{t}']['meta']['results'][metric]['mean'])
        l.append(data[f'l_{t}']['meta']['results'][metric]['mean'])
        no.append(data[t]['meta']['results'][metric]['mean'])
    #print(no)
    df=pd.DataFrame({'x_values': transcriptions, 
                    'lps':lps, 
                    'lp': lp, 
                    'l': l ,
                    'verbatim': no
                    })
    
    #fig, ax = plt.subplots()
    #print(df.drop('x_values'))
    #print(df[1:].idxmax(axis=0)[0])
    #print(df[1:].max(axis=0)[0])
    #ax.annotate('local max', xy=())
    # multiple line plots
    plt.plot( 'x_values', 'lps', data=df, marker='o', linewidth=1)
    plt.plot( 'x_values', 'lp', data=df, marker='o', linewidth=1)
    plt.plot( 'x_values', 'l', data=df, marker='o', linewidth=1)
    plt.plot( 'x_values', 'verbatim', data=df, marker='o', linewidth=1)
    #plt.plot( 'x_values', 'y3_values', data=df, marker='', color='olive', linewidth=2, linestyle='dashed', label="toto")

    plt.ylim(0,1)
    # show legend
    plt.title(f'Cross-Validation, {metric[:-4]} for k = {5}')
    plt.legend()
    plt.grid()
    #plt.show()
    plt.savefig(os.path.join('out_vis', f'crossval_{metric[:-4]}.png'))
    plt.clf()
