import json
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
import numpy as np
from bert_serving.client import BertClient
bc = BertClient()

##import nltk
##nltk.download('wordnet')
##nltk.download('stopwords')

ps = PorterStemmer()
wnl = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))
CONDITIONS_JSON = 'conditions_clean.json'


# Would lemmatization help BERT classification?
def clean_text(s, remove_stopwords=False):
    pattern = re.compile('[\W_]+')
    words = pattern.sub(' ', s.lower()).split()
    if remove_stopwords:
        words = [word for word in words if word not in stop_words]
    return ' '.join([wnl.lemmatize(word) for word in words])


with open(CONDITIONS_JSON) as f:
    condition_dict = json.load(f)

symp2cond = {}
for cond, data in condition_dict.items():
    for symp in data['symptoms']:
        symp = clean_text(symp)
        # symp_kw = tuple(extract_symptom_keywords(symp))
        # if symp_kw not in symp2cond:
        #     symp2cond[symp_kw] = []
        # symp2cond[symp_kw].append(cond)
        if symp not in symp2cond:
            symp2cond[symp] = []
        symp2cond[symp].append(cond)

symptoms = [symptom for symptom in list(symp2cond.keys())]
symp2bert = dict(zip(symptoms, bc.encode(symptoms)))


# BERT works pretty well out of the box, but maybe keyword matching can further improve
def nearest_neighbor(query):
    # clean_query = clean_text(query, remove_stopwords=True)
    clean_query = query
    print(f"Searched using \'{clean_query}\':")
    query_bert = bc.encode([clean_query])
    distances = [(symp, np.linalg.norm(query_bert - symp_bert)) for symp, symp_bert in symp2bert.items()]
    return sorted(distances, key=lambda x: x[1])


# Dealing with synonyms -- word embeddings?
# sorted(match_score('im always nervous').items(), key=lambda x: x[1])[-10:]
# def match_score(query):
#     # ss: symptom scores
#     # cc: candidate condition
#     ss = {}
#     tokens = extract_symptom_keywords(query)
#     for symp_kw in symp2cond:
#         ss[symp_kw] = sum(
#             [max([fuzz.partial_ratio(token, kw) for kw in symp_kw])
#              for token in tokens]) / len(tokens)
#     return ss
