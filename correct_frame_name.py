import os
import re
import shutil
import ebsynth_kit

def correct_split_frame_name():
    project_dir, _, frame_path, frame_mask_path, frame_key_output, _ , = ebsynth_kit.project_args
    dir_path = project_dir

    out_dirs = [d for d in os.listdir(dir_path) if d.startswith('output-')]

    for out_dir in out_dirs:
        img_path = os.path.join(dir_path, out_dir)

        imgs = [f for f in os.listdir(img_path) if os.path.isfile(os.path.join(img_path, f))]

        # 优化正则表达式,检查是否符合 D5 格式
        imgs = [f for f in imgs if not re.match(r'^\d{5}\.\w{3,4}$', f)]
        print("dir {} imgs {}".format(img_path,len(imgs)))

        if len(imgs)==0:
            continue

        first_img = imgs[0]
        ext = first_img.split('.')[-1]

        prefix = out_dir.split('-')[-1]
        start_num = int(prefix) + 1

        imgs.sort()

        for i, img in enumerate(imgs):
            src = os.path.join(img_path, img)
            dst = os.path.join(img_path, '{:05d}.{}'.format(start_num+i, ext))
            shutil.move(src, dst)

    print('Done!')
    