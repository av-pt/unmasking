from g2p_en import G2p
from pyphonetics import Soundex, FuzzySoundex, RefinedSoundex, Metaphone, MatchingRatingApproach, Lein
from nltk import word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer
from pyclts import CLTS
import spacy
import ujson, os, atexit

def dump_with_message(msg, cache_loaded, cache_changed, obj, file_path, **kwargs):
    if cache_loaded and cache_changed:
        print(msg)
        with open(file_path, 'w') as fp:
            ujson.dump(obj, fp, **kwargs)

def persistent_cache(func):
    """
    Persistent cache decorator.
    Creates a "cache/" directory if it does not exist and writes the
    caches of the given func to the file "cache/<func-name>.cache" once
    on exit.
    """
    file_path = os.path.join('cache', f'{func.__name__}.cache')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        print(f'Loading {file_path}')
        with open(file_path, 'r') as fp:
            cache = ujson.load(fp)
    except (IOError, ValueError):
        cache = {}
    atexit.register(lambda: dump_with_message(f'Writing {file_path}',
                                               True,
                                               True,
                                               cache,
                                               file_path,
                                               indent=4))
    def wrapper(*args):
        if str(args) not in cache:
            #print('Keys in cache:', [x[:20] for x in cache.keys()])
            #print('Current key:', str(args)[:20])
            cache[str(args)] = func(*args)
        return cache[str(args)]
    return wrapper

clts = CLTS('authorship_unmasking/ext_modules/clts/')

inner_g2p_en = G2p()

@persistent_cache
def g2p_en(verbatim):
    return inner_g2p_en(verbatim)

nlp = spacy.load('en_core_web_sm')

# Arpabet to IPA dict with stress
arpanet2ipa_orig = {'AA': 'ɑ', 'AE': 'æ', 'AH': 'ʌ', 'AO': 'ɔ', 'AW': 'aʊ', 'AX': 'ə', 'AXR': 'ɚ', 'AY': 'aɪ', 'EH': 'ɛ', 'ER': 'ɝ', 'EY': 'eɪ', 'IH': 'ɪ', 'IX': 'ɨ', 'IY': 'i', 'OW': 'oʊ', 'OY': 'ɔɪ', 'UH': 'ʊ', 'UW': 'u', 'UX': 'ʉ', 'B': 'b', 'CH': 'tʃ', 'D': 'd', 'DH': 'ð', 'DX': 'ɾ', 'EL': 'l̩', 'EM': 'm̩', 'EN': 'n̩', 'F': 'f', 'G': 'ɡ', 'HH': 'h', 'H': 'h', 'JH': 'dʒ', 'K': 'k', 'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ŋ', 'NX': 'ɾ̃', 'P': 'p', 'Q': 'ʔ', 'R': 'ɹ', 'S': 's', 'SH': 'ʃ', 'T': 't', 'TH': 'θ', 'V': 'v', 'W': 'w', 'WH': 'ʍ', 'Y': 'j', 'Z': 'z', 'ZH': 'ʒ'}
primary_stress = {key + '1': 'ˈ' + value for key, value in arpanet2ipa_orig.items()}
secondary_stress = {key + '0': 'ˌ' + value for key, value in arpanet2ipa_orig.items()}
arpabet2ipa = {**arpanet2ipa_orig, **primary_stress, **secondary_stress}

# Arpabet to IPA dict without stress
no_primary_stress = {key + '1': value for key, value in arpanet2ipa_orig.items()}
no_secondary_stress = {key + '0': value for key, value in arpanet2ipa_orig.items()}
no_tertiary_stress = {key + '2': value for key, value in arpanet2ipa_orig.items()}
arpabet2ipa_no_stress = {**arpanet2ipa_orig, **no_primary_stress, **no_secondary_stress, **no_tertiary_stress}


soundex = Soundex()
fuzsoundex = FuzzySoundex()
refsoundex = RefinedSoundex()
metaphone = Metaphone()
matching_rating_approach = MatchingRatingApproach()
lein = Lein()

detokenizer = TreebankWordDetokenizer()

def g2p_pyphonetics(verbatim, transcription_model):
    transcribed_tokens = []
    tokens = word_tokenize(verbatim)
    for token in tokens:
        if token.upper().isupper():
            transcribed_tokens.append(transcription_model.phonetics(token))
        else:
            transcribed_tokens.append(token)
    transcription = detokenizer.detokenize(transcribed_tokens)
    return transcription

def g2p(verbatim, transcription_system="ipa"):
    """
    Takes a verbatim string and returns its transcription to the
    system declared in transcription_system.
    Keeps punctuation where applicable.
    transcription_system in {"ipa", "soundex", "fuzsoundex", "refsoundex", "metaphone", "mra", "lein"}
    """
    if transcription_system == 'ipa':
        transcription = ''
        phonemes = g2p_en(verbatim)
        for symbol in phonemes:
            if symbol in arpabet2ipa_no_stress.keys():
                transcription += arpabet2ipa_no_stress[symbol]
            else:
                transcription += symbol
        return transcription
    elif transcription_system == 'soundex':
        return g2p_pyphonetics(verbatim, soundex)
    elif transcription_system == 'fuzsoundex':
        return g2p_pyphonetics(verbatim, fuzsoundex)
    elif transcription_system == 'refsoundex':
        return g2p_pyphonetics(verbatim, refsoundex)
    elif transcription_system == 'metaphone':
        return g2p_pyphonetics(verbatim, metaphone)
    elif transcription_system == 'mra':
        return g2p_pyphonetics(verbatim, matching_rating_approach)
    elif transcription_system == 'lein':
        return g2p_pyphonetics(verbatim, lein)

# Init sound classes
sc = {
    'art': clts.soundclass('art'), 
    'asjp': clts.soundclass('asjp'), 
    'color': clts.soundclass('color'), 
    'cv': clts.soundclass('cv'), 
    'dolgo': clts.soundclass('dolgo'), 
    'sca': clts.soundclass('sca')
}

@persistent_cache
def clts_translate(symbol, sound_class_system):
    return clts.bipa.translate(symbol, sc[sound_class_system])

def g2sc(verbatim, sound_class_system='dolgo'):
    """
    Takes a verbatim string and replaces each symbol to
    its corresponding sound class declared in sound_class_system.
    Flow: verbatim -> ipa -> sound class
    Keeps punctuation where applicable.
    sound_class_system in {'art', 'asjp', 'color', 'cv', 'dolgo', 'sca'}
    """
    char_tokens = g2p_en(verbatim)
    # Arpabet to IPA and tag s = symbol, p = punctuation
    char_ipa = [(arpabet2ipa_no_stress[symbol], 's') if symbol in arpabet2ipa_no_stress.keys() else (symbol, 'p') for symbol in char_tokens]
    char_sound_class = ''.join([clts_translate(symbol, sound_class_system) if tag == 's' else symbol for symbol, tag in char_ipa])
    return char_sound_class

def lemmatize(verbatim, system):
    """
    Takes a verbatim string, removes punctuation, lemmatizes words, removes stopwords.
    Returns space separated tokens.
    """
    doc = nlp(verbatim)
    if system == 'lemma':
        return ' '.join([token.lemma_ for token in doc])
    elif system == 'punct':
        return ' '.join([token.text.lower() 
                                for token in doc 
                                if (not token.is_punct and not token.like_num)])
    elif system == 'lemma_punct':
        return ' '.join([token.lemma_ for token in doc if not token.is_punct])
    elif system == 'lemma_punct_stop':
        return ' '.join([token.lemma_ for token in doc if (not token.is_stop and not token.is_punct and not token.like_num)])

def transcribe(verbatim, system):
    if system in {'art', 'asjp', 'color', 'cv', 'dolgo', 'sca'}:
        return g2sc(verbatim, system)
    elif system in {'ipa', 'soundex', 'fuzsoundex', 'refsoundex', 'metaphone', 'mra', 'lein'}:
        return g2p(verbatim, system)
    elif system in {'lemma', 'lemma_punct', 'lemma_punct_stop', 'punct'}:
        return lemmatize(verbatim, system)
    elif system.startswith('p_'):
        return transcribe(lemmatize(verbatim, 'punct'), system.split('_')[1])
    elif system.startswith('l_'):
        return transcribe(lemmatize(verbatim, 'lemma'), system.split('_')[1])
    elif system.startswith('lp_'):
        return transcribe(lemmatize(verbatim, 'lemma_punct'), system.split('_')[1])
    elif system.startswith('lps_'):
        return transcribe(lemmatize(verbatim, 'lemma_punct_stop'), system.split('_')[1])
    else:
        raise Exception('\'' + system + '\' is not a valid transcription system!')