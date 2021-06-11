import yaml, subprocess, os
from tqdm import tqdm

#CLI
#take job.yml with <output_dir> and <transcription> placeholders

all_transcription_systems = [
    #'original', 
    'art', 
    'asjp', 
    'color', 
    'cv', 
    'dolgo', 
    'sca', 
    'ipa', 
    'soundex', 
    'fuzsoundex', 
    'refsoundex', 
    'metaphone', 
    'mra', 
    'lein', 
    'lemma', 
    'lemma_punct', 
    'lemma_punct_stop', 
    'l_art', 
    'l_asjp', 
    'l_color', 
    'l_cv', 
    'l_dolgo', 
    'l_sca', 
    'l_ipa', 
    'l_soundex', 
    'l_fuzsoundex', 
    'l_refsoundex', 
    'l_metaphone', 
    'l_mra', 
    'l_lein', 
    'lp_art', 
    'lp_asjp', 
    'lp_color', 
    'lp_cv', 
    'lp_dolgo', 
    'lp_sca', 
    'lp_ipa', 
    'lp_soundex', 
    'lp_fuzsoundex', 
    'lp_refsoundex', 
    'lp_metaphone', 
    'lp_mra', 
    'lp_lein', 
    'lps_art', 
    'lps_asjp', 
    'lps_color', 
    'lps_cv', 
    'lps_dolgo', 
    'lps_sca', 
    'lps_ipa', 
    'lps_soundex', 
    'lps_fuzsoundex', 
    'lps_refsoundex', 
    'lps_metaphone', 
    'lps_mra', 
    'lps_lein'
]

used_transcription_systems = [
    'original', 
    'asjp', 
    'cv', 
    'dolgo', 
    'ipa', 
    'soundex', 
    'refsoundex', 
    'lemma', 
    'lemma_punct', 
    'lemma_punct_stop', 
    'l_asjp', 
    'l_cv', 
    'l_dolgo', 
    'l_ipa', 
    'l_soundex', 
    'l_refsoundex', 
    'lp_asjp', 
    'lp_cv', 
    'lp_dolgo', 
    'lp_ipa', 
    'lp_soundex', 
    'lp_refsoundex', 
    'lps_asjp', 
    'lps_cv', 
    'lps_dolgo', 
    'lps_ipa', 
    'lps_soundex', 
    'lps_refsoundex', 
]

leftover_transcription_systems = [
    'punct'
]
print('Running unmasking for:', leftover_transcription_systems)
for transcription_system in tqdm(leftover_transcription_systems, desc='Transcriptions'):
    # Load job.yml
    with open('app/orig_job.yml') as f:
        doc = yaml.load(f, Loader=yaml.FullLoader)

    doc['job%']['input']['transcription'] = transcription_system
    doc['job%']['output_dir'] = os.path.join('..', 'out', transcription_system)
    
    with open('app/temp_job.yml', 'w') as f:
        yaml.dump(doc, f)

    subprocess.run(['./unmask', 'run', 'app/temp_job.yml'])

# TODO: Remove temp file
