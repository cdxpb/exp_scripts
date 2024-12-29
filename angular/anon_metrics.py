import os
import torch
import numpy as np
import csv
from scipy.spatial.transform import Rotation as R
import argparse
import json

# Load SMPL data from .pt files
def load_smpl_data(pt_dir, method):
    smpl_data = {}
    if method=='gvhmr':
        
        for file in os.listdir(pt_dir):
            if file.endswith('.pt'):
                file_path = os.path.join(pt_dir, file)
                data = torch.load(file_path)
                smpl_data[file[:-3]] = {
                    'transl': data['smpl_params_global']['transl'],
                    'body_pose': data['smpl_params_global']['body_pose'],
                }
    else:
        for file in os.listdir(pt_dir):
            if file.endswith('.json'):
                file_path = os.path.join(pt_dir, file)
                with open(file_path, 'r') as _file:
                # file_path = os.path.join(pt_dir, file)
                    data = json.load(_file)
                    
                    smplxdata = data['annotations']
                    body_pose = []
                    transl = []
                        
                    for a in smplxdata:
                        body_pose.append(a['smplx_params']['pose_body'])
                        transl.append(a['smplx_params']['trans'])
                        
                    smpl_data[file[:-5]] = {
                        'transl': transl,
                        'body_pose': body_pose,
                    }
                
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
    # Ensure body_pose has the correct shape (N, 3) where N is the number of frames or rotations
    body_pose = np.array(body_pose)
    
    if body_pose.ndim == 2 and body_pose.shape[1] != 3:
        # If body_pose contains joint rotations, extract them correctly
        # For example, consider using just the root rotation (first 3 values) or the specific joint you need
        body_pose = body_pose[:, :3]  # Adjust to get the first 3 elements for each frame (if needed)
    
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

# Detect anomalies based on thresholds
def detect_anomalies(metrics, thresholds):
    anomalies = {
        'root_velocity': metrics['root_mean_velocity'] > thresholds['max_velocity'],
        'root_acceleration': metrics['root_mean_acceleration'] > thresholds['max_acceleration'],
        'angular_velocity': metrics['body_mean_angular_velocity'] > thresholds['max_angular_velocity'],
        'angular_acceleration': metrics['body_mean_angular_acceleration'] > thresholds['max_angular_acceleration']
    }
    return anomalies

# Save results to a CSV file
def save_to_csv(results, output_csv, subset):
    with open(output_csv, mode='w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow([
            'video_id',
            'root_mean_velocity', 'root_mean_acceleration',
            'body_mean_angular_velocity', 'body_mean_angular_acceleration',
        ])

        # Write rows
        for result in results:
            writer.writerow([
                result['video_id'],
                result['metrics']['root_mean_velocity'],
                result['metrics']['root_mean_acceleration'],
                result['metrics']['body_mean_angular_velocity'],
                result['metrics']['body_mean_angular_acceleration'],
            ])
        
    with open(subset+'_anomalies.csv', mode='w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow([
            'video_id',
            'root_mean_velocity', 'root_mean_acceleration',
            'body_mean_angular_velocity', 'body_mean_angular_acceleration',
        ])
        
        for result in results:
            if any(result['anomalies'].values()):  # Check if any anomaly is True
                writer.writerow([
                    result['video_id'],
                    result['metrics']['root_mean_velocity'],
                    result['metrics']['root_mean_acceleration'],
                    result['metrics']['body_mean_angular_velocity'],
                    result['metrics']['body_mean_angular_acceleration'],
                ])


# Main function
def main(pt_dir, output_csv):
    method='gvhmr'
    subset=''
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--method', dest='method', type=str, help='gvhmr or motionx')
    parser.add_argument('--directory', dest='directory', type=str, help='data directory of the chosen method')
    parser.add_argument('--subset', dest='subset', type=str,)

    args = parser.parse_args()

    
    if(args.method):
        method=args.method
        if(method == 'motionx'):
            pt_dir = './motionxdata/motion/mesh_recovery/global_motion'
    
    # if(args.directory):
    #     pt_dir = args.directory
        
    if(args.subset):
        subset = args.subset
        pt_dir = pt_dir + '/' + subset
        
    thresholds = {
        'max_velocity': 0.085,               # Threshold for root mean velocity
        'max_acceleration': 0.06,         # Threshold for root mean acceleration
        'max_angular_velocity': 0.085,      # Threshold for body angular velocity
        'max_angular_acceleration': 0.06   # Threshold for body angular acceleration
    }
    
    smpl_data = load_smpl_data(pt_dir, method)
    results = []

    for video_id, data in smpl_data.items():
        
        #skip short videos, less than 90 frames
        if(len(data['transl'])<90):
            continue
        
        # Compute metrics
        root_mean_velocity, root_mean_acceleration = compute_root_metrics(data['transl'])
        body_mean_angular_velocity, body_mean_angular_acceleration = compute_body_pose_metrics(data['body_pose'])


        metrics = {
            'root_mean_velocity': root_mean_velocity,
            'root_mean_acceleration': root_mean_acceleration,
            'body_mean_angular_velocity': body_mean_angular_velocity,
            'body_mean_angular_acceleration': body_mean_angular_acceleration
        }

        # Detect anomalies
        anomalies = detect_anomalies(metrics, thresholds)

        # Store results
        results.append({
            'video_id': video_id,
            'metrics': metrics,
            'anomalies': anomalies
        })

    # Save results to CSV
    save_to_csv(results, './csvs/' + subset+'_'+output_csv, subset)

if __name__ == "__main__":
    pt_dir = "./"  # Directory containing .pt files
    output_csv = "output.csv"         # Path to save the CSV
    main(pt_dir, output_csv)
