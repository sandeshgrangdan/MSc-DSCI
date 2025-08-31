from collections import defaultdict


def make_inverted_index(documents):
    list_inverted_index = defaultdict(list)

    for doc in documents:
        doc_id = doc.get("id", "")
        doc = doc.get("doc", "")
        terms = doc.split()
        for term in terms:
            list_inverted_index[term].append(doc_id)

    return list_inverted_index
