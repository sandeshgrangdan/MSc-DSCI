import re
import nltk
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag, word_tokenize


nltk.download("stopwords")
nltk.download("punkt_tab")
nltk.download("averaged_perceptron_tagger_eng")
nltk.download("wordnet")

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()


# Convert POS tags to WordNet format
def get_wordnet_pos(word):
    tag = pos_tag([word])[0][1][0].upper()
    tag_dict = {
        "J": wordnet.ADJ,
        "N": wordnet.NOUN,
        "V": wordnet.VERB,
        "R": wordnet.ADV,
    }
    return tag_dict.get(tag, wordnet.NOUN)


def clean_text(text):
    # 1. Lowercase
    text = text.lower()

    # 2. Keep alphanumeric + domain-specific terms (don't remove numbers blindly)
    text = re.sub(r"[^a-zA-Z0-9\s#+]", " ", text)  # keeps things like C++, C#, etc.

    # 3. Tokenize
    words = word_tokenize(text)

    # 4. Remove stopwords
    words = [word for word in words if word not in stop_words]

    # 5. Lemmatize with POS tagging
    words = [lemmatizer.lemmatize(word, get_wordnet_pos(word)) for word in words]

    return " ".join(words)
