import pickle

model = pickle.load(open("scam_model.pkl","rb"))
vectorizer = pickle.load(open("vectorizer.pkl","rb"))

def text_trust_score(text):

    try:

        text_vector = vectorizer.transform([text])

        prediction = model.predict(text_vector)[0]

        if prediction == 1:
            return 30   # suspicious
        else:
            return 85   # trustworthy

    except:
        return 60