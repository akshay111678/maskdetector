
import os
import zipfile
import random
import shutil
import tensorflow as tf
from tensorflow.keras.optimizers import RMSprop
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from shutil import copyfile
from os import getcwd
from os import listdir
import cv2
from tensorflow.keras.layers import Conv2D, Input, ZeroPadding2D, BatchNormalization, Activation, MaxPooling2D, Flatten, Dense
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.callbacks import TensorBoard, ModelCheckpoint
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
from sklearn.utils import shuffle
import imutils
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image  as mpimg


# https://github.com/mk-gurucharan/Face-Mask-Detection/blob/master/FaceMask-Detection.ipynb
def split_data(SOURCE, TRAINING, TESTING, SPLIT_SIZE):
    dataset = []

    for unitData in os.listdir(SOURCE):
        data = SOURCE + unitData
        if (os.path.getsize(data) > 0):
            dataset.append(unitData)
        else:
            print('Skipped ' + unitData)
            print('Invalid file i.e zero size')

    train_set_length = int(len(dataset) * SPLIT_SIZE)
    test_set_length = int(len(dataset) - train_set_length)
    shuffled_set = random.sample(dataset, len(dataset))
    train_set = dataset[0:train_set_length]
    test_set = dataset[-test_set_length:]

    for unitData in train_set:
        temp_train_set = SOURCE + unitData
        final_train_set = TRAINING + unitData
        copyfile(temp_train_set, final_train_set)

    for unitData in test_set:
        temp_test_set = SOURCE + unitData
        final_test_set = TESTING + unitData
        copyfile(temp_test_set, final_test_set)


YES_SOURCE_DIR = "C:\\Users\\91866\\PycharmProjects\\mask detector\\observations-master\\experiements\\dest_folder\\val\\with_mask\\"
TRAINING_YES_DIR = "C:\\Users\\91866\\PycharmProjects\\mask detector\\observations-master\\experiements\\dest_folder\\train\\yes1\\"
TESTING_YES_DIR = "C:\\Users\\91866\\PycharmProjects\\mask detector\\observations-master\\experiements\\dest_folder\\test\\yes1\\"
NO_SOURCE_DIR = "C:\\Users\\91866\\PycharmProjects\\mask detector\\observations-master\\experiements\\dest_folder\\val\\without_mask"
TRAINING_NO_DIR = "C:\\Users\\91866\\PycharmProjects\\mask detector\\observations-master\\experiements\\dest_folder\\train\\no1\\"
TESTING_NO_DIR = "C:\\Users\\91866\\PycharmProjects\\mask detector\\observations-master\\experiements\\dest_folder\\test\\no1\\"
# split_size = .8
# split_data(YES_SOURCE_DIR, TRAINING_YES_DIR, TESTING_YES_DIR, split_size)
# split_data(NO_SOURCE_DIR, TRAINING_NO_DIR, TESTING_NO_DIR, split_size)

model = tf.keras.models.Sequential([
    tf.keras.layers.Conv2D(100, (3, 3), activation='relu', input_shape=(150, 150, 3)),
    tf.keras.layers.MaxPooling2D(2, 2),

    tf.keras.layers.Conv2D(100, (3, 3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2, 2),

    tf.keras.layers.Flatten(),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(50, activation='relu'),
    tf.keras.layers.Dense(2, activation='softmax')
])
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['acc'])

TRAINING_DIR = "C:\\Users\\91866\\PycharmProjects\\mask detector\\observations-master\\experiements\\dest_folder\\train"
train_datagen = ImageDataGenerator(rescale=1.0/255,
                                   rotation_range=40,
                                   width_shift_range=0.2,
                                   height_shift_range=0.2,
                                   shear_range=0.2,
                                   zoom_range=0.2,
                                   horizontal_flip=True,
                                   fill_mode='nearest')

train_generator = train_datagen.flow_from_directory(TRAINING_DIR,
                                                    batch_size=10,
                                                    target_size=(150, 150))
VALIDATION_DIR = "C:\\Users\\91866\\PycharmProjects\\mask detector\\observations-master\\experiements\\dest_folder\\test"
validation_datagen = ImageDataGenerator(rescale=1.0/255)

validation_generator = validation_datagen.flow_from_directory(VALIDATION_DIR,
                                                         batch_size=10,
                                                         target_size=(150, 150))
checkpoint = ModelCheckpoint('model-{epoch:03d}.model',monitor='val_loss',verbose=0,save_best_only=True,mode='auto')


history = model.fit_generator(train_generator,
                              epochs=10,
                              validation_data=validation_generator,
                              callbacks=[checkpoint])
model.save("model_01")

face_clsfr=cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

labels_dict = {0: 'without_mask', 1: 'with_mask'}
color_dict = {0: (0, 0, 255), 1: (0, 255, 0)}

size = 4
webcam = cv2.VideoCapture(0)  # Use camera 0

# We load the xml file
faceCascade = cv2.CascadeClassifier('C:\\Users\\91866\\PycharmProjects\\mask detector\\venv\\Lib\\site-packages\\cv2\\data\\haarcascade_frontalface_default.xml')

while True:
    (rval, im) = webcam.read()
    # im = cv2.flip(im, 1, 1)  # Flip to act as a mirror

    # Resize the image to speed up detection
    mini = cv2.resize(im, (im.shape[1] // size, im.shape[0] // size))

    # detect MultiScale / faces
    faces = faceCascade.detectMultiScale(
        mini,
        scaleFactor=1.5,
        minNeighbors=5,
        minSize=(30, 30)
    )
    # Draw rectangles around each face
    for f in faces:
        (x, y, w, h) = [v * size for v in f]  # Scale the shapesize backup
        # Save just the rectangle faces in SubRecFaces
        face_img = im[y:y + h, x:x + w]
        resized = cv2.resize(face_img, (150, 150))
        normalized = resized / 255.0
        reshaped = np.reshape(normalized, (1, 150, 150, 3))
        reshaped = np.vstack([reshaped])
        result = model.predict(reshaped)
        # print(result)

        label = np.argmax(result, axis=1)[0]

        cv2.rectangle(im, (x, y), (x + w, y + h), color_dict[label], 2)
        cv2.rectangle(im, (x, y - 40), (x + w, y), color_dict[label], -1)
        cv2.putText(im, labels_dict[label], (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imshow('frame', im)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    # When everything done, release the capture
webcam.release()
cv2.destroyAllWindows()