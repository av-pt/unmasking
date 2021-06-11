import os, sys, json
from converters import transcribe
import spacy
from tqdm import tqdm
from glob import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

nlp = spacy.load('en_core_web_sm')
transcription_systems = {'art', 'asjp', 'color', 'cv', 'dolgo', 'sca', 'ipa', 
                         'soundex', 'fuzsoundex', 'refsoundex', 'metaphone', 
                         'mra', 'lein'}

def compute_differences():
    corpus_path = os.path.join('in', 'corpus', 'gutenberg_all')
    folders = [f.name for f in os.scandir(corpus_path) if f.is_dir()]
    print(f'Found {len(folders)} folders: [{", ".join(folders[:3])}, ...]')

    texts = []
    for folder in folders:
        with open(os.path.join(corpus_path, folder, 'known01.txt')) as f:
            texts.append(f.read())
        with open(os.path.join(corpus_path, folder, 'unknown.txt')) as f:
            texts.append(f.read())
    verbatim_tokens = []
    for text in tqdm(texts):
        doc = nlp(text)
        verbatim_tokens.extend([token.text.lower() 
                                for token in doc 
                                if (not token.is_punct and not token.like_num)])
    
    verbatim_types = set(verbatim_tokens)
    types = dict()
    print(f'Verbatim tokens: {len(verbatim_tokens)}')
    print(f'Verbatim types: {len(verbatim_types)}')
    types['original'] = len(verbatim_types)
    for system in transcription_systems:
        try:
            transcribed_types = {transcribe(t, system) for t in verbatim_types}
            types[system] = len(transcribed_types)
        except IndexError as ie:
            print(f'IndexError for {system}. Ignoring {system}.')
            continue
        print(f'{system} types: {len(transcribed_types)}')
    print(types)
    with open('scripts/transcribed_types.json', 'w') as f:
        json.dump(types, f)

def vis_by_vocab_size():
    # Needs results of compute_differences() (scripts/transcribed_types.json)
    # Load vocab size information
    with open('scripts/transcribed_types.json') as f:
        vocab_sizes = json.load(f)
    print('X-values:', vocab_sizes)

    # Load available out_meta data for "p_"
    path = 'out_meta'
    data_folders = [f.name for f in os.scandir(path) 
                    if f.is_dir() and f.name.startswith('p_')]
    print('Visualizing Y-values for:', data_folders)
    data = {}
    for folder in data_folders:
        path_to_json = glob(os.path.join(path, 
                                            folder,
                                            'job_*',
                                            'UnmaskingResult.*'))[0]
        with open(path_to_json) as f:
            data[folder] = json.load(f)
    #print(data)
    # Extract metrics, very hacky
    metrics = list(data['p_dolgo']['meta']['results'].keys())

    # Plot each metric
    for metric in metrics:
        y_values = []
        vs = []

        for t in data_folders:  # These are names of transcriptions like p_original
            y_values.append(data[t]['meta']['results'][metric]['mean'])
            vs.append(vocab_sizes[t[2:]])

        #print(p)
        #print(vs)

        
        df=pd.DataFrame({'vocab_size': vs, 
                         'y_values': y_values,
                         'labels': [f'{name[2:]}  ' for name in data_folders]
                         })
        #print(df)
        #fig, ax = plt.subplots()
        ax = df.plot('vocab_size', 'y_values', kind='scatter')
        df[['vocab_size','y_values','labels']].apply(lambda x: ax.text(*x, rotation='vertical', va='top', ha='center'),axis=1)

        #coef = np.polyfit(vs,y_values,1)
        #poly1d_fn = np.poly1d(coef) 
        # poly1d_fn is now a function which takes in x and returns an estimate for y

        #plt.plot(vs,y, 'yo', vs, poly1d_fn(x), '--k')


        m, b = np.polyfit(vs, y_values, 1)

        ax.plot(vs, np.add(np.multiply(m, vs), b), "--k", linewidth=1)
        #for k, v in df.iterrows():
            #print(k,v)
            #ax.annotate(k, v.labels)
        #print(df)
        #plt.scatter('vocab_size', 'y_values', data=df, marker='o')
        #plt.plot( 'x_values', 'verbatim', data=df, marker='o', linewidth=1)
        ##plt.plot( 'x_values', 'y3_values', data=df, marker='', color='olive', linewidth=2, linestyle='dashed', label="toto")
        plt.xlabel('vocabulary size')
        plt.ylabel(metric[:-4])
        
        plt.xlim(0,50000)
        plt.ylim(0,1)

        ## show legend
        plt.title(f'{metric[:-4]} vs. vocabulary size (cross-val. with k = {5})')
        #plt.legend()
        plt.grid()
        ##plt.show()
        plt.savefig(os.path.join('scripts/out_vis', f'crossval_{metric[:-4]}.png'))
        plt.clf()



# TODO:
# implement p_ in transcribe() to remove punct and numericals
# unmask for all p_ systems
# Plot: x-axis=len(types/vocab) y-axis=score
# Look for other non-phonetic transformations that reduce the number of types
# -> If they're all on one line, the reduction impact might be higher than the phonetic information impact

if __name__ == '__main__':
    #compute_differences()
    vis_by_vocab_size()