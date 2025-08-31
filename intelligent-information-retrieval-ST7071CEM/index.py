import json

from crawler.selenium import Crawler
from utils.clean import clean_text
from utils.config import config
from utils.inverted_index import make_inverted_index
from sklearn.feature_extraction.text import TfidfVectorizer

from utils.logger import pretty_logger
from utils.files import file_handler

dep_author_list = [
    "Piotr Lis",
    "Lien Luu",
    "Philip McCosker",
    "Richard Pennington",
    "Graham Sadler",
    "Uchenna Tony-Okeke",
    "Torri Wang",
]


def handle_inverted_index_and_tf_idf():
    pubs = []
    publication_list_after_stem = []
    with open(f"{config.output_dir}/publication.json", "r") as file:
        pubs = json.load(file)

    processed_docs = []

    count = 1

    refined_publication = []

    for pub in pubs:
        authors = pub["authors"]

        r_pub = pub
        r_auth = []
        for auth in authors:
            if auth["name"] in dep_author_list:
                r_auth.append(auth)
            else:
                r_auth.append({"name": auth.get("name", ""), "link": ""})

        # doc = f"{pub['title']} {pub.get('abstract', '')}"
        doc = f"{pub['title']} {' '.join(a['name'] for a in pub['authors'] if a.get('name') in dep_author_list)}"

        r_pub["authors"] = r_auth
        r_pub["id"] = count

        refined_publication.append(r_pub)

        text = f"{clean_text(doc)}"
        # pretty_logger(text, doc)

        publication_list_after_stem.append(text)

        processed_docs.append(
            {
                "id": count,
                "doc": text,
            }
        )

        count += 1

    # file_handler.write_file(refined_publication, "pubs.json")

    i_index = make_inverted_index(processed_docs)

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(publication_list_after_stem)

    return (i_index, tfidf_matrix, vectorizer)


if __name__ == "__main__":
    i_index = handle_inverted_index_and_tf_idf()

    file_handler.write_file(dict(i_index[0]), "index.json")

    # pretty_logger(i_index, "test")
