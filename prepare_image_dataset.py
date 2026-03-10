import cv2
import os
import numpy as np

dataset_path = "dataset"

features = []
labels = []

for category in ["real", "fake"]:
    folder = os.path.join(dataset_path, category)

    for img_name in os.listdir(folder):

        img_path = os.path.join(folder, img_name)

        img = cv2.imread(img_path)

        img = cv2.resize(img, (128,128))

        img = img.flatten()

        features.append(img)

        if category == "real":
            labels.append(0)
        else:
            labels.append(1)

features = np.array(features)
labels = np.array(labels)

print("Dataset loaded:", features.shape)