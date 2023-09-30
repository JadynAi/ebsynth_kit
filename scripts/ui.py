
from cProfile import label
import gradio as gr

from ebsynth_kit import ebsynth_utility_process
from modules import script_callbacks
from modules.call_queue import wrap_gradio_gpu_call
from stage1 import ebsynth_stage1
import ebsynth_kit


def on_ui_tabs():

    with gr.Blocks(analytics_enabled=False) as ebs_interface:
        with gr.Row().style(equal_height=False):
            with gr.Column(variant='panel'):

                with gr.Row():
                    with gr.Column(elem_id="detail",scale = 0.5):
                        gr.HTML(value="<p style='margin-bottom: 0.7em'>\
                                        The process of creating a video can be divided into the following stages.<br>\
                                        (Stage 2,3,5 only show a guide and do nothing actual processing.)<br><br>\
                                        <b>stage 1</b> <br>\
                                            Extract frames from the original video to directory 'video_frame'. <br>\
                                            Pick keyframes from sequence frames to directory 'video_key'. <br>\
                                            Please note that if the video_frame or video_key folder exists, the corresponding steps will be skipped. <br>\
                                            If the number of keyframes is too few,then after ebsynth runs,it will cause screen tearing, and many sequence frames cannot be used.<br>\
                                            This step is to increase the number of keyframes.<br>\
                                            This step will delete the original video_key folder and generate a new video_key folder.Maybe you need backup the folder.<br><br>\
                                        <b>stage 2(optional)</b> <br>\
                                            Mask sequence frames.<br>\
                                            Use SegmentAnything or whatever you like to mask all images in the video_frame folder.<br><br>\
                                        <b>stage 3</b> <br>\
                                            img2img keyframes to directory video_key_output.It is recommended to use multi frame scripts to img2img.<br><br>\
                                        <b>stage 4(optional)</b> <br>\
                                            Enlarge or reduce all the pictures in the folder you specify, or crop them to the size you want.<br>\
                                            The purpose of this step is to scale the image back to the size of the original video before encoding it into a video.<br>\
                                            It is recommended that you restore the size of the pictures in the video_key/video_key_output/video_frame/video_mask file.<br><br>\
                                        <b>stage 5</b> <br>\
                                            Generate .ebs file.(ebsynth project file)<br><br>\
                                        <b>stage 6</b> <br>\
                                            Running ebsynth.(on your self)<br>\
                                            Open the generated .ebs under project directory and press [Run All] button. <br>\
                                            If ""out-*"" directory already exists in the Project directory, delete it manually before executing.<br>\
                                            If multiple .ebs files are generated, run them all.<br><br>\
                                        <b>stage 7</b> <br>\
                                            Concatenate each frame while crossfading.<br>\
                                            Composite audio files extracted from the original video onto the concatenated video.<br><br>\
                                        </p>")
                        with gr.Group():
                            html_info = gr.HTML()
                            
                    with gr.Column(elem_id="process stage"):
                        debug_info = gr.HTML(elem_id="ebs_info_area", value=".")

                        with gr.Tabs(elem_id="stage step",default=0):
                            with gr.Tab("Stage 1",elem_id='stage_1') as stage1:
                                project_dir = gr.Textbox(label='Project directory', lines=1)
                                original_movie_path = gr.Textbox(label='Original Movie Path', lines=1)
                                selected_frame_scale_tab = gr.State(value=0)

                                with gr.Accordion("Decode Frame Options",open=False):
                                    with gr.Tabs(elem_id="frame_width_height",default=1):
                                        with gr.Tab("Frame resize by size",elem_id='frame_wh_1') as frame_size:
                                            frame_width = gr.Number(value=-1, label="Frame Width", precision=0, interactive=True)
                                            frame_height = gr.Number(value=-1, label="Frame Height", precision=0, interactive=True)
                                        with gr.Tab("Frame resize by scale",elem_id='frame_wh_2') as frame_scale:
                                            frame_wh_scale = gr.Slider(minimum=0.1, maximum=2.0, step=0.1, label='Width and height scaling', value=1.0)
                                    frame_size.select(fn=lambda: 0, inputs=[], outputs=[selected_frame_scale_tab])
                                    frame_scale.select(fn=lambda: 1, inputs=[], outputs=[selected_frame_scale_tab])

                                with gr.Row(elem_id="frame_options"):
                                    use_specific_fps = gr.Checkbox(label="Decode using a specific frame rate", value=True)
                                    decoder_frames_fps = gr.Slider(minimum=1, maximum=240, step=1, label='Number of decoded sequence frames', value=12)
                                with gr.Row(elem_id="sequence frame"):
                                    gr.Button("Increase the number of keyframes", elem_id="increase_key_frames", variant='primary')
                                    gr.Button("Add last frame to keyframes", elem_id="add_last_frame", variant='primary')

                                run_stage_1 = gr.Button("Run stage 1", elem_id="run_1", variant='primary')
                                args_stage1 = dict(
                                    fn=wrap_gradio_gpu_call(ebsynth_utility_process),
                                    inputs=[
                                        project_dir,
                                        original_movie_path,

                                        selected_frame_scale_tab,

                                        frame_width,
                                        frame_height,

                                        frame_wh_scale,

                                        use_specific_fps,
                                        decoder_frames_fps
                                    ],
                                    outputs=[
                                        debug_info,
                                        html_info,
                                    ],
                                    show_progress=False,
                                )
                                run_stage_1.click(**args_stage1)

                            with gr.Tab("Stage 2",elem_id='stage_2') as stage2:
                                gr.HTML(value="<p style='margin-bottom: 0.7em'>\
                                            Mask sequence frames.<br>\
                                            Cutting out the characters or the subject you want can reduce background flicker. Of course, this step is optional.<br>\
                                            Use SegmentAnything or whatever you like to mask all images in the video_frame folder.<br>\
                                        </p>")
                            with gr.Tab("Stage 3",elem_id='stage_3') as stage3:
                                key_add_last_frame = gr.Checkbox(label="Add last frame to keyframes", value=True)
                            with gr.Tab("Stage 4",elem_id='stage_4') as stage4:
                                auto_scale = gr.Checkbox(label="Auto scale,If Auto Scale is open, click generate button will scale video_key/video_key_output/video_frame/video_mask all files to original video size", value=True)
                                scale_dir = gr.Textbox(label='Need to scale directory', lines=1)
                                scale_selected_frame_scale_tab = gr.State(value=0)
                                with gr.Tabs(elem_id="scale_frame_width_height",default=1):
                                    with gr.Tab("Frame resize by size",elem_id='scale_frame_wh_1') as scale_frame_size:
                                        scale_frame_width = gr.Number(value=-1, label="Frame Width", precision=0, interactive=True)
                                        scale_frame_height = gr.Number(value=-1, label="Frame Height", precision=0, interactive=True)
                                    with gr.Tab("Frame resize by scale",elem_id='scale_frame_wh_2') as scale_frame_scale:
                                        scale_frame_wh_scale = gr.Slider(minimum=0.1, maximum=2.0, step=0.1, label='Width and height scaling', value=1.0)

                                scale_frame_size.select(fn=lambda: 0, inputs=[], outputs=[selected_frame_scale_tab])
                                scale_frame_scale.select(fn=lambda: 1, inputs=[], outputs=[selected_frame_scale_tab])

                            with gr.Tab("Stage 5",elem_id='stage_5') as stage5:
                                key_add_last_frame = gr.Checkbox(label="Add last frame to keyframes", value=True)
                            with gr.Tab("Stage 6",elem_id='stage_6') as stage6:
                                key_add_last_frame = gr.Checkbox(label="Add last frame to keyframes", value=True)
                            with gr.Tab("Stage 7",elem_id='stage_7') as stage7:
                                output_fps = gr.Number(value=-1, label="Output Video FPS", precision=0, interactive=True)
                                blend_rate = gr.Slider(minimum=0.0, maximum=1.0, step=0.01, label='Crossfade blend rate', value=1.0)
                                export_type = gr.Dropdown(choices=["mp4","webm","gif","rawvideo"], value="mp4" ,label="Export type")

                       



            ebs_args = dict(
                fn=wrap_gradio_gpu_call(ebsynth_utility_process),
                inputs=[
                    0,

                    project_dir,
                    original_movie_path,

                    key_add_last_frame,
                    selected_frame_scale_tab,

                    frame_width,
                    frame_height,

                    frame_wh_scale,

                    auto_scale,
                    scale_dir,
                    scale_selected_frame_scale_tab,
                    scale_frame_width,
                    scale_frame_height,
                    scale_frame_wh_scale,

                    output_fps,
                    blend_rate,
                    export_type,
                ],
                outputs=[
                    debug_info,
                    html_info,
                ],
                show_progress=False,
            )
            # generate_btn.click(**ebs_args)
           
    return (ebs_interface, "Ebsynth kit", "ebs_interface"),



script_callbacks.on_ui_tabs(on_ui_tabs)

