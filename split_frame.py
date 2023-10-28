import os
import shutil
import ebsynth_kit

def split_sequence_frames():

    project_dir, _, frame_path, frame_mask_path, frame_key_output, _ , = ebsynth_kit.project_args
    video_frame_path = frame_path  
    video_key_output_path = frame_key_output

    key_frames = sorted(os.listdir(video_key_output_path))
    key_frame_ids = [int(name.split('.')[0]) for name in key_frames]

    first_frame = os.listdir(video_frame_path)[0]
    ext = first_frame.split('.')[-1]
    if ext not in ['jpg', 'png', 'webp']:
        raise ValueError('Unsupported image format')

    max_key_frame_id = max(key_frame_ids)
    frame_files = sorted(os.listdir(video_frame_path))
    max_frame_id = int(frame_files[-1].split('.')[0])

    for i in range(len(key_frame_ids) - 1):
        frame_name = 'output-{:05d}'.format(key_frame_ids[i])
        frame_path = os.path.join(project_dir, frame_name)
        os.mkdir(frame_path, exist_ok=True)

        frame_dir = os.path.join(frame_path, 'frame')
        os.mkdir(frame_dir, exist_ok=True)

        ref_dir = os.path.join(frame_path, 'reference')
        os.mkdir(ref_dir, exist_ok=True)

        start_id = key_frame_ids[i] + 1
        end_id = key_frame_ids[i+1]
        for id in range(start_id, end_id):
            frame_file = '{:05d}.{}'.format(id, ext)
            src_frame = os.path.join(video_frame_path, frame_file)
            dst_frame = os.path.join(frame_dir, frame_file)
            shutil.copy(src_frame, dst_frame)

            if id <= (start_id + end_id) // 2:
                ref_file = '{:05d}.{}'.format(key_frame_ids[i], ext)
            else:
                ref_file = '{:05d}.{}'.format(key_frame_ids[i+1], ext)
            src_ref = os.path.join(video_key_output_path, ref_file)
            dst_ref = os.path.join(ref_dir, frame_file)
            shutil.copy(src_ref, dst_ref)

        key_start_ref = os.path.join(video_key_output_path, '{:05d}.{}'.format(key_frame_ids[i], ext))
        key_end_ref = os.path.join(video_key_output_path, '{:05d}.{}'.format(end_id, ext))
        key_start_src = os.path.join(frame_path, '{:05d}.{}'.format(key_frame_ids[i], ext))
        key_end_src = os.path.join(frame_path, '{:05d}.{}'.format(end_id, ext))
        shutil.copy(key_start_ref, key_start_src)
        shutil.copy(key_end_ref, key_end_src)


    if max_key_frame_id < max_frame_id:
        last_frame_name = 'output-{}'.format(max_key_frame_id)
        last_frame_path = os.path.join(output_path, last_frame_name)
        os.mkdir(last_frame_path)

        frame_dir = os.path.join(last_frame_path, 'frame')
        os.mkdir(frame_dir)

        ref_dir = os.path.join(last_frame_path, 'reference')
        os.mkdir(ref_dir)

        for id in range(max_key_frame_id+1, max_frame_id+1):
            frame_file = '{:05d}.{}'.format(id, ext)
            src_frame = os.path.join(video_frame_path, frame_file)
            dst_frame = os.path.join(frame_dir, frame_file)
            shutil.copy(src_frame, dst_frame)

            ref_file = '{:05d}.{}'.format(max_key_frame_id, ext)
            src_ref = os.path.join(video_key_output_path, ref_file)
            dst_ref = os.path.join(ref_dir, frame_file)
            shutil.copy(src_ref, dst_ref)

    print('Done!')