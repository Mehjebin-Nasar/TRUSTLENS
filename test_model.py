import pickle

# Load the trained model
with open("scam_model.pkl", "rb") as model_file:
    model = pickle.load(model_file)

# Load the TF-IDF vectorizer
with open("vectorizer.pkl", "rb") as vectorizer_file:
    vectorizer = pickle.load(vectorizer_file)


def predict_message(text: str) -> str:
    """
    Predict whether a message is Scam or Safe.
    """
    text_vector = vectorizer.transform([text])
    prediction = model.predict(text_vector)[0]
    return "Scam" if prediction == 1 else "Safe"


if __name__ == "__main__":
    # Test examples
    print(predict_message("Congratulations! You won a free prize"))
    print(predict_message("Hi, are you coming to class today?"))
