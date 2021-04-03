from g2p_en import G2p
from pyphonetics import Soundex, FuzzySoundex, RefinedSoundex, Metaphone, MatchingRatingApproach, Lein
from nltk import word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer
from pyclts import CLTS
import spacy

clts = CLTS('authorship_unmasking/ext_modules/clts/')

g2p_en = G2p()

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
fuzzy_soundex = FuzzySoundex()
refined_soundex = RefinedSoundex()
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
    transcription_system in {"ipa", "soundex", "fuzzy_soundex", "refined_soundex", "metaphone", "mra", "lein"}
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
    elif transcription_system == 'fuzzy_soundex':
        return g2p_pyphonetics(verbatim, fuzzy_soundex)
    elif transcription_system == 'refined_soundex':
        return g2p_pyphonetics(verbatim, refined_soundex)
    elif transcription_system == 'metaphone':
        return g2p_pyphonetics(verbatim, metaphone)
    elif transcription_system == 'mra':
        return g2p_pyphonetics(verbatim, matching_rating_approach)
    elif transcription_system == 'lein':
        return g2p_pyphonetics(verbatim, lein)

def g2sc(verbatim, sound_class_system='dolgo'):
    """
    Takes a verbatim string and replaces each symbol to
    its corresponding sound class declared in sound_class_system.
    Flow: verbatim -> ipa -> sound class
    Keeps punctuation where applicable.
    sound_class_system in {'art', 'asjp', 'color', 'cv', 'dolgo', 'sca'}
    """
    dest_sound_class = clts.soundclass(sound_class_system)
    char_tokens = g2p_en(verbatim)
    # Arpabet to IPA and tag s = symbol, p = punctuation
    char_ipa = [(arpabet2ipa_no_stress[symbol], 's') if symbol in arpabet2ipa_no_stress.keys() else (symbol, 'p') for symbol in char_tokens]
    char_sound_class = ''.join([clts.bipa.translate(symbol, dest_sound_class) if tag == 's' else symbol for symbol, tag in char_ipa])
    return char_sound_class

def lemmatize(verbatim, system):
    """
    Takes a verbatim string, removes punctuation, lemmatizes words, removes stopwords.
    Returns space separated tokens.
    """
    doc = nlp(verbatim)
    if system == 'lemma':
        return ' '.join([token.lemma_ for token in doc])
    elif system == 'lemma_punct':
        return ' '.join([token.lemma_ for token in doc if not token.is_punct])
    elif system == 'lemma_punct_stop':
        return ' '.join([token.lemma_ for token in doc if (not token.is_stop and not token.is_punct and not token.like_num)])

def transcribe(verbatim, system):
    if system in {'art', 'asjp', 'color', 'cv', 'dolgo', 'sca'}:
        return g2sc(verbatim, system)
    elif system in {'ipa', 'soundex', 'fuzzy_soundex', 'refined_soundex', 'metaphone', 'mra', 'lein'}:
        return g2p(verbatim, system)
    elif system in {'lemma', 'lemma_punct', 'lemma_punct_stop'}:
        return lemmatize(verbatim, system)
    elif system.startswith('l_'):
        return transcribe(lemmatize(verbatim, 'lemma'), system.split('_')[1])
    elif system.startswith('lp_'):
        return transcribe(lemmatize(verbatim, 'lemma_punct'), system.split('_')[1])
    elif system.startswith('lps_'):
        return transcribe(lemmatize(verbatim, 'lemma_punct_stop'), system.split('_')[1])
    else:
        raise Exception('\'' + system + '\' is not a valid transcription system!')