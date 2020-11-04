"""Collection of helpful function to pre-process image and help
with training/using the neural network"""

from itertools import groupby
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.utils import to_categorical

VALID_CHAR = '2345678abcdefghkmnprwxy'
VALID_SIZE = 5

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

def _all_equal(iterable):
    "Returns True if all the elements are equal to each other"
    g = groupby(iterable)
    return next(g, True) and not next(g, False)

def shuffle_array(array_list, axis=0):
    """shuffle array along given axis

    Args:
        array_list (np.array of tf.tensor)
        axis (int, optional): shuffling axis. Defaults to 0.

    Returns:
        list: list of shuffled array
    """
    if _all_equal((array.shape[axis] for array in array_list)):
        raise AssertionError(f"Arrays are not identical along axis {axis}")
    indices = np.arange(array_list[0].shape[axis])
    np.random.shuffle(indices)
    new_array_list = []
    for array in array_list:
        if isinstance(array, tf.Tensor):
            new_array_list.append(tf.gather(array, indices,axis=axis))
        else:
            new_array_list.append(array[indices])
    return new_array_list

def magic_cudnn_error_go_away():
    """Run this at the top or face dire consequences. I have slight idea how it works,
    but no idea why it's needed"""
    physical_devices = tf.config.experimental.list_physical_devices('GPU')
    tf.config.experimental.set_memory_growth(physical_devices[0], True)

def _comprehend_discriminator_output(array):
    """convert one-hot label array to vector array. To be deprecated (not used anywhere)

    Args:
        array (np.array): one-hot coded label

    Returns:
        np.array: model best guesses
    """
    if isinstance(array, tf.Tensor):
        return tf.math.argmax(tf.math.reduce_mean(tf.math.reduce_mean(array,axis=1),axis=1),axis=1)
    return np.argmax(np.mean(np.mean(array,axis=1),axis=1),axis=1)

# %%
