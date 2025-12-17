import json

# GTP converter class
class GtpConverter:

    # Fill constants keys in the rules file
    def fill_constants(self):
        self.PREDECESSOR_KEY = 'predecessor'
        self.SUCCESSOR_KEY = 'successor'
        self.PHONEMES_KEY = 'phonemes'
        self.CENTER_KEY = 'center'
        self.RULE_KEY = 'rules'
        self.GRAPHEMES_KEY = 'graphemes'
        self.SUBSETS_KEY = 'subsets'
        self.NAME_KEY = 'name'

    # Initialize the GTP converter
    def __init__(self, gtp_rules_file):
        # Load the rules file
        with open(gtp_rules_file, 'r', encoding='utf-8') as f:
            self.gtp_rules = json.load(f)
            self.fill_constants()
            self.fill_subsets()

    # Fill the subsets keys in the rules file
    def fill_subsets(self):
        subset_keys = [subset[self.NAME_KEY] for subset in self.gtp_rules[self.SUBSETS_KEY]]

        # Iterate over the rules and fill the subsets keys (e.g SV, EI to their corresponding graphemes)
        for rule in self.gtp_rules[self.RULE_KEY]:
            if self.PREDECESSOR_KEY in rule and rule[self.PREDECESSOR_KEY] in subset_keys:
                rule[self.PREDECESSOR_KEY] = self.gtp_rules[self.SUBSETS_KEY][subset_keys.index(rule[self.PREDECESSOR_KEY])][self.GRAPHEMES_KEY]
            
            if self.SUCCESSOR_KEY in rule and rule[self.SUCCESSOR_KEY] in subset_keys:
                rule[self.SUCCESSOR_KEY] = self.gtp_rules[self.SUBSETS_KEY][subset_keys.index(rule[self.SUCCESSOR_KEY])][self.GRAPHEMES_KEY]
            

    # Parse the word into chunks
    # For example, the word "sueño" will be parsed into the following chunks:
    # Single chunks: [{$,s,u}, {s,u,e}, {u,e,ñ}, {e,ñ,o}, {ñ,o,$}]
    # Double chunks: [{$,su,e}, {s,ue,ñ}, {u,eñ,o}, {e,ño,$}]
    def parse_word_into_chunks(self, word: str, number_of_chars=1) -> list[dict]:
        # Add $ to the beginning and end of the word
        word = f"${word}$"

        # Iterate over the word and create the chunks
        return [{self.PREDECESSOR_KEY: word[i-1],
                    self.CENTER_KEY: word[i:i+number_of_chars],
                    self.SUCCESSOR_KEY: word[i+number_of_chars]} 
                for i in range(1, len(word)-number_of_chars)]

    # Get the candidates for a given chunk (Where there is a match for the center key)
    def get_candidates(self, chunk: dict) -> list[dict]:
        return [rule for rule in self.gtp_rules[self.RULE_KEY] if rule[self.CENTER_KEY] == chunk[self.CENTER_KEY]]

    # Get the phoneme from the candidates
    def get_phonemes_from_candidates(self, chunk: dict, candidates: list[dict]) -> str:
        default_candidate = None
        
        # Iterate over the candidates and get the phoneme
        for candidate in candidates:

            # If there is a match for the predecessor key, return the phoneme of this candidate
            if self.PREDECESSOR_KEY in candidate and chunk[self.PREDECESSOR_KEY] in candidate[self.PREDECESSOR_KEY].split(' '):
                return candidate[self.PHONEMES_KEY]

            # If there is a match for the successor key, return the phoneme of this candidate
            if self.SUCCESSOR_KEY in candidate and chunk[self.SUCCESSOR_KEY] in candidate[self.SUCCESSOR_KEY].split(' '):
                return candidate[self.PHONEMES_KEY]

            # If there is no match for the predecessor or successor key, 
            # set the default candidate to the current candidate (the one with no predecessor nor successor)
            if self.PREDECESSOR_KEY not in candidate and self.SUCCESSOR_KEY not in candidate:
                default_candidate = candidate

        # Return the phoneme of the default candidate if it exists, otherwise return None
        return default_candidate[self.PHONEMES_KEY] if default_candidate is not None else None

    # Process the phonemes for a given single and double chunk
    def process_phonemes(self, single_chunk: dict, double_chunk: dict) -> tuple[str, bool]:

        # Get the candidates for the double chunk (A matching by 'center' key)
        double_candidates = self.get_candidates(double_chunk)

        # Get the candidates for the single chunk (A matching by 'center' key)
        single_candidates = self.get_candidates(single_chunk)

        # If there are double candidates, process the double chunk, otherwise process the single chunk
        if len(double_candidates) > 0:

            # Get the phoneme from the double candidates
            phoneme = self.get_phonemes_from_candidates(double_chunk, double_candidates)
            
            # If the phoneme of the double chunk is found, return the phoneme and the double chunk indicator to True
            # Otherwise, proceed with the single candidates to get the phoneme of the single chunk
            if phoneme is not None:
                return phoneme, True
            else:
                phoneme = self.get_phonemes_from_candidates(single_chunk, single_candidates)
        else:
            phoneme = self.get_phonemes_from_candidates(single_chunk, single_candidates)

        # Return the phoneme of the single chunk and the double chunk indicator to False
        return phoneme, False


    # Process the word into phonemes
    def process(self, word: str) -> str:
        # Initialize the phonemes list (list of characters of the phonemes of the word)
        phonemes = []

        # Parse the word into single and double chunks
        single_word_chunks = self.parse_word_into_chunks(word, 1)
        double_word_chunks = self.parse_word_into_chunks(word, 2)

        # Add the end of word chunk to the double chunks in order to make the two chunks lists the same length for the zip function.
        double_word_chunks.append({self.CENTER_KEY: '$', self.PREDECESSOR_KEY: '$', self.SUCCESSOR_KEY: '$'})

        # Initialize the is_double_chunk flag to False (No double chuck matching detected yet)
        is_double_chunk = False

        # Iterate over the single and double chunks and process the phonemes
        for (single_chunk, double_chunk) in zip(single_word_chunks, double_word_chunks):
            
            # If the is_double_chunk flag is True (A double chunk has been matched in the previous iteration), skip the current iteration and reset the flag to False
            if is_double_chunk:
                is_double_chunk = False
                continue

            # If the single chunk is a valid grapheme, process the phonemes, otherwise print an error message and return None
            if single_chunk[self.CENTER_KEY] in self.gtp_rules[self.GRAPHEMES_KEY].split(' '):

                # Get the phonemes from the single and double chunks
                phoneme, is_double_chunk = self.process_phonemes(single_chunk, double_chunk)

                # If the phonemes are found, add them to the phonemes list, otherwise print an error message and return None
                if phoneme is not None:
                    phonemes.append(phoneme)
                else:
                    print(f"No phoneme found for chunk {single_chunk}. Word {word} is not a valid word.")
                    return None
            else:
                print(f"Character {single_chunk['center']} not found in graphemes. Word {word} is not a valid word.")
                return None
        
        # Return the phonemes as a string
        return ''.join(phonemes)

gtp_converter = GtpConverter('spanish_gtp_rules.json')

list_of_words = [
    "sueño", "pequenita", "desarrollar", "guitarra", "cigüeña", "alburquerque", "atenúas", "zorro",
    "muchacho", "hierro", "mándamelo", "rápidamente", "chiringuitos", "caballeros", "escribí"
]

for word in list_of_words:
    print(f"{word}: {gtp_converter.process(word)}")

print("--------------------------------")

additional_words = [
    "barranquilla", "mantequilla", "medellín", "colombia","playa",
    "ciudad", "méxico", "calle", "juntos", "sevilla", "muñeca", "año", "javier",
    "juan", "mientras", "quiero", "querías", "coqueto", "trabajar", "hombre"
]

for word in additional_words:
    print(f"{word}: {gtp_converter.process(word)}")