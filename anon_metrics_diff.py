import os
import torch
import numpy as np
import csv
from scipy.spatial.transform import Rotation as R
import argparse
import json

# Load SMPL data from .pt files
def load_smpl_data(pt_file):
    smpl_data = {}
    data = torch.load(pt_file)
    smpl_data['transl'] = data['smpl_params_global']['transl']
    smpl_data['body_pose'] = data['smpl_params_global']['body_pose']
    return smpl_data

# Compute root translation velocity and acceleration
def compute_root_metrics(transl):
    transl = np.array(transl)  # Convert to numpy array
    velocities = np.linalg.norm(transl[1:] - transl[:-1], axis=1)  # Frame-to-frame velocity
    accelerations = np.abs(velocities[1:] - velocities[:-1])  # Frame-to-frame acceleration
    
    mean_velocity = np.mean(velocities)
    mean_acceleration = np.mean(accelerations)
    
    return mean_velocity, mean_acceleration

# Compute body pose angular velocity and acceleration
def compute_body_pose_metrics(body_pose):
    body_pose = np.array(body_pose)
    if body_pose.ndim == 2 and body_pose.shape[1] != 3:
        body_pose = body_pose[:, :3]  # Adjust to get the first 3 elements for each frame

    rotations = R.from_rotvec(body_pose)  # Convert axis-angle to rotation matrices

    angular_velocities = []
    for i in range(1, len(rotations)):
        delta_rot = rotations[i] * rotations[i - 1].inv()  # Relative rotation between frames
        angular_velocity = delta_rot.magnitude()  # Magnitude of the relative rotation
        angular_velocities.append(angular_velocity)

    angular_velocities = np.array(angular_velocities)
    angular_accelerations = np.abs(np.diff(angular_velocities))  # Frame-to-frame acceleration

    mean_angular_velocity = np.mean(angular_velocities)
    mean_angular_acceleration = np.mean(angular_accelerations)

    return mean_angular_velocity, mean_angular_acceleration

# Main function to process CSV and calculate metrics
def process_csv(input_csv, root_dir):
    # Read the CSV into a list of rows
    with open(input_csv, mode='r') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
    
    # Calculate metrics for each row
    for row in rows:
        video_id = row['video_id']
        folder_path = os.path.join(root_dir, video_id)
        
        # Find the .pt file in the folder
        pt_file = None
        for file in os.listdir(folder_path):
            if file.endswith('.pt'):
                pt_file = os.path.join(folder_path, file)
                break
        
        if pt_file is None:
            print(f"Warning: No .pt file found for {video_id}. Skipping.")
            continue
        
        # Load SMPL data and compute metrics
        smpl_data = load_smpl_data(pt_file)
        root_mean_velocity, root_mean_acceleration = compute_root_metrics(smpl_data['transl'])
        body_mean_angular_velocity, body_mean_angular_acceleration = compute_body_pose_metrics(smpl_data['body_pose'])

        # Update row with new metrics (without overwriting existing columns)
        row['root_mean_velocity_new'] = root_mean_velocity
        row['root_mean_acceleration_new'] = root_mean_acceleration
        row['body_mean_angular_velocity_new'] = body_mean_angular_velocity
        row['body_mean_angular_acceleration_new'] = body_mean_angular_acceleration

    # Write the updated rows to a new CSV file with interleaved columns
    output_csv = input_csv.replace('.csv', '_diff.csv')
    with open(output_csv, mode='w', newline='') as file:
        # Interleave the columns: original column, new column
        fieldnames = []
        for field in reader.fieldnames:
            if field != 'video_id':  # Exclude video_id from interleaving
                fieldnames.append(field)
                fieldnames.append(f"{field}_new")
        fieldnames = ['video_id'] + fieldnames  # Add video_id at the beginning

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        # Write rows with interleaved columns
        for row in rows:
            interleaved_row = {'video_id': row['video_id']}
            for field in reader.fieldnames:
                if field != 'video_id':
                    interleaved_row[field] = row[field]
                    interleaved_row[f"{field}_new"] = row[f"{field}_new"]
            writer.writerow(interleaved_row)

# Main entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_csv', type=str, required=True, help="Input CSV file")
    parser.add_argument('--root_dir', type=str, required=True, help="Root directory containing the folders with .pt files")
    args = parser.parse_args()

    process_csv(args.input_csv, args.root_dir)
