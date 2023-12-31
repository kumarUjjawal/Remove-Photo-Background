import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import numpy as np
import cv2
from glob import glob
from tqdm import tqdm
import tensorflow as tf
from tensorflow.keras.utils import CustomObjectScope
from metrics import dice_loss, dice_coef, iou
from cutout import perform_image_cutout
import sys
from trimap_module import trimap
from pymatting import cutout


""" Global parameters """
H = 512
W = 512

""" Creating a directory """
def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

if __name__ == "__main__":
    """ Seeding """
    np.random.seed(42)
    tf.random.set_seed(42)
    
    """ Directory for storing files """
    create_dir("remove_bg")

    """ Loading model: DeepLabV3+ """
    with CustomObjectScope({'iou': iou, 'dice_coef': dice_coef, 'dice_loss': dice_loss}):
        model = tf.keras.models.load_model("model.h5")

    """ Load the dataset """
    data_x = glob("images/*")
    #print(data_x)
    for path in tqdm(data_x, total=len(data_x)):
         """ Extracting name """
         name = path.split("/")[-1].split(".")[0]

         """ Read the image """
         image = cv2.imread(path, cv2.IMREAD_COLOR)
         h, w, _ = image.shape
         x = cv2.resize(image, (W, H))
         x = x/255.0
         x = x.astype(np.float32)
         x = np.expand_dims(x, axis=0)

         """ Prediction """
         y = model.predict(x)[0]
         y = cv2.resize(y, (w, h))
         y = np.expand_dims(y, axis=-1)
         y = y > 0.5

         photo_mask = y
         background_mask = np.abs(1-y)

         masked_photo = image * photo_mask
         background_mask = np.concatenate([background_mask, background_mask, background_mask], axis=-1)
         background_mask = background_mask * [0, 0, 0]
         final_photo = masked_photo + background_mask
         cv2.imwrite(f"remove_bg/{name}.png", final_photo)
    
    # trimap manual input
    #name  = "trimap.png"; 
    #image = cv2.imread(name, cv2.IMREAD_GRAYSCALE)
    size = 10;         
    number = name[-5];
    title = "test_image"

    #trimap(image, title, size, number, erosion=10);

    # Path to the directory containing the images
    directory = "remove_bg"

    # Create a new directory for trimap images
    trimap_directory = "trimap_images"
    if not os.path.exists(trimap_directory):
        os.makedirs(trimap_directory)

    # Iterate over each file in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".png"):
            # Generate the input and output paths for trimap and trimmed images
            input_path = os.path.join(directory, filename)
            output_path = os.path.join(trimap_directory, filename)
            #print(filename)
            print(str(input_path))
            image = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
            trimap(image, title, size, number, erosion=10)
    
    #Cutout Operation
    # Define paths
    input_folder = "./images/"
    trimap_folder = "./trimap_images/"
    output_folder = "./output/"

    # Get the list of image files
    image_files = os.listdir(input_folder)

    # Iterate over the image files
    for image_file in image_files:
        # Get the corresponding trimap file
        image_name = os.path.splitext(image_file)[0]
        trimap_file = image_name + ".png"

        # Check if the trimap file exists
        if os.path.isfile(os.path.join(trimap_folder, trimap_file)):
            # Call the cutout function
            cutout(
                os.path.join(input_folder, image_file),
                os.path.join(trimap_folder, trimap_file),
                os.path.join(output_folder, image_name + "_cutout.png")
            )
        else:
            print(f"No corresponding trimap found for image: {image_file}")
