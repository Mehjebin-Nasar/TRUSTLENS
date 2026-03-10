import cv2
import os
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

dataset_path = "dataset"

features = []
labels = []

for category in ["real","fake"]:

    folder = os.path.join(dataset_path,category)

    for img_name in os.listdir(folder):

        img_path = os.path.join(folder,img_name)

        img = cv2.imread(img_path)
        img = cv2.resize(img,(128,128))
        img = img.flatten()

        features.append(img)

        if category == "real":
            labels.append(0)
        else:
            labels.append(1)

features = np.array(features)
labels = np.array(labels)

print("Dataset loaded:",features.shape)


# Train Model
X_train,X_test,y_train,y_test = train_test_split(features,labels,test_size=0.2)

model = RandomForestClassifier()
model.fit(X_train,y_train)

print("Model trained")


# Test with a new image
img = cv2.imread("uploaded.jpg")
img = cv2.resize(img,(128,128))
img = img.flatten().reshape(1,-1)

prediction = model.predict(img)

if prediction == 1:
    print("Possible fake image")
else:
    print("Real image")