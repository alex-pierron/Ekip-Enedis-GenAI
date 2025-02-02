import re
import unicodedata
import pandas as pd

def normalize_text(text, keep_alphanum=False):
    if pd.notna(text):
        # convert text to lowercase and remove accents
        text = str(text).lower().strip()
        normalized_text = ''.join(
            c for c in unicodedata.normalize('NFD', text) 
            if unicodedata.category(c) != 'Mn'
        )
        # remove non-alphanumeric characters
        if keep_alphanum:
            normalized_text = re.sub(r'[^a-zA-Z0-9]', '', normalized_text)
        return normalized_text
    return text
