
import numpy as np
from PIL import Image, ImageStat 
import cv2 

def is_low_quality_image(pil_image):
    try:
        img_gray = pil_image.convert("L")
        stat = ImageStat.Stat(img_gray)
        mean_brightness = stat.mean[0]
        stddev = stat.stddev[0]
        return mean_brightness < 20 or stddev < 10
    except Exception as e:
        print(f"Error checking image quality: {e}")
        return True

def is_leaf_detected(pil_image):
    try:
        cv_image = np.array(pil_image)
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        lower_green = np.array([20, 20, 20])
        upper_green = np.array([90, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)
        green_pixel_count = np.sum(mask > 0)
        total_pixels = mask.shape[0] * mask.shape[1]
        green_ratio = green_pixel_count / total_pixels
        return green_ratio > 0.05
    except Exception as e:
        print(f"Error during leaf detection: {e}")
        return False
