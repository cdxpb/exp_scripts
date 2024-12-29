import os
import shutil
import pandas as pd
import argparse

def create_directory(directory):
    """Create directory if it does not exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def copy_files(csv_file, input_folder, output_folder, exte):
    # Ensure input and output directories exist
    create_directory(output_folder)
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Iterate over each row in the CSV
    for _, row in df.iterrows():
        video_id = row['video_id']
        
        # Construct the input file path
        input_file = os.path.join(input_folder, f"{video_id}.{exte}")  # Assuming the file extension is .mp4, change it if needed
        
        # Check if the file exists
        if os.path.exists(input_file):
            # Construct the output file path
            output_file = os.path.join(output_folder, f"{video_id}.{exte}")
            
            # Copy the file from input folder to output folder
            shutil.copy(input_file, output_file)
            print(f"Copied {input_file} to {output_file}")
        else:
            print(f"File {input_file} does not exist in the input folder")

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Copy files listed in a CSV file")
    # parser.add_argument("csv_file", type=str, help="Path to the CSV file containing the video IDs")
    parser.add_argument("subset", type=str, help="Subset")
    # parser.add_argument("output_folder", type=str, help="Path to the output folder to copy files to")
    
    # Parse arguments
    args = parser.parse_args()
    videos_fol = "./motionxdata/videos/" + args.subset
    motion_fol = "./motionxdata/motion/mesh_recovery/global_motion/" + args.subset

    output_vid_fol =  './copied/' + args.subset
    output_vis_fol =  './visjson/' + args.subset
    # Call the function to copy files
    copy_files("./csvs/"+args.subset+"_anomalies.csv", videos_fol, output_vid_fol, 'mp4')
    copy_files("./csvs/"+args.subset+"_anomalies.csv", motion_fol, output_vis_fol, 'json')

if __name__ == "__main__":
    main()
