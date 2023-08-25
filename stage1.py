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


def resize_img(img, w, h):
    if img.shape[0] + img.shape[1] < h + w:
        interpolation = interpolation=cv2.INTER_CUBIC
    else:
        interpolation = interpolation=cv2.INTER_AREA

    return cv2.resize(img, (w, h), interpolation=interpolation)

def resize_all_img(path, frame_width, frame_height):
    if not os.path.isdir(path):
        return
    
    pngs = glob.glob( os.path.join(path, "*.png") )
    img = cv2.imread(pngs[0])
    org_h,org_w = img.shape[0],img.shape[1]

    if frame_width == -1 and frame_height == -1:
        return
    elif frame_width == -1 and frame_height != -1:
        frame_width = int(frame_height * org_w / org_h)
    elif frame_width != -1 and frame_height == -1:
        frame_height = int(frame_width * org_h / org_w)
    else:
        pass
    print("({0},{1}) resize to ({2},{3})".format(org_w, org_h, frame_width, frame_height))

    for png in pngs:
        img = cv2.imread(png)
        img = resize_img(img, frame_width, frame_height)
        cv2.imwrite(png, img)

def resize_all_img_by_scale(path, scale):
    if not os.path.isdir(path):
        return
    if scale <= 0:
        dbg.print("scale must bigger than zero!!!")
        return
    
    pngs = glob.glob( os.path.join(path, "*.png") )
    img = cv2.imread(pngs[0])

    for png in pngs:
        img = cv2.imread(png)
        img = cv2.resize(img, (0,0),fx=scale,fy=scale)
        cv2.imwrite(png, img)


def ebsynth_utility_stage1(dbg, project_args, frame_resize_type, frame_width, frame_height, frame_wh_scale):
    dbg.print("stage1")
    dbg.print("")

    tmp_key_frame = 'tmp_keys'
    video_key = 'video_key'

    project_dir, original_movie_path, frame_path, frame_mask_path, _, = project_args

    if os.path.isdir( frame_mask_path ):
        dbg.print("Skip mask dir create")
    else:
        os.makedirs(frame_mask_path, exist_ok=True)

    if os.path.isdir( frame_path ):
        dbg.print("Skip frame extraction")
    else:
        os.makedirs(frame_path, exist_ok=True)

        png_path = os.path.join(frame_path , "%05d.png")
        # ffmpeg.exe -ss 00:00:00  -y -i %1 -qscale 0 -f image2 -c:v png "%05d.png"
        # subprocess.call("ffmpeg -ss 00:00:00  -y -i " + original_movie_path + " -qscale 0 -f image2 -c:v png " + png_path, shell=True)
        subprocess.call(['ffmpeg', '-i', original_movie_path, 
                 '-qscale:v', '0',
                 '-f', 'image2', 
                 '-c:v', 'png',
                 f'{frames_dir}/%05d.png'])

        dbg.print("frame extracted")

        frame_width = max(frame_width,-1)
        frame_height = max(frame_height,-1)

        if frame_resize_type == 0:
            if frame_width != -1 or frame_height != -1:
                dbg.print("resize by size")
                resize_all_img(frame_path, frame_width, frame_height)
        elif frame_resize_type == 1:
            if frame_wh_scale != 1:
                dbg.print("resize by scale")
                resize_all_img_by_scale(frame_path, frame_wh_scale)
    
    if not os.path.exists(tmp_key_frame):   
        os.makedirs(tmp_key_frame)
    # 解码关键帧,检查文件夹是否跳过    
    if not os.listdir(tmp_key_frame):
        subprocess.call(['ffmpeg', '-i', original_movie_path, '-qscale:v', '0', '-vf',
                   'select=eq(pict_type\\,I)', '-vsync', 'vfr',
                   '-c:v', 'png', f'{tmp_key_frame}/%05d.png'])
    # 新文件夹路径  
    if not os.path.exists(video_key):
        os.makedirs(video_key)
        start = time.time()

        start_index = 0
        key_names = sorted(os.listdir(tmp_key_frame))  
        frame_names = sorted(os.listdir(frames_dir))

        for key_name in key_names:
            key = cv2.imread(os.path.join(tmp_key_frame, key_name))
            # 直接 slice 
            frame_names_subset = frame_names[start_index:]  
            print(f'check key {key_name} index {start_index}')
            for i, frame_name in enumerate(frame_names_subset):
                frame = cv2.imread(os.path.join(frames_dir, frame_name))

                if frame.shape == key.shape:
                    diff = cv2.norm(frame, key, cv2.NORM_L1)
                    # difference = cv2.subtract(frame, key) 
                    # gray_diff = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
                    # diff = cv2.countNonZero(gray_diff)
                    if diff == 0:
                        start_index += i + 1
                        print(f'check equals key {key_name} and frame is {frame_name}')
                        # 找到相同的序列帧, cv2.imwrite 存储一份新的图片，但是会导致图片变大
                        # cv2.imwrite(os.path.join(video_key, frame_name), frame)
                        shutil.copy(os.path.join(frames_dir, frame_name),os.path.join(video_key, frame_name)) 
                        break
        ### delete tmp directory
        shutil.rmtree(tmp_key_frame)
        dbg.print("Pick key frame cost: {}".format(time.time() - start))

    dbg.print("completed.")


