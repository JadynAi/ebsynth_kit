import os

from modules.ui import plaintext_to_html

import cv2
import glob
from PIL import Image


project_args= []

def x_ceiling(value, step):
  return -(-value // step) * step

def ebsynth_utility_process(project_dir:str, original_movie_path:str, frame_resize_type:int, frame_width:int, frame_height:int, frame_wh_scale:float,
                    use_specific_fps:bool,
                    decoder_frames_fps:int):

    project_dir = project_dir.replace("\"","")
    if not os.path.isdir(project_dir):
        print("{0} project_dir not found".format(project_dir))

    original_movie_path_new = original_movie_path.replace("\"","")
    if not os.path.isfile(original_movie_path_new):
        print("{0} original_movie_path not found".format(original_movie_path_new))

    frame_path = os.path.join(project_dir , "video_frame")
    frame_mask_path = os.path.join(project_dir, "video_mask")

    if not os.path.exists(frame_mask_path):
        os.makedirs(frame_mask_path, exist_ok=True)

    frame_key_output = os.path.join(project_dir, "video_key_output")
    if not use_specific_fps:
        decoder_frames_fps = -1
    
    global project_args
    project_args = [project_dir, original_movie_path_new, frame_path, frame_mask_path, frame_key_output, decoder_frames_fps]
    print("project_args: {0}".format(project_args))
