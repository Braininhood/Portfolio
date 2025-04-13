import cv2
import numpy as np
import os
import sys
import tensorflow as tf

from sklearn.model_selection import train_test_split

# Constants
EPOCHS = 10
IMG_WIDTH = 30
IMG_HEIGHT = 30
NUM_CATEGORIES = 43
TEST_SIZE = 0.4


def main():
    # Check command-line arguments
    if len(sys.argv) not in [2, 3]:
        sys.exit("Usage: python traffic.py data_directory [model.h5]")

    # Load image arrays and labels
    images, labels = load_data(sys.argv[1])

    # Convert labels to categorical format
    labels = tf.keras.utils.to_categorical(labels, NUM_CATEGORIES)

    # Split dataset into training and testing sets
    x_train, x_test, y_train, y_test = train_test_split(
        np.array(images), np.array(labels), test_size=TEST_SIZE
    )

    # Get a compiled neural network
    model = get_model()

    # Train the model
    model.fit(x_train, y_train, epochs=EPOCHS)

    # Evaluate model performance
    model.evaluate(x_test, y_test, verbose=2)

    # Save the trained model if a filename was provided
    if len(sys.argv) == 3:
        filename = sys.argv[2]
        model.save(filename)
        print(f"Model saved to {filename}.")


def load_data(data_dir):
    """
    Load image data from directory `data_dir`.

    Each category directory (0 to NUM_CATEGORIES - 1) contains images.
    The function returns:
        - images: List of numpy arrays (each image resized to IMG_WIDTH x IMG_HEIGHT x 3).
        - labels: List of corresponding integer labels.
    """
    images = []
    labels = []

    for category in range(NUM_CATEGORIES):
        category_path = os.path.join(data_dir, str(category))

        if not os.path.isdir(category_path):
            continue  # Skip if directory is missing

        # Load all images in the category folder
        for file in os.listdir(category_path):
            file_path = os.path.join(category_path, file)

            # Read and resize image
            img = cv2.imread(file_path)
            if img is None:
                continue  # Skip invalid images

            img = cv2.resize(img, (IMG_WIDTH, IMG_HEIGHT))
            images.append(img)
            labels.append(category)

    return images, labels


def get_model():
    """
    Returns a compiled convolutional neural network model.

    - Uses Conv2D, MaxPooling, Dropout, and Dense layers.
    - The output layer has NUM_CATEGORIES units (softmax activation).
    """
    model = tf.keras.Sequential([
        # Convolutional layer (32 filters, 3x3 kernel)
        tf.keras.layers.Conv2D(32, (3, 3), activation="relu",
                               input_shape=(IMG_WIDTH, IMG_HEIGHT, 3)),
        tf.keras.layers.MaxPooling2D(pool_size=(2, 2)),

        # Convolutional layer (64 filters, 3x3 kernel)
        tf.keras.layers.Conv2D(64, (3, 3), activation="relu"),
        tf.keras.layers.MaxPooling2D(pool_size=(2, 2)),

        # Flatten layer
        tf.keras.layers.Flatten(),

        # Fully connected hidden layer
        tf.keras.layers.Dense(128, activation="relu"),

        # Dropout layer to prevent overfitting
        tf.keras.layers.Dropout(0.5),

        # Output layer with NUM_CATEGORIES units (softmax for classification)
        tf.keras.layers.Dense(NUM_CATEGORIES, activation="softmax")
    ])

    # Compile the model
    model.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    return model


if __name__ == "__main__":
    main()
