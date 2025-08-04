import cv2
import numpy as np
def remove_small_objects(binary_image, min_size = 2000):

    #find all your connected components (white blobs in your image)
    binary_image = binary_image.astype(np.uint8)
    nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(binary_image, connectivity=8)
    #connectedComponentswithStats yields every seperated component with information on each of them, such as size
    #the following part is just taking out the background which is also considered a component, but most of the time we don't want that.
    sizes = stats[1:, -1]; nb_components = nb_components - 1

    # minimum size of particles we want to keep (number of pixels)
    #here, it's a fixed value, but you can set it as you want, eg the mean of the sizes or whatever
    #min_size = 2000  

    #your answer image
    img2 = np.zeros((output.shape))
    #for every component in the image, you keep it only if it's above min_size
    for i in range(0, nb_components):
      if sizes[i] >= min_size:
          img2[output == i + 1] = 255
  

    return img2

def fill_holes(binary_image):
    h, w = binary_image.shape[:2]
    mask = np.zeros((h+2, w+2), np.uint8)
    cv2.floodFill(255*binary_image.astype(np.uint8), mask, (0,0), 255);
    mask = cv2.bitwise_not(mask)
    return mask[1:-1,1:-1]

def fill_holes2(binary_image):
    h, w = binary_image.shape[:2]
    mask = np.zeros((h+2, w+2), np.uint8)
    cv2.floodFill(255*binary_image.astype(np.uint8), mask, (0,0), 255);
    mask = cv2.bitwise_not(mask)
    return mask

def get_largest_blobs(binary_image, num_blobs):

    #find connected components 
    binary_image = binary_image.astype(np.uint8)
    num_comps, output, stats, centroids = cv2.connectedComponentsWithStats(binary_image, connectivity=8)
  
    sizes = stats[1:, -1]; nb_components = num_comps - 1
   
    blob_indices = np.argsort(sizes)[::-1][0:num_blobs]
  
    aggregate_img = np.zeros((binary_image.shape[0], binary_image.shape[1],num_blobs))

    centroid_list = centroids[blob_indices+1]
    for i in range(num_blobs):
        img2 = np.zeros((output.shape))
        img2[output == blob_indices[i]+1] = 255
        img2 = fill_holes2(img2) == 255
        aggregate_img[:,:,i] = img2[:-2,:-2]
    return aggregate_img, centroid_list
