import os
import subprocess
import glob
import cv2
import re
import shutil

from transformers import AutoProcessor, CLIPSegForImageSegmentation
from PIL import Image
import torch
import numpy as np
import time


def resize_img(img, w, h):
    if img.shape[0] + img.shape[1] < h + w:
        interpolation = interpolation=cv2.INTER_CUBIC
    else:
        interpolation = interpolation=cv2.INTER_AREA

    return cv2.resize(img, (w, h), interpolation=interpolation)

def resize_all_img(dbg, path, frame_width, frame_height):
    if not os.path.isdir(path):
        return
    
    pngs = glob.glob( os.path.join(path, "*.png") )
    img = cv2.imread(pngs[0])
    org_h,org_w = img.shape[0],img.shape[1]
    if org_w == frame_width and org_h == frame_height:
        print("not need to resize")
        return

    if frame_width == -1 and frame_height == -1:
        return
    elif frame_width == -1 and frame_height != -1:
        frame_width = int(frame_height * org_w / org_h)
    elif frame_width != -1 and frame_height == -1:
        frame_height = int(frame_width * org_h / org_w)
    else:
        pass
    print("({0},{1}) resize to ({2},{3})".format(org_w, org_h, frame_width, frame_height))

    for i,png in enumerate(pngs):
        img = cv2.imread(png)
        img = resize_img(img, frame_width, frame_height)
        cv2.imwrite(png, img)
        print(f"Processing image {i+1}/{len(pngs)}")

def resize_all_img_by_scale(dbg, path, scale):
    if not os.path.isdir(path):
        return
    if scale <= 0:
        dbg.print("scale must bigger than zero!!!")
        return
    
    pngs = glob.glob( os.path.join(path, "*.png") )
    img = cv2.imread(pngs[0])

    for i,png in enumerate(pngs):
        img = cv2.imread(png)
        img = cv2.resize(img, (0,0),fx=scale,fy=scale)
        cv2.imwrite(png, img)
        print(f"Processing image {i+1}/{len(pngs)}")


def ebsynth_utility_stage4(dbg, project_args, auto_scale:bool,
                    scale_dir:str,        
                    scale_selected_frame_scale_tab:int,
                    scale_frame_width:int,
                    scale_frame_height:int,
                    scale_frame_wh_scale:float):
    dbg.print("stage4")
    dbg.print("")

    project_dir, original_movie_path, frame_path, frame_mask_path, frame_key_output, = project_args

    if auto_scale:
        if not os.path.isfile(original_movie_path):
            dbg.print("{0} original_movie_path not found".format(original_movie_path))
            return
    
        dbg.print(original_movie_path)
        capture = cv2.VideoCapture(original_movie_path)

        # 获取视频的宽度和高度
        taget_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        target_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        target_dirs = [os.path.join(project_dir , "video_key"),
                       frame_path,frame_mask_path,frame_key_output]
        for d in target_dirs:
            dbg.print("{0} start scale".format(d))
            scale_dir_pictures(dbg,d,0,taget_width,target_height,scale_frame_wh_scale)
            dbg.print("{0} scale end".format(d))
    else:
        dbg.print("{0} start scale".format(scale_dir))
        scale_dir_pictures(dbg,scale_dir,scale_selected_frame_scale_tab,scale_frame_width,scale_frame_height,scale_frame_wh_scale)
        dbg.print("{0} scale end".format(scale_dir))


    dbg.print("completed.")


def scale_dir_pictures(dbg,scale_dir:str,scale_selected_frame_scale_tab:int,
                    scale_frame_width:int,
                    scale_frame_height:int,
                    scale_frame_wh_scale:float):
    
    scale_frame_width = max(scale_frame_width,-1)
    scale_frame_height = max(scale_frame_height,-1)

    if scale_selected_frame_scale_tab == 0:
        if scale_frame_width != -1 or scale_frame_height != -1:
            dbg.print("scale dir resize by size")
            resize_all_img(dbg, scale_dir, scale_frame_width, scale_frame_height)
    elif scale_selected_frame_scale_tab == 1:
        if scale_frame_wh_scale != 1:
            dbg.print("scale dir resize by scale")
            resize_all_img_by_scale(dbg, scale_dir, scale_frame_wh_scale)


