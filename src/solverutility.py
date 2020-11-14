"""Helpful function to preprocess image and help with training/using the neural network"""

import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.utils import to_categorical

VALID_CHAR = '2345678abcdefghkmnprwxy'
VALID_SIZE = 5

load_model = tf.keras.models.load_model

def decode_image(bytes_string):
    """Decode the captcha images from bytes string and extract the alpha channel"""
    img = cv2.imdecode(np.frombuffer(bytes_string, np.uint8),-1)
    img = img[:,:,-1]
    return img

def remove_grid(image):
    """Remove grid from captcha using MORPH_OPEN in cv2

    Args:
        image (cv2_image): valid 2D image array

    Returns:
        image: image after removing grid
    """
    kernel = np.full((3,3), 127, np.uint8)
    image[-2:] = 0
    return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

def trim_border(image,pad=1):
    """Trim all zero pixel around captcha. Useful after calling remove_grid
    to simplify image structure

    Args:
        image (array): valid 2D image array
        pad (int, optional): add zero-pixel border around the image. Defaults to 1.

    Returns:
        image: image after trim and pad
    """
    column = np.nonzero(image.sum(axis=0))[0]
    left = column.min()-pad
    right = column.max()+1+pad
    row = np.nonzero(image.sum(axis=1))[0]
    top = row.min()-pad
    bottom = row.max()+1+pad
    return image[top:bottom,left:right]

def preprocess_raw_image(cv2_image, pad=1):
    """Standardize captcha image by consecutively apply remove_grid then trim

    Args:
        cv2_image (2D-array): 2D-array of image. Be careful with how cv2 and numpy treats array
        pad (int, optional): add zero-pixel border around the image. Defaults to 1.

    Returns:
        np.array: numpy array of image
    """
    image = cv2_image
    image = remove_grid(image)
    image = trim_border(image, pad)
    image = np.array(image)
    return image

def image_to_tensor(image):
    """convert and reshape into correct shape (bs,height,width,channel)"""
    image = tf.cast(image, tf.float32)
    image = tf.expand_dims(image, 0)
    image = tf.expand_dims(image, -1)
    image = tf.image.resize_with_pad(image, 64, 128)
    return image

def label_to_array(label, valid_char=VALID_CHAR, valid_num=VALID_SIZE):
    """convert string labels into valid one-hot coded array.
    To be used in BinaryCrossEntropy calculation

    Args:
        label (iterable): label to be converted
        valid_char (iterable, optional): Valid characters list. Defaults to VALID_CHAR.
        valid_num (int, optional): Valid size of label. Defaults to VALID_SIZE.

    Returns:
        np.array: one-hot coded array of label
    """
    label_vector = []
    if len(label) != valid_num:
        raise AssertionError(f'Label must have length = {valid_num}')
    for char in label:
        if char not in valid_char:
            raise AssertionError(f'Label contains invalid char {char}')
        label_vector.append(valid_char.find(char))
    return to_categorical(label_vector, num_classes=len(valid_char))

def array_to_label(array, trans_char=VALID_CHAR):
    """reverse from one-hot coded array to label

    Args:
        array (np.array): one-hot coded array
        trans_char (iterable, optional): translation dictionary. Defaults to VALID_CHAR.

    Returns:
        [type]: [description]
    """
    label_vector = np.argmax(array, axis=-1)
    result = []
    for vector in label_vector:
        result.append(trans_char[vector])
    return result
