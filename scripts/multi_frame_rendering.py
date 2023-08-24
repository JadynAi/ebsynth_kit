# Original Xanthius (https://xanthius.itch.io/multi-frame-rendering-for-stablediffusion)
# Modified OedoSoldier [大江户战士] (https://space.bilibili.com/55123)
# Modified ClockZinc [星瞳毒唯](https://space.bilibili.com/113557956)
import numpy as np
from tqdm import trange
from PIL import Image, ImageSequence, ImageDraw, ImageFilter, PngImagePlugin

import modules.scripts as scripts
import gradio as gr

from modules import processing, shared, sd_samplers, images
from modules.processing import Processed
from modules.sd_samplers import samplers
from modules.shared import opts, cmd_opts, state
from modules import deepbooru
from modules.script_callbacks import ImageSaveParams, before_image_saved_callback
from modules.sd_hijack import model_hijack

import pandas as pd

import piexif
import piexif.helper

import os,sys
import re
import pandas as pd
sys.path.append('./')
# MY_GLOBAL_VALUE_ITERATION_NUM = 0

# def modify_global_variable(num):
#     global MY_GLOBAL_VALUE_ITERATION_NUM
#     MY_GLOBAL_VALUE_ITERATION_NUM = num

def gr_show(visible=True):
    return {"visible": visible, "__type__": "update"}


def gr_show_value_none(visible=True):
    return {"value": None, "visible": visible, "__type__": "update"}


def gr_show_and_load(value=None, visible=True):
    if value:
        if value.orig_name.endswith('.csv'):
            value = pd.read_csv(value.name)
        else:
            value = pd.read_excel(value.name)
    else:
        visible = False
    return {"value": value, "visible": visible, "__type__": "update"}

def sort_images(lst):
    pattern = re.compile(r"[\d\u4e00-\u9fa5]+(?=\.)(?!.*[\d\u4e00-\u9fa5])")
    try:
        sorted_lst  = sorted(lst, key=lambda x: int(re.search(pattern, x).group()))
        return sorted_lst
    except:
        return lst

class Script(scripts.Script):
    def title(self):
        return "(ebsynth) Multi-frame rendering"

    def show(self, is_img2img):
        return is_img2img

    def ui(self, is_img2img):
        self.num_controlnet_units = opts.data.get("control_net_max_models_num", 1)
        with gr.Row():
            input_dir = gr.Textbox(label='Input directory', lines=1)
            output_dir = gr.Textbox(label='Output directory', lines=1)
        # reference_imgs = gr.UploadButton(label="Upload Guide Frames", file_types = ['.png','.jpg','.jpeg'], live=True, file_count = "multiple")
        first_denoise = gr.Slider(
            minimum=0,
            maximum=1,
            step=0.05,
            label='Initial denoising strength',
            value=1,
            elem_id=self.elem_id("first_denoise"))
        append_interrogation = gr.Dropdown(
            label="Append interrogated prompt at each iteration", choices=[
                "None", "CLIP", "DeepBooru"], value="None")
        third_frame_image = gr.Dropdown(
            label="Third column (reference) image",
            choices=[
                "None",
                "FirstGen",
                "OriginalImg",
                "Historical",
                "SecondImg"],
            value="FirstGen")
        color_correction_enabled = gr.Checkbox(
            label="Enable color correction",
            value=False,
            elem_id=self.elem_id("color_correction_enabled"))
        unfreeze_seed = gr.Checkbox(
            label="Unfreeze seed",
            value=False,
            elem_id=self.elem_id("unfreeze_seed"))
        loopback_source = gr.Dropdown(
            label="Loopback source",
            choices=[
                "None",
                "Previous",
                "Current",
                "First"],
            value="Current")
        org_alpha = gr.Slider(
            minimum=0,
            maximum=1,
            step=0.01,
            label='图片可视度',
            value=1)
        with gr.Row():
            single_mode_checkbox = gr.Checkbox(label="单图模式\\single mode")
            mask_mode_checkbox = gr.Checkbox(label="掩码重绘\\mask inpaint mode")
            path_name_match_checkbox = gr.Checkbox(label="与图片名称匹配\\mask_name matches figure_name")
        with gr.Column(variant='panel',visible= False) as mask_mode_block:
            # 这是mask的设置
            with gr.Row(variant='panel'):
                IS_recstrth = gr.Slider(
                    minimum=1,
                    maximum=255,
                    step=1,
                    label="背景去除强度\\background remove strength",
                    value=30)
                
            # 如果没有就使用默认文件夹内的
            mask_dir = gr.Textbox(label='Mask Input directory', lines=1)
            # 开启后，mask的名字和path的名字一致
             

            # 使用Controlnet_inpaint
        using_ctrl_net_inpaint_checkbox = gr.Checkbox(label="使用Controlnet_inpaint\\use controlnet inpaint")
        with gr.Row(visible=False) as ctrlnet_inpaint_block:
            ctrlnet_inpaint_unit_num = gr.Dropdown(
                [f"Controlnet Unit {i}" for i in range(self.num_controlnet_units)], label="ControlNet inpaint索引\\ControlNet inpaint model index")
            test_full_inpaint_checkbox = gr.Checkbox(label="(test)use controlnet inpaint but not use any SD inpaint")
        
        change_controlnet_image_checkbox = gr.Checkbox(label="批次更改controlnet的图片\\Use another image as ControlNet input")
        with gr.Row(visible=False) as ctrlnet_image_info:
                    ctrlnet_image_dirs = []
                    with gr.Group():
                        with gr.Tabs():
                            for i in range(self.num_controlnet_units):
                                with gr.Tab(f"Controlnet Unit {i}", open=False):
                                    ctrlnet_image_dirs.append(gr.Textbox(label='controlnet图片输入地址\\ControlNet Image input directory', lines=1))
                                    ctrlnet_image_dirs.append(gr.Checkbox(label="固定单张图片\\fixed controlnet image"))




        def visible_mask_mode(mask_mode_checkbox):
            if mask_mode_checkbox:
                return gr.update(visible=True)
            else:
                return gr.update(visible=False)
        # 掩码重绘开启与否，使用的话就打开？
        mask_mode_checkbox.change(fn=visible_mask_mode,inputs=[mask_mode_checkbox],outputs=[mask_mode_block])
        # 是否使用ctrlnet自带的inpaint,使用就打开就行了。
        using_ctrl_net_inpaint_checkbox.change(fn=visible_mask_mode,inputs=[using_ctrl_net_inpaint_checkbox],outputs=[ctrlnet_inpaint_block])
        # 更换controlnet的输入图片
        change_controlnet_image_checkbox.change(fn=visible_mask_mode,inputs=[change_controlnet_image_checkbox],outputs=[ctrlnet_image_info])

        with gr.Row():
            use_txt = gr.Checkbox(label='Read tags from text files')

        with gr.Row():
            txt_path = gr.Textbox(
                label='Text files directory (Optional, will load from input dir if not specified)',
                lines=1)

        with gr.Row():
            use_csv = gr.Checkbox(label='Read tabular commands')
            csv_path = gr.File(
                label='.csv or .xlsx',
                file_types=['file'],
                visible=False)

        with gr.Row():
            with gr.Column():
                table_content = gr.Dataframe(visible=False, wrap=True)

        use_csv.change(
            fn=lambda x: [gr_show_value_none(x), gr_show_value_none(False)],
            inputs=[use_csv],
            outputs=[csv_path, table_content],
        )
        csv_path.change(
            fn=lambda x: gr_show_and_load(x),
            inputs=[csv_path],
            outputs=[table_content],
        )

        return [
            append_interrogation,
            input_dir,
            output_dir,
            first_denoise,
            third_frame_image,
            color_correction_enabled,
            unfreeze_seed,
            loopback_source,
            use_csv,
            table_content,
            use_txt,
            txt_path,
            single_mode_checkbox,
            org_alpha,
            mask_mode_checkbox,
            IS_recstrth,
            mask_dir,
            path_name_match_checkbox,
            using_ctrl_net_inpaint_checkbox,
            change_controlnet_image_checkbox,
            ctrlnet_inpaint_unit_num,
            test_full_inpaint_checkbox,
            *ctrlnet_image_dirs,
            ]

    def run(
            self,
            p,
            append_interrogation,
            input_dir,
            output_dir,
            first_denoise,
            third_frame_image,
            color_correction_enabled,
            unfreeze_seed,
            loopback_source,
            use_csv,
            table_content,
            use_txt,
            txt_path,
            single_mode_checkbox,
            org_alpha,
            mask_mode_checkbox,
            IS_recstrth,
            mask_dir,
            path_name_match_checkbox,
            using_ctrl_net_inpaint_checkbox,
            change_controlnet_image_checkbox,
            ctrlnet_inpaint_unit_num,
            test_full_inpaint_checkbox,
            *ctrlnet_image_dirs,
            ):
        freeze_seed = not unfreeze_seed
        # second_flag = False
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)       

        # 在目标目录下创建一个mask文件夹，储存文件
        if mask_mode_checkbox:
            if mask_dir: # 
                mask_path = mask_dir
                if not os.path.exists(mask_path):
                    print("Mask folder not detected 未检测到蒙版路径")
            


        if use_csv:
            prompt_list = [i[0] for i in table_content.values.tolist()]
            prompt_list.insert(0, prompt_list.pop())

        # 图片信息与蒙版信息收集
        reference_imgs = [os.path.join(input_dir,f) for f in os.listdir(input_dir) if re.match(r'.+\.(jpg|png)$',f)]
        reference_imgs = sort_images(reference_imgs)
        if mask_mode_checkbox:
            if path_name_match_checkbox:
                mask_imgs = [os.path.join(mask_path,f) for f in os.listdir(input_dir) if re.match(r'.+\.(jpg|png)$',f)]
                mask_imgs = sort_images(mask_imgs)
            else:
                mask_imgs = [os.path.join(mask_path,f) for f in os.listdir(mask_path) if re.match(r'.+\.(jpg|png)$',f)]
                mask_imgs = sort_images(mask_imgs)
        
        if change_controlnet_image_checkbox:
            single_ctrlnet_image_flags = ctrlnet_image_dirs[1::2]
            ctrlnet_image_dirs = ctrlnet_image_dirs[::2]
            ctrlnet_image_dirs = [input_dir if ctrlnet_image_dir=="" else ctrlnet_image_dir for ctrlnet_image_dir in ctrlnet_image_dirs]
            # 这边默认是和原文件同名
            cn_images = []
            for ctrlnet_image_dir, single_ctrlnet_image_flag in zip(ctrlnet_image_dirs,single_ctrlnet_image_flags):
                # 如果是开启的单图模式，将默认第一张图的路径
                if single_ctrlnet_image_flag:
                    image_paths = [os.path.join(ctrlnet_image_dir, os.listdir(ctrlnet_image_dir)[0]) for _ in reference_imgs]
                # 如果不是单图模式，判断第一张图片路径是否存在
                else : 
                    # 如果存在，则进行匹配
                    if os.path.exists(os.path.join(ctrlnet_image_dir,os.path.basename(reference_imgs[0]))):
                        image_paths = [os.path.join(ctrlnet_image_dir, os.path.basename(path)) for path in reference_imgs]
                    # 如果不存在，就默认里面所有文件了，直接开摆！
                    else :
                        image_paths = [os.path.join(ctrlnet_image_dir, f) for f in os.listdir(ctrlnet_image_dir) if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
                cn_images.append(image_paths)

        print(f"ISnet::MFR::will process {len(reference_imgs):4d} images")

        if use_txt:
            if txt_path == "":
                files = [re.sub(r'\.(jpg|png)$', '.txt', path)
                         for path in reference_imgs]
            else:
                files = [
                    os.path.join(
                        txt_path,
                        os.path.basename(
                            re.sub(
                                r'\.(jpg|png)$',
                                '.txt',
                                path))) for path in reference_imgs]
            prompt_list = [open(file, 'r').read().rstrip('\n')
                           for file in files]

        loops = len(reference_imgs)

        processing.fix_seed(p)
        batch_count = p.n_iter

        p.batch_size = 1
        p.n_iter = 1

        output_images, info = None, None
        initial_seed = p.seed
        initial_info = None

        initial_width = p.width
        initial_img = reference_imgs[0]  # p.init_images[0]
        p.init_images = [
            Image.open(initial_img).convert("RGBA").resize(
                (initial_width, p.height), Image.ANTIALIAS)]

        # grids = []
        # all_images = []
        # original_init_image = p.init_images
        original_prompt = p.prompt
        if original_prompt != "":
            original_prompt = original_prompt.rstrip(
                ', ') + ', ' if not original_prompt.rstrip().endswith(',') else original_prompt.rstrip() + ' '
        original_denoise = p.denoising_strength
        state.job_count = loops * batch_count

        initial_color_corrections = [
            processing.setup_color_correction(
                p.init_images[0])]

        # for n in range(batch_count):
        history = None
        # frames = []
        third_image = None
        third_image_index = 0
        frame_color_correction = None

        # Reset to original init image at the start of each batch
        p.width = initial_width
        p.mask_blur = 0
        p.control_net_resize_mode = "Just Resize"
        # p.control_net_resize_mode = "Scale to Fit (Inner Fit)"
        if single_mode_checkbox :
            print("ISNET::MFR::Single mode OPEN!!!")
            third_frame_image = "None"
        for i in range(loops):
            # modify_global_variable(int(i))
            if state.interrupted:
                break
            filename = os.path.basename(reference_imgs[i])
            p.n_iter = 1
            p.batch_size = 1
            p.do_not_save_grid = True
            # 选择controlnet输入的图像
            p.control_net_input_image = Image.open(
                reference_imgs[i]).convert("RGBA").resize(
                (initial_width, p.height), Image.ANTIALIAS)
            if mask_mode_checkbox:
                Isnet_mask = Image.open(
                    mask_imgs[i]).convert("RGBA").resize(
                    (initial_width, p.height), Image.ANTIALIAS)

            if(i > 0):
                loopback_image = p.init_images[0]
                if loopback_source == "Current":
                    loopback_image = p.control_net_input_image
                elif loopback_source == "First":
                    loopback_image = history
                elif loopback_source == "None":
                    loopback_image = Image.open(
                        reference_imgs[i]).convert("RGBA").resize(
                        (initial_width, p.height), Image.ANTIALIAS)
                    if org_alpha != 1:
                        img2 = Image.new("RGBA", (initial_width, p.height), "white")
                        loopback_image = Image.blend(img2, loopback_image, org_alpha)

                if third_frame_image != "None":
                    p.width = initial_width * 3
                    img = Image.new("RGBA", (initial_width * 3, p.height))
                    img.paste(p.init_images[0], (0, 0))
                    # img.paste(p.init_images[0], (initial_width, 0))
                    img.paste(loopback_image, (initial_width, 0))
                    if i == 1:
                        third_image = p.init_images[0]
                    img.paste(third_image, (initial_width * 2, 0))
                    p.init_images = [img]
                    if color_correction_enabled:
                        p.color_corrections = [
                            processing.setup_color_correction(img)]


                    if change_controlnet_image_checkbox:
                        msk = []
                        # 这边需要创建不少图呢 疯狂cv 大江户
                        for cn_image in cn_images:
                            m = Image.new("RGB", (initial_width * 3, p.height))
                            m.paste(Image.open(cn_image[i - 1]).resize(
                                (initial_width, p.height), Image.ANTIALIAS), (0, 0))
                            m.paste(Image.open(cn_image[i]).resize(
                                (initial_width, p.height), Image.ANTIALIAS), (initial_width, 0))
                            m.paste(Image.open(cn_image[third_image_index]).resize(
                                (initial_width, p.height), Image.ANTIALIAS), (initial_width * 2, 0))
                            msk.append(m)
                    else:
                        msk = Image.new("RGBA", (initial_width * 3, p.height))
                        msk.paste(Image.open(reference_imgs[i - 1]).convert("RGBA").resize(
                            (initial_width, p.height), Image.ANTIALIAS), (0, 0))
                        msk.paste(p.control_net_input_image, (initial_width, 0))
                        msk.paste(Image.open(reference_imgs[third_image_index]).convert("RGBA").resize(
                            (initial_width, p.height), Image.ANTIALIAS), (initial_width * 2, 0))
                        
                    p.control_net_input_image = msk


                    # 这是生成mask的蒙版的
                    latent_mask = Image.new(
                        "RGBA", (initial_width * 3, p.height), "black")
                    if mask_mode_checkbox:
                        latent_mask.paste(Isnet_mask,(initial_width, 0))
                    else:
                        latent_draw = ImageDraw.Draw(latent_mask)
                        latent_draw.rectangle(
                            (initial_width, 0, initial_width * 2, p.height), fill="white")
                        
                    # 如果没有测试全图SDinpaint     
                    if not test_full_inpaint_checkbox:
                        p.image_mask = latent_mask
                    else :
                        latent_mask1 = Image.new(
                        "RGBA", (initial_width * 3, p.height), "black")
                        latent_draw = ImageDraw.Draw(latent_mask1)
                        latent_draw.rectangle(
                            (initial_width, 0, initial_width * 2, p.height), fill="white")
                        p.image_mask = latent_mask1

                    p.denoising_strength = original_denoise
                elif not single_mode_checkbox:
                    p.width = initial_width * 2
                    img = Image.new("RGBA", (initial_width * 2, p.height))
                    img.paste(p.init_images[0], (0, 0))
                    # img.paste(p.init_images[0], (initial_width, 0))
                    img.paste(loopback_image, (initial_width, 0))
                    p.init_images = [img]
                    if color_correction_enabled:
                        p.color_corrections = [
                            processing.setup_color_correction(img)]
                        
                    if change_controlnet_image_checkbox:
                        msk = []
                        for cn_image in cn_images:
                            m = Image.new("RGB", (initial_width * 2, p.height))
                            m.paste(Image.open(cn_image[i - 1]).resize((initial_width, p.height), Image.ANTIALIAS), (0, 0))
                            m.paste(Image.open(cn_image[i]).resize((initial_width, p.height), Image.ANTIALIAS), (initial_width, 0))
                        msk.append(m) 
                    else :
                        msk = Image.new("RGBA", (initial_width * 2, p.height))
                        msk.paste(Image.open(reference_imgs[i - 1]).convert("RGBA").resize(
                            (initial_width, p.height), Image.ANTIALIAS), (0, 0))
                        msk.paste(p.control_net_input_image, (initial_width, 0))
                    p.control_net_input_image = msk
                    # frames.append(msk)

                    # latent_mask = Image.new("RGBA", (initial_width*2, p.height), "white")
                    # latent_draw = ImageDraw.Draw(latent_mask)
                    # latent_draw.rectangle((0,0,initial_width,p.height), fill="black")
                    latent_mask = Image.new(
                        "RGBA", (initial_width * 2, p.height), "black")
                    if mask_mode_checkbox:
                        latent_mask.paste(Isnet_mask,(initial_width, 0))
                    else:
                        latent_draw = ImageDraw.Draw(latent_mask)
                        latent_draw.rectangle(
                            (initial_width, 0, initial_width * 2, p.height), fill="white")

                    # p.latent_mask = latent_mask
                    # 如果没有测试全图SDinpaint
                    if not test_full_inpaint_checkbox:
                        p.image_mask = latent_mask
                    else :
                        latent_mask1 = Image.new(
                        "RGBA", (initial_width * 2, p.height), "black")
                        latent_draw = ImageDraw.Draw(latent_mask1)
                        latent_draw.rectangle(
                            (initial_width, 0, initial_width * 2, p.height), fill="white")
                        p.image_mask = latent_mask1
                    p.denoising_strength = original_denoise

                # 单图模式
                elif single_mode_checkbox:
                    p.width = initial_width
                    img = loopback_image.copy()
                    p.init_images = [img]
                    if color_correction_enabled:
                        p.color_corrections = [
                            processing.setup_color_correction(img)]
                    
                    if change_controlnet_image_checkbox:
                        msk = [Image.open(cn_image[i]).resize((initial_width, p.height)) for cn_image in cn_images] 
                    else :
                        msk = p.control_net_input_image.resize((initial_width, p.height), Image.ANTIALIAS)

                    p.control_net_input_image = msk
                    # frames.append(msk)

                    # latent_mask = Image.new("RGBA", (initial_width*2, p.height), "white")
                    # latent_draw = ImageDraw.Draw(latent_mask)
                    # latent_draw.rectangle((0,0,initial_width,p.height), fill="black")
                    if mask_mode_checkbox:
                        latent_mask = Isnet_mask
                    else:
                        latent_mask = Image.new(
                            "RGBA", (initial_width, p.height), "white")
                    
                    # latent_draw = ImageDraw.Draw(latent_mask)
                    # latent_draw.rectangle(
                    #     (initial_width, 0, initial_width * 2, p.height), fill="white")

                    # p.latent_mask = latent_mask
                    # 如果没有测试全图SDinpaint
                    if not test_full_inpaint_checkbox:
                        p.image_mask = latent_mask
                    else :
                        latent_mask1 = Image.new(
                            "RGBA", (initial_width, p.height), "white")
                        p.image_mask = latent_mask

                    p.denoising_strength = original_denoise
            else:
                if mask_mode_checkbox:
                    latent_mask = Isnet_mask
                else:
                    latent_mask = Image.new(
                        "RGBA", (initial_width, p.height), "white")
                # p.latent_mask = latent_mask
                # 如果没有测试全图SDinpaint
                if not test_full_inpaint_checkbox:
                    p.image_mask = latent_mask
                else :
                    # latent_mask1 = Image.new(
                    #     "RGBA", (initial_width, p.height), "white")
                    # p.image_mask = latent_mask1
                    pass

                p.denoising_strength = first_denoise
                if change_controlnet_image_checkbox:
                    msk = [Image.open(cn_image[i]).resize((initial_width, p.height)) for cn_image in cn_images] 
                else :
                    msk = p.control_net_input_image.resize((initial_width, p.height), Image.ANTIALIAS)
                p.control_net_input_image = msk
                
                init_image_for_0 = Image.open(reference_imgs[0]).convert("RGBA").resize((p.width, p.height), Image.ANTIALIAS)
                if org_alpha != 1:
                    img2 = Image.new("RGBA", (initial_width, p.height), "white")
                    loopback_image = Image.blend(img2, loopback_image, org_alpha)
                if color_correction_enabled:
                    p.color_corrections = [
                        processing.setup_color_correction(init_image_for_0)]
                p.init_images = [init_image_for_0
                    ]
                # frames.append(p.control_net_input_image)

            # if opts.img2img_color_correction:
            #     p.color_corrections = initial_color_corrections

            if append_interrogation != "None":
                p.prompt = original_prompt
                if append_interrogation == "CLIP":
                    p.prompt += shared.interrogator.interrogate(p.init_images[0])
                elif append_interrogation == "DeepBooru":
                    p.prompt += deepbooru.model.tag(p.init_images[0])

            if use_csv or use_txt:
                p.prompt = original_prompt + prompt_list[i]

            
            # 首先是考虑ctrlnet inpaint
            if using_ctrl_net_inpaint_checkbox:
                if not change_controlnet_image_checkbox:
                    p.control_net_input_image = [p.control_net_input_image] * self.num_controlnet_units
                p.control_net_input_image[int(ctrlnet_inpaint_unit_num[-1])] = {"image": p.init_images[0], "mask": latent_mask.convert("L")}

            processed = processing.process_images(p)

            if initial_seed is None:
                initial_seed = processed.seed
            if initial_info is None:
                initial_info = processed.info

            init_img = processed.images[0]
            if(i > 0) and (not single_mode_checkbox):
                init_img = init_img.crop(
                    (initial_width, 0, initial_width * 2, p.height))
            elif single_mode_checkbox:
                init_img = init_img.crop(
                    (0, 0, initial_width, p.height))


            comments = {}
            if len(model_hijack.comments) > 0:
                for comment in model_hijack.comments:
                    comments[comment] = 1

            info = processing.create_infotext(
                p,
                p.all_prompts,
                p.all_seeds,
                p.all_subseeds,
                comments,
                0,
                0)
            pnginfo = {}
            if info is not None:
                pnginfo['parameters'] = info

            params = ImageSaveParams(init_img, p, filename, pnginfo)
            before_image_saved_callback(params)
            fullfn_without_extension, extension = os.path.splitext(
                filename)

            info = params.pnginfo.get('parameters', None)

            def exif_bytes():
                return piexif.dump({
                    'Exif': {
                        piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(info or '', encoding='unicode')
                    },
                })

            if extension.lower() == '.png':
                pnginfo_data = PngImagePlugin.PngInfo()
                for k, v in params.pnginfo.items():
                    pnginfo_data.add_text(k, str(v))

                init_img.save(
                    os.path.join(
                        output_dir,
                        filename),
                    pnginfo=pnginfo_data)

            elif extension.lower() in ('.jpg', '.jpeg', '.webp'):
                init_img.save(os.path.join(output_dir, filename))

                if opts.enable_pnginfo and info is not None:
                    piexif.insert(
                        exif_bytes(), os.path.join(
                            output_dir, filename))
            else:
                init_img.save(os.path.join(output_dir, filename))

            if third_frame_image != "None":
                if third_frame_image == "FirstGen" and i == 0:
                    third_image = init_img
                    third_image_index = 0
                elif third_frame_image == "OriginalImg" and i == 0:
                    third_image = initial_img[0]
                    third_image_index = 0
                elif third_frame_image == "Historical":
                    third_image = processed.images[0].crop(
                        (0, 0, initial_width, p.height))
                    third_image_index = (i - 1)
                elif third_frame_image == "SecondImg" and i < 3:
                    # print('\n',f'loop_length : {loops}',f'third_image_index : {third_image_index}','\n')
                    third_image = processed.images[0].crop(
                        (0, 0, initial_width, p.height))
                    third_image_index = (i - 1)
                    # print('\n',f'loop_length : {loops}',f'third_image_index : {third_image_index}','\n')



            p.init_images = [init_img]
            if(freeze_seed):
                p.seed = initial_seed
            else:
                p.seed = processed.seed + 1
            # p.seed = processed.seed
            if i == 0:
                history = init_img

        processed = Processed(p, [], initial_seed, initial_info)
        print("\r\n-------------------\r\n ISNET::MFR is DONE! \r\n-------------------")

        return processed


if __name__ == '__main__':
    A = Image.new("RGBA", (100 * 3, 200), "black")
    print('done')