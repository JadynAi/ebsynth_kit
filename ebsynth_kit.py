import os

from modules.ui import plaintext_to_html

import cv2
import glob
from PIL import Image

from extensions.ebsynth_kit.stage1 import ebsynth_stage1
from extensions.ebsynth_kit.stage1 import supplementary_keyframe
from extensions.ebsynth_kit.stage4 import ebsynth_utility_stage4
from extensions.ebsynth_kit.stage5 import ebsynth_utility_stage5
from extensions.ebsynth_kit.stage6 import ebsynth_utility_stage6


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

def ebsynth_utility_process(stage_index: int, project_dir:str, original_movie_path:str, key_add_last_frame:bool, selected_frame_type:int, frame_width:int, frame_height:int, frame_wh_scale:float,
                    auto_scale:bool,
                    scale_dir:str,        
                    scale_selected_frame_scale_tab:int,
                    scale_frame_width:int,
                    scale_frame_height:int,
                    scale_frame_wh_scale:float, output_fps:int, blend_rate:float, export_type:str):
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
    

    project_args = [project_dir, original_movie_path_new, frame_path, frame_mask_path, frame_key_output]


    if stage_index == 0:
        ebsynth_stage1(dbg, project_args, key_add_last_frame, selected_frame_type, frame_width, frame_height, frame_wh_scale)
    elif stage_index == 1:
        supplementary_keyframe(dbg, project_args, key_add_last_frame, selected_frame_type, frame_width, frame_height, frame_wh_scale)

    elif stage_index == 2:
        dbg.print("stage 2")
        dbg.print("!!! !!! !!!")
        dbg.print("Semantically segment all the pictures under the video_frame folder and process them into mask pictures!")
        dbg.print("It is recommended to use segment anything to batch process the semantic segmentation of all frames!")
        dbg.print("Or use any other way you like to get the mask image")
        return process_end( dbg, "" )

    elif stage_index == 3:
        dbg.print("stage 3")
        dbg.print("")
        dbg.print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        dbg.print("1. Go to img2img tab")
        dbg.print("2. Select multi-frame rendering")
        dbg.print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return process_end( dbg, "" )
    
    elif stage_index == 4:
        ebsynth_utility_stage4(dbg, project_args, auto_scale,
                    scale_dir,        
                    scale_selected_frame_scale_tab,
                    scale_frame_width,
                    scale_frame_height,
                    scale_frame_wh_scale)
    elif stage_index == 5:
        ebsynth_utility_stage5(dbg, project_args)
        
    elif stage_index == 6:
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
    elif stage_index == 7:
        ebsynth_utility_stage6(dbg, project_args, output_fps, blend_rate, export_type)
    else:
        pass

    return process_end( dbg, info )
