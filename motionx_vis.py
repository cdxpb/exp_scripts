import argparse
from pathlib import Path
from tqdm import tqdm
from hmr4d.utils.pylogger import Log
import subprocess
import os


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--subset", type=str)
    parser.add_argument("-s", "--static_cam", action="store_true", help="If true, skip DPVO")
    args = parser.parse_args()

    folder = Path('./visjson/'+args.subset)

    # Run demo.py for each .mp4 file
    json_paths = sorted(list(folder.glob("*.json")))
    Log.info(f"Found {len(json_paths)} .json files in {folder}")
    
    for json_path in tqdm(json_paths):
        filename_no_ext = json_path.stem
        command = ["python", "./render_world_space_motion.py", "--filename", str(filename_no_ext)]
        if args.subset is not None:
            command += ["--subset", args.subset]

        Log.info(f"Running: {' '.join(command)}")
        subprocess.run(command, env=dict(os.environ), check=True)
