"""Functions and Class to manage I/O for Tensorflow Serving Webserver"""

import cv2
import numpy as np
import requests as rq

VALID_CHAR = '2345678abcdefghkmnprwxy'
VALID_SIZE = 5

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

def resize_then_pad(image, height, width):
    img_h, img_w = image.shape
    ratio = min(height / img_h, width / img_w)
    new_img = cv2.resize(image, (int(img_w*ratio), int(img_h*ratio)))
    new_img_h, new_img_w = new_img.shape
    delta_h = height - new_img_h
    delta_w = width - new_img_w
    top = delta_h // 2
    bottom = delta_h - top
    left = delta_w //2
    right = delta_w - left
    new_img = cv2.copyMakeBorder(new_img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=0)
    return new_img

def image_to_list(image):
    """convert and reshape into correct shape (bs,height,width,channel) and return as native Python list"""
    img = np.array(image)
    img = np.expand_dims(img, 0)
    img = np.expand_dims(img, -1)
    return img.tolist()

def preprocess_image(raw_input):
    img = decode_image(raw_input)
    img = preprocess_raw_image(img)
    img = resize_then_pad(img, 64, 128)
    img = image_to_list(img)
    return img

def to_categorical(y, num_classes=None, dtype='float32'):
    """Converts a class vector (integers) to binary class matrix.
    E.g. for use with categorical_crossentropy.
    Arguments:
        y: class vector to be converted into a matrix
            (integers from 0 to num_classes).
        num_classes: total number of classes. If `None`, this would be inferred
        as the (largest number in `y`) + 1.
        dtype: The data type expected by the input. Default: `'float32'`.
    Returns:
        A binary matrix representation of the input. The classes axis is placed
        last.
    """
    y = np.array(y, dtype='int')
    input_shape = y.shape
    if input_shape and input_shape[-1] == 1 and len(input_shape) > 1:
        input_shape = tuple(input_shape[:-1])
    y = y.ravel()
    if not num_classes:
        num_classes = np.max(y) + 1
    n = y.shape[0]
    categorical = np.zeros((n, num_classes), dtype=dtype)
    categorical[np.arange(n), y] = 1
    output_shape = input_shape + (num_classes,)
    categorical = np.reshape(categorical, output_shape)
    return categorical

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

class SolverManager():
    """Manage I/O for Solver"""
    def __init__(self, MODEL_API = r"http://localhost:8501/v1/models/solver:predict"):
        self.API = MODEL_API
        
    def predict(self, raw_input):
        image = preprocess_image(raw_input)
        with rq.post(self.API, json={'instances':image}) as response:
            json_result = response.json()
        return ''.join(array_to_label(np.array(json_result['predictions'])[0]))
    

