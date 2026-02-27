import pickle

# ==========================
# LOAD MODEL + VECTORIZER
# ==========================

with open("scam_model.pkl", "rb") as model_file:
    model = pickle.load(model_file)

with open("vectorizer.pkl", "rb") as vectorizer_file:
    vectorizer = pickle.load(vectorizer_file)


# ==========================
# PREDICTION FUNCTION
# ==========================

def predict_message(text: str) -> str:
    """
    Predict whether a message is Scam or Safe.
    Works for numeric or string labels.
    """

    text_vector = vectorizer.transform([text])

    # If model uses probability
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(text_vector)[0]
        scam_prob = max(probabilities)
        return "Scam" if scam_prob > 0.5 else "Safe"

    # Fallback to direct prediction
    prediction = model.predict(text_vector)[0]

    if isinstance(prediction, str):
        return prediction.capitalize()

    return "Scam" if prediction == 1 else "Safe"


# ==========================
# TEST BLOCK
# ==========================

if __name__ == "__main__":
    print("Test 1:", predict_message("Congratulations! You won a free prize"))
    print("Test 2:", predict_message("Hi, are you coming to class today?"))