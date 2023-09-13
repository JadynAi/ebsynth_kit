# ebsynth_kit

## Overview
#### AUTOMATIC1111 UI extension for creating videos using img2img and ebsynth.

This plugin was made on the basis of [Ebsynth utility](https://github.com/s9roll7/ebsynth_utility), simplifying some of the processes.

## Workflows

There are a total of seven steps, of which step 2/3/5 does not need to be operated in this plugin

#### step1/step1.1

Decode the input video, decode sequence frames into video_frame folders, decode keyframes into video_key folders, and create video_mask and video_key_output folders.
Step1.1 is an advanced version of step1, optional or not. This step is mainly to compensate for the possible defect of step 1, that is, the number of keyframes is too small. Step 1.1 will increase the number of keyframes to avoid tearing and crashing during subsequent EBSYNTH processing.

#### step2

Mask sequence frames.
Use SegmentAnything or whatever you like to mask all images in the video_frame folder.

#### step3

img2img keyframes.It is recommended to use multi frame scripts to img2img.I want you to select the output directory as a video_key_output under the project directory.
It is highly recommended to use this plugin to generate keyframed pictures [sequence toolkit](https://github.com/OedoSoldier/sd-webui-image-sequence-toolkit)

#### step4 

The options bar on the left provides configuration options. This is an optional step. Before compositing the video, consider whether to enlarge or reduce the frame size based on personal circumstances.

#### step5

This part of the code comes from ebsynt utility, which generates ebs files based on the video_key folder and video_frame folder.

#### step6

Install ebsynth software, open the ebs file directly, and then run all

#### step7

The ebsynth software will generate the corresponding converted frame folder in the project directory, starting with output. This step is to synthesize the converted frames into a video.



