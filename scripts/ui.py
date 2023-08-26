
import gradio as gr

from ebsynth_kit import ebsynth_utility_process
from modules import script_callbacks
from modules.call_queue import wrap_gradio_gpu_call
from tkinter import filedialog
import queue


def on_ui_tabs():

    with gr.Blocks(analytics_enabled=False) as ebs_interface:
        with gr.Row().style(equal_height=False):
            with gr.Column(variant='panel'):

                with gr.Row():
                    with gr.Column(elem_id="ebs_settings"):
                        project_dir = gr.Textbox(label='Project directory', lines=1)
                        original_movie_path = gr.Textbox(label='Original Movie Path', lines=1)
                        with gr.Accordion("Stage1 setting",open=False):
                            key_add_last_frame = gr.Checkbox(label="Add last frame to keyframes", value=True)
                            selected_frame_scale_tab = gr.State(value=0)
                            with gr.Tabs(elem_id="frame_width_height",default=1):
                                with gr.Tab("Frame resize by size",elem_id='frame_wh_1') as frame_size:
                                    frame_width = gr.Number(value=-1, label="Frame Width", precision=0, interactive=True)
                                    frame_height = gr.Number(value=-1, label="Frame Height", precision=0, interactive=True)
                                with gr.Tab("Frame resize by scale",elem_id='frame_wh_2') as frame_scale:
                                    frame_wh_scale = gr.Slider(minimum=0.1, maximum=2.0, step=0.1, label='Width and height scaling', value=1.0)

                            frame_size.select(fn=lambda: 0, inputs=[], outputs=[selected_frame_scale_tab])
                            frame_scale.select(fn=lambda: 1, inputs=[], outputs=[selected_frame_scale_tab])
                        with gr.Accordion("Stage6 setting",open=False):
                            blend_rate = gr.Slider(minimum=0.0, maximum=1.0, step=0.01, label='Crossfade blend rate', value=1.0)
                            export_type = gr.Dropdown(choices=["mp4","webm","gif","rawvideo"], value="mp4" ,label="Export type")
                                    

                    with gr.Column(variant='panel'):
                        with gr.Column(scale=1):
                            with gr.Group():
                                debug_info = gr.HTML(elem_id="ebs_info_area", value=".")

                            with gr.Column(scale=2):
                                stage_index = gr.Radio(label='Process Stage', choices=["stage 1","stage 2","stage 3","stage 4","stage 5","stage 6"], value="stage 1", type="index")
                                gr.HTML(value="<p style='margin-bottom: 0.7em'>\
                                                The process of creating a video can be divided into the following stages.<br>\
                                                (Stage 2,3 only show a guide and do nothing actual processing.)<br><br>\
                                                <b>stage 1</b> <br>\
                                                    Extract frames from the original video to directory 'video_frame'. <br>\
                                                    Pick keyframes from sequence frames to directory 'video_key'. <br>\
                                                        Automatically selected if auto mode is selected. <br>\
                                                        Otherwise pick keyframes according to the set keyframe options. <br>\
                                                    Please note that if the video_frame or video_key folder exists, the corresponding steps will be skipped. <br><br>\
                                                <b>stage 2(optional)</b> <br>\
                                                    Mask sequence frames.<br><br>\
                                                <b>stage 3</b> <br>\
                                                    img2img keyframes.It is recommended to use multi frame scripts to img2img.<br><br>\
                                                <b>stage 4</b> <br>\
                                                    Generate .ebs file.(ebsynth project file)<br><br>\
                                                <b>stage 5</b> <br>\
                                                    Running ebsynth.(on your self)<br>\
                                                    Open the generated .ebs under project directory and press [Run All] button. <br>\
                                                    If ""out-*"" directory already exists in the Project directory, delete it manually before executing.<br>\
                                                    If multiple .ebs files are generated, run them all.<br><br>\
                                                <b>stage 6</b> <br>\
                                                    Concatenate each frame while crossfading.<br>\
                                                    Composite audio files extracted from the original video onto the concatenated video.<br><br>\
                                                </p>")
                            
                            with gr.Row():
                                generate_btn = gr.Button('Generate', elem_id="ebs_generate_btn", variant='primary')
                            
                            with gr.Group():
                                html_info = gr.HTML()


            ebs_args = dict(
                fn=wrap_gradio_gpu_call(ebsynth_utility_process),
                inputs=[
                    stage_index,

                    project_dir,
                    original_movie_path,

                    key_add_last_frame,
                    selected_frame_scale_tab,

                    frame_width,
                    frame_height,

                    frame_wh_scale,

                    blend_rate,
                    export_type,

                    bg_src,
                    bg_type,
                    mask_blur_size,
                    mask_threshold,
                    fg_transparency,
                ],
                outputs=[
                    debug_info,
                    html_info,
                ],
                show_progress=False,
            )
            generate_btn.click(**ebs_args)
           
    return (ebs_interface, "Ebsynth kit", "ebs_interface"),



script_callbacks.on_ui_tabs(on_ui_tabs)

