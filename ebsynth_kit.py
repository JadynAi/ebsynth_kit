import os

from modules.ui import plaintext_to_html

import cv2
import glob
from PIL import Image

from extensions.ebsynth_kit.stage1 import ebsynth_utility_stage1
from extensions.ebsynth_kit.stage4 import ebsynth_utility_stage4
from extensions.ebsynth_kit.stage6 import ebsynth_utility_stage6
from extensions.ebsynth_kit.stage7 import ebsynth_utility_stage7


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

def ebsynth_utility_process(stage_index: int, project_dir:str, original_movie_path:str, auto_pick_key_frame:bool, selected_frame_type:int, frame_width:int, frame_height:int, frame_wh_scale:float, key_min_gap:int, key_max_gap:int, key_th:float, key_add_last_frame:bool, blend_rate:float, export_type:str, bg_src:str, bg_type:str, mask_blur_size:int, mask_threshold:float, fg_transparency:float):
    args = locals()
    info = ""
    info = dump_dict(info, args)
    dbg = debug_string()


    def process_end(dbg, info):
        return plaintext_to_html(dbg.to_string()), plaintext_to_html(info)


    if not os.path.isdir(project_dir):
        dbg.print("{0} project_dir not found".format(project_dir))
        return process_end( dbg, info )

    if not os.path.isfile(original_movie_path):
        dbg.print("{0} original_movie_path not found".format(original_movie_path))
        return process_end( dbg, info )
    
    frame_path = os.path.join(project_dir , "video_frame")
    frame_mask_path = os.path.join(project_dir, "video_mask")

    if not os.path.exists(frame_mask_path):
        os.makedirs(frame_mask_path, exist_ok=True)

    frame_key_output = os.path.join(inv_path, "video_key_output")
    

    project_args = [project_dir, original_movie_path, frame_path, frame_mask_path, frame_key_output]


    if stage_index == 0:
        ebsynth_utility_stage1(dbg, project_args, auto_pick_key_frame, selected_frame_type, frame_width, frame_height, frame_wh_scale, key_min_gap, key_max_gap, key_th, key_add_last_frame)

    elif stage_index == 1:
        dbg.print("stage 2")
        dbg.print("!!! !!! !!!")
        dbg.print("Semantically segment all the pictures under the video_frame folder and process them into mask pictures!")
        dbg.print("It is recommended to use segment anything to batch process the semantic segmentation of all frames!")
        dbg.print("Or use any other way you like to get the mask image")
        return process_end( dbg, "" )

    elif stage_index == 2:
        dbg.print("stage 3")
        dbg.print("")
        dbg.print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        dbg.print("1. Go to img2img tab")
        dbg.print("2. Select multi-frame rendering")
        dbg.print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return process_end( dbg, "" )
    
    elif stage_index == 3:
        ebsynth_utility_stage5(dbg, project_args, is_invert_mask)
    elif stage_index == 4:
        dbg.print("stage 6")
        dbg.print("")
        dbg.print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        dbg.print("Running ebsynth.(on your self)")
        dbg.print("Open the generated .ebs under %s and press [Run All] button."%(project_dir))
        dbg.print("If ""out-*"" directory already exists in the %s, delete it manually before executing."%(project_dir))
        dbg.print("If multiple .ebs files are generated, run them all.")
        dbg.print("(I recommend associating the .ebs file with EbSynth.exe.)")
        dbg.print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return process_end( dbg, "" )
        
    elif stage_index == 5:
        ebsynth_utility_stage6(dbg, project_args, blend_rate, export_type, is_invert_mask)
    elif stage_index == 6:
        if mask_mode != "Normal":
            dbg.print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            dbg.print("Please reset [configuration]->[etc]->[Mask Mode] to Normal.")
            dbg.print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            return process_end( dbg, "" )
        ebsynth_utility_stage7(dbg, project_args, bg_src, bg_type, mask_blur_size, mask_threshold, fg_transparency, export_type)
    else:
        pass

    return process_end( dbg, info )
