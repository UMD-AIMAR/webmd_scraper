import json
import re
import string
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from fuzzywuzzy import fuzz

##import nltk
##nltk.download('wordnet')
##nltk.download('stopwords')

wnl = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def extract_symptom_keywords(s):
    pattern = re.compile('[\W_]+')
    words = pattern.sub(' ', s).split()
    return [wnl.lemmatize(word.lower()) for word in words if word not in stop_words]

with open('conditions_clean.json') as f:
    condition_dict = json.load(f)

symp2cond = {}
for cond, data in condition_dict.items():
    for symp in data['symptoms']:
        symp_kw = tuple(extract_symptom_keywords(symp))
        if symp_kw not in symp2cond:
            symp2cond[symp_kw] = []
        symp2cond[symp_kw].append(cond)

# Dealing with synonyms -- word embeddings?
# sorted(match_score('im always nervous').items(), key=lambda x: x[1])[-10:]
def match_score(query):
    # ss: symptom scores
    # cc: candidate condition
    ss = {}
    tokens = extract_symptom_keywords(query)
    for symp_kw in symp2cond:
        ss[symp_kw] = sum(
            [max([fuzz.partial_ratio(token, kw) for kw in symp_kw])
             for token in tokens]) / len(tokens)
    return ss
