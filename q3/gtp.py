import json

class GtpConverter:
    def __init__(self, gtp_rules_file):
        with open(gtp_rules_file, 'r', encoding='utf-8') as f:
            self.gtp_rules = json.load(f)
            self.fill_subsets()

    def fill_subsets(self):
        subset_keys = [subset['name'] for subset in self.gtp_rules['subsets']]

        for rule in self.gtp_rules['rules']:
            if rule.get('predecessor') is not None and rule['predecessor'] in subset_keys:
                rule['predecessor'] = self.gtp_rules['subsets'][subset_keys.index(rule['predecessor'])]['graphemes']
            
            if rule.get('successor') is not None and rule['successor'] in subset_keys:
                rule['successor'] = self.gtp_rules['subsets'][subset_keys.index(rule['successor'])]['graphemes']
            

    def parse_word_into_chunks(self, word: str, number_of_chars=1) -> list[str]:
        word = f"${word}$"
        return [{'predecessor': word[i],
                    'center': word[i+1:i+number_of_chars+1],
                    'successor': word[i+number_of_chars+1]} 
                for i in range(len(word)-number_of_chars-1)]

    def get_candidates(self, chunk: dict) -> list[dict]:
        return [rule for rule in self.gtp_rules['rules'] if rule['center'] == chunk['center']]

    def get_phonemes_from_candidates(self, chunk: dict, candidates: list[dict]) -> str:
        for candidate in candidates:
            if candidate.get('predecessor') is not None and chunk['predecessor'] in candidate['predecessor'].split(' '):
                return candidate['phonemes']
            if candidate.get('successor') is not None and chunk['successor'] in candidate['successor'].split(' '):
                return candidate['phonemes']

        default_candidate = [candidate for candidate in candidates if candidate.get('predecessor') is None and candidate.get('successor') is None]
        return default_candidate[0]['phonemes'] if len(default_candidate) > 0 else None

    def process_phonemes(self, single_chunk: dict, double_chunk: dict) -> str:
        is_double_chunk = False
        double_candidates = self.get_candidates(double_chunk)
        single_candidates = self.get_candidates(single_chunk)
        if len(double_candidates) > 0:
            phoneme = self.get_phonemes_from_candidates(double_chunk, double_candidates)
            if phoneme is not None:
                is_double_chunk = True
            else:
                phoneme = self.get_phonemes_from_candidates(single_chunk, single_candidates)
        else:
            phoneme = self.get_phonemes_from_candidates(single_chunk, single_candidates)

        return phoneme, is_double_chunk


    def process(self, word: str) -> str:
        phonemes = []

        single_word_chunks = self.parse_word_into_chunks(word, 1)
        double_word_chunks = self.parse_word_into_chunks(word, 2)
        double_word_chunks.append({'center': '$', 'predecessor': '$', 'successor': '$'})

        is_double_chunk = False

        for (single_chunk, double_chunk) in zip(single_word_chunks, double_word_chunks):
            if is_double_chunk:
                is_double_chunk = False
                continue
            
            if single_chunk['center'] in self.gtp_rules['graphemes'].split(' '):
                phoneme, is_double_chunk = self.process_phonemes(single_chunk, double_chunk)

                if phoneme is not None:
                    phonemes.append(phoneme)
                else:
                    print(f"No phoneme found for chunk {single_chunk}. Word {word} is not a valid word.")
                    return None
            else:
                print(f"Character {single_chunk['center']} not found in graphemes. Word {word} is not a valid word.")
                return None
        
        return ''.join(phonemes)

gtp_converter = GtpConverter('spanish_gtp_rules.json')
#print(gtp_converter.gtp_rules)

list_of_words = [
    "sueño", "pequenita", "desarrollar", "guitarra", "cigüeña", "alburquerque", "atenúas", "zorro",
    "muchacho", "hierro", "mándamelo", "rápidamente", "chiringuitos", "caballeros", "escribí"
]

for word in list_of_words:
    print(f"{word}: {gtp_converter.process(word)}")