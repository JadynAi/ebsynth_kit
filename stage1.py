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
        dbg.print(f"Processing image {i+1}/{len(pngs)}")

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
        dbg.print(f"Processing image {i+1}/{len(pngs)}")

def handle_video(dbg, project_args, video_path:str, is_re_gen:bool, key_add_last_frame:bool, frame_resize_type, frame_width, frame_height, frame_wh_scale):
    original_movie_path = video_path
    project_dir, _, frame_path, frame_mask_path, frame_key_output, = project_args
    tmp_key_frame = os.path.join(project_dir , "tmp_keys")
    video_key =  os.path.join(project_dir , "video_key")
    dbg.print(original_movie_path)

    capture = cv2.VideoCapture(original_movie_path)

        # 获取视频的宽度和高度
    target_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    target_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    capture.release()

    if is_re_gen:
        shutil.rmtree(frame_path,ignore_errors=True)
        shutil.rmtree(tmp_key_frame,ignore_errors=True)
        shutil.rmtree(video_key,ignore_errors=True)
    
    if not os.path.isdir(frame_key_output):
        os.makedirs(frame_key_output, exist_ok=True)

    if os.path.isdir( frame_mask_path ):
        dbg.print("Skip mask dir create")
    else:
        os.makedirs(frame_mask_path, exist_ok=True)

    if os.path.isdir( frame_path ):
        dbg.print("Skip frame extraction")
    else:
        os.makedirs(frame_path, exist_ok=True)

        frame_width = max(frame_width,-1)
        frame_height = max(frame_height,-1)

        if frame_resize_type == 0 and (frame_width != -1 or frame_height != -1) and (frame_width != target_width or frame_height != target_height):
            dbg.print("resize by size")
            # resize_all_img(dbg, frame_path, frame_width, frame_height)
            run_ffmpeg(['-i', original_movie_path,
                '-qscale:v', '0', 
                '-s', f'w={frame_width}:h={frame_height}', 
                '-f', 'image2',
                '-c:v', 'png', 
                f'{frame_path}/%05d.png'])
        elif frame_resize_type == 1 and frame_wh_scale != 1:
            dbg.print("resize by scale")
            # resize_all_img_by_scale(dbg, frame_path, frame_wh_scale)
            run_ffmpeg(['-i', original_movie_path,
                '-qscale:v', '0', 
                '-s', f'in_w*{frame_wh_scale}:in_h*{frame_wh_scale}', 
                '-f', 'image2',
                '-c:v', 'png', 
                f'{frame_path}/%05d.png'])
        else:
            run_ffmpeg(['-i', original_movie_path, 
                 '-qscale:v', '0',
                 '-f', 'image2', 
                 '-c:v', 'png',
                 f'{frame_path}/%05d.png'])

        dbg.print("frame extracted")
    
    if not os.path.exists(tmp_key_frame):   
        os.makedirs(tmp_key_frame)
    # 解码关键帧,检查文件夹是否跳过    
    if not os.listdir(tmp_key_frame):
        frame_width = max(frame_width,-1)
        frame_height = max(frame_height,-1)

        if frame_resize_type == 0 and (frame_width != -1 or frame_height != -1) and (frame_width != target_width or frame_height != target_height):
            dbg.print("resize key by size")
            shutil.rmtree(video_key)
            # resize_all_img(dbg, tmp_key_frame, frame_width, frame_height)
            run_ffmpeg(['-i', original_movie_path, '-qscale:v',
                            '-s', f'w={frame_width}:h={frame_height}', 
                            '0', '-vf',
                            'select=eq(pict_type\\,I)', '-fps_mode', 'vfr',
                            '-c:v', 'png', f'{tmp_key_frame}/%05d.png'])
        elif frame_resize_type == 1 and frame_wh_scale != 1:
            dbg.print("resize key by scale")
            shutil.rmtree(video_key)
            # resize_all_img_by_scale(dbg, tmp_key_frame, frame_wh_scale)
            run_ffmpeg(['-i', original_movie_path, '-qscale:v',
                            '-s', f'in_w*{frame_wh_scale}:in_h*{frame_wh_scale}', 
                            '0', '-vf',
                            'select=eq(pict_type\\,I)', '-fps_mode', 'vfr',
                            '-c:v', 'png', f'{tmp_key_frame}/%05d.png'])
        else:
            run_ffmpeg(['-i', original_movie_path, '-qscale:v', '0', '-vf',
                   'select=eq(pict_type\\,I)', '-fps_mode', 'vfr',
                   '-c:v', 'png', f'{tmp_key_frame}/%05d.png'])
        
    # 新文件夹路径  
    if not os.path.exists(video_key):
        os.makedirs(video_key)
        start = time.time()

        start_index = 0
        key_names = sorted(os.listdir(tmp_key_frame))  
        frame_names = sorted(os.listdir(frame_path))

        for key_name in key_names:
            key = cv2.imread(os.path.join(tmp_key_frame, key_name))
            # 直接 slice 
            frame_names_subset = frame_names[start_index:]  
            print(f'check key {key_name} index {start_index}')
            for i, frame_name in enumerate(frame_names_subset):
                frame = cv2.imread(os.path.join(frame_path, frame_name))

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
                        shutil.copy(os.path.join(frame_path, frame_name),os.path.join(video_key, frame_name)) 
                        break
        ### delete tmp directory
        shutil.rmtree(tmp_key_frame)
        dbg.print("Pick key frame cost: {}".format(time.time() - start))

    dbg.print("completed.")



def ebsynth_utility_stage1(dbg, project_args, key_add_last_frame:bool, frame_resize_type, frame_width, frame_height, frame_wh_scale):
    dbg.print("stage1")
    dbg.print("")

    _, original_movie_path, _, _, _, = project_args
    handle_video(dbg,project_args,original_movie_path,False,key_add_last_frame,frame_resize_type, frame_width, frame_height, frame_wh_scale)


def supplementary_keyframe(dbg, project_args, key_add_last_frame:bool, frame_resize_type, frame_width, frame_height, frame_wh_scale):
    dbg.print("stage1.1 ")
    dbg.print("")

    project_dir, original_movie_path, frame_path, frame_mask_path, _, = project_args
    added_key_frame_video_path =  os.path.join(project_dir , "tmp_supplementary_key_frame_video.mp4")
    dbg.print(original_movie_path)
    if os.path.isfile(added_key_frame_video_path):
        os.remove(added_key_frame_video_path)

    capture = cv2.VideoCapture(original_movie_path)

    # 获取视频的宽度和高度
    fps = 30
    if capture:
        fps = capture.get(cv2.CAP_PROP_FPS)
        capture.release()
    print("original video fps%s".format(fps))

    run_ffmpeg(['-i', original_movie_path,
              '-c:v', 'libx264',
              '-preset', 'slow', 
              '-x264-params', f'keyint={2*fps}:min-keyint={fps}:scenecut=100',
              '-vf', '-yadif=mode=1:parity=-1:deint=0,setpts=N/FRAME_RATE/TB',  
              '-c:a', 'copy',
              added_key_frame_video_path])
    handle_video(dbg,project_args,added_key_frame_video_path,True,key_add_last_frame,frame_resize_type, frame_width, frame_height, frame_wh_scale)

def run_ffmpeg(args: List[str]) -> bool:
    commands = [
        'ffmpeg',
        '-hide_banner',
        '-hwaccel','auto',
        *args
    ]
    subprocess.call(commands)



