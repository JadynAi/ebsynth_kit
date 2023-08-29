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



