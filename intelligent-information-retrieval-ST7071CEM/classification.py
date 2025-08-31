# task_2_classification/classifier.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


def create_dataset():
    """
    Creates a sample dataset.
    NOTE: You must expand this with at least 100 documents as per the assignment brief.
    """
    data = {
        "text": [
            # Business
            "The stock market saw a significant downturn after the quarterly earnings report.",
            "Venture capital funding for tech startups has increased by 20% this year.",
            "Effective supply chain management is crucial for global logistics companies.",
            "The corporation announced a merger with its biggest competitor.",
            "Consumer spending is a key indicator of economic health and fiscal policy.",
            # Health
            "The new vaccine shows a 95% efficacy rate in clinical trials.",
            "Regular exercise and a balanced diet are essential for cardiovascular health.",
            "Public health officials are monitoring the spread of the new influenza virus.",
            "The hospital opened a new wing dedicated to cancer research and treatment.",
            "Mental health awareness campaigns aim to reduce stigma around therapy.",
            # Politics
            "The parliament passed a new bill on environmental regulations.",
            "Diplomatic talks between the two nations have stalled over trade disputes.",
            "The upcoming election is expected to have a high voter turnout.",
            "The prime minister addressed the nation regarding the new foreign policy.",
            "Government reforms aim to tackle corruption and improve public services.",
        ],
        "category": [
            "Business",
            "Business",
            "Business",
            "Business",
            "Business",
            "Health",
            "Health",
            "Health",
            "Health",
            "Health",
            "Politics",
            "Politics",
            "Politics",
            "Politics",
            "Politics",
        ],
    }
    return pd.DataFrame(data)


class DocumentClassifier:
    def __init__(self):
        """Initializes the classifier and the model pipeline."""
        # Create a pipeline that first vectorizes the text and then applies the classifier
        self.model = make_pipeline(TfidfVectorizer(), MultinomialNB())
        self.is_trained = False

    def train(self, df):
        """Trains the classifier on the provided dataframe."""
        X = df["text"]
        y = df["category"]

        # Split data for evaluation
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        print("Training the classification model...")
        self.model.fit(X_train, y_train)
        self.is_trained = True

        # Evaluate the model
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Model training complete. Accuracy on test set: {accuracy:.2f}\n")

    def classify(self, document):
        """Classifies a new document."""
        if not self.is_trained:
            return "Model is not trained yet. Please call train() first."

        # The model expects a list or iterable of documents
        prediction = self.model.predict([document])
        return prediction[0]


if __name__ == "__main__":
    # 1. Create and load the dataset
    # In a real scenario, you would load this from a file (e.g., CSV)
    # df = pd.read_csv('your_collected_documents.csv')
    dataset = create_dataset()

    # 2. Initialize and train the classifier
    classifier = DocumentClassifier()
    classifier.train(dataset)

    # 3. Use the trained model to classify new documents
    # This demonstrates the system's robustness with various inputs
    print("--- Testing the classifier with new inputs ---")

    # Short input, clear topic
    test_doc_1 = "The company's profits soared last quarter."
    print(f"Input: '{test_doc_1}'")
    print(f"Predicted Category: {classifier.classify(test_doc_1)}\n")

    # Long input with stop words
    test_doc_2 = "Despite ongoing debates in the senate, the proposed healthcare reform bill is expected to be voted on next week."
    print(f"Input: '{test_doc_2}'")
    print(f"Predicted Category: {classifier.classify(test_doc_2)}\n")

    # Input with mixed topics (should pick the dominant one)
    test_doc_3 = "The politician announced a new economic plan to support hospitals."
    print(f"Input: '{test_doc_3}'")
    print(f"Predicted Category: {classifier.classify(test_doc_3)}\n")

    # Challenging input (less common words)
    test_doc_4 = "Fiscal austerity measures were debated by the legislature."
    print(f"Input: '{test_doc_4}'")
    print(f"Predicted Category: {classifier.classify(test_doc_4)}\n")
