import os

from modules.ui import plaintext_to_html

import cv2
import glob
from PIL import Image

from extensions.ebsynth_kit.stage1 import ebsynth_stage1


project_args= []

def x_ceiling(value, step):
  return -(-value // step) * step

def dump_dict(string, d:dict):
    for key in d.keys():
        string += ( key + " : " + str(d[key]) + "\n")
    return string

class debug_string:
    txt = ""
    def print(self, comment):
        print(comment)
        self.txt += comment + '\n'
    def to_string(self):
        return self.txt

def ebsynth_utility_process(project_dir:str, original_movie_path:str, selected_frame_type:int, frame_width:int, frame_height:int, frame_wh_scale:float,
                    use_specific_fps:bool,
                    decoder_frames_fps:int):
    args = locals()
    info = ""
    info = dump_dict(info, args)
    dbg = debug_string()


    def process_end(dbg, info):
        return plaintext_to_html(dbg.to_string()), plaintext_to_html(info)


    project_dir = project_dir.replace("\"","")
    if not os.path.isdir(project_dir):
        dbg.print("{0} project_dir not found".format(project_dir))
        return process_end( dbg, info )

    original_movie_path_new = original_movie_path.replace("\"","")
    if not os.path.isfile(original_movie_path_new):
        dbg.print("{0} original_movie_path not found".format(original_movie_path_new))
        return process_end( dbg, info )

    frame_path = os.path.join(project_dir , "video_frame")
    frame_mask_path = os.path.join(project_dir, "video_mask")

    if not os.path.exists(frame_mask_path):
        os.makedirs(frame_mask_path, exist_ok=True)

    frame_key_output = os.path.join(project_dir, "video_key_output")
    if not use_specific_fps:
        decoder_frames_fps = -1
    

    project_args = [project_dir, original_movie_path_new, frame_path, frame_mask_path, frame_key_output, decoder_frames_fps]

    ebsynth_stage1(dbg, selected_frame_type, frame_width, frame_height, frame_wh_scale)
    return process_end( dbg, info )
