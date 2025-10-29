#!/usr/bin/env python3
"""
Cleanup script to remove generated files
"""

import os
import shutil

def ask_yes_no(question):
    """Ask y/n question, default to 'n'"""
    while True:
        response = input(f"{question} (y/N): ").strip().lower()
        if response == '' or response == 'n':
            return False
        elif response == 'y':
            return True
        else:
            print("Please answer 'y' or 'n'")

def delete_files(file_list, description):
    """Delete list of files if they exist"""
    deleted = []
    for file in file_list:
        if os.path.exists(file):
            try:
                os.remove(file)
                deleted.append(file)
            except Exception as e:
                print(f"  Error deleting {file}: {e}")
    
    if deleted:
        print(f"  Deleted {len(deleted)} file(s)")
        for f in deleted:
            print(f"    - {f}")
    else:
        print(f"  No {description} files found")

def delete_directory(dir_path, description):
    """Delete directory if it exists"""
    if os.path.exists(dir_path):
        try:
            shutil.rmtree(dir_path)
            print(f"  Deleted directory: {dir_path}")
        except Exception as e:
            print(f"  Error deleting {dir_path}: {e}")
    else:
        print(f"  No {description} directory found")

def main():
    print("=" * 60)
    print("CLEANUP SCRIPT - Remove Generated Files")
    print("=" * 60)
    print("Default answer is 'N' (No) - just press Enter to skip\n")
    
    # SUMO network files
    if ask_yes_no("Delete SUMO network files?"):
        sumo_files = [
            'intersection.net.xml',
            'intersection.nod.xml',
            'intersection.edg.xml',
            'traffic.rou.xml',
            'traffic_dynamic.rou.xml',
            'traffic_incident.rou.xml',
            'tls_program.add.xml',
            'simulation.sumocfg'
        ]
        delete_files(sumo_files, "SUMO network")
    else:
        print("  Skipped SUMO network files")
    
    print()
    
    # Training logs
    if ask_yes_no("Delete training logs?"):
        delete_directory('logs', "training logs")
    else:
        print("  Skipped training logs")
    
    print()
    
    # Test logs
    if ask_yes_no("Delete test logs?"):
        delete_directory('test_logs', "test logs")
    else:
        print("  Skipped test logs")
    
    print()
    
    # Trained models
    if ask_yes_no("Delete trained models?"):
        delete_directory('models', "models")
    else:
        print("  Skipped trained models")
    
    print()
    
    # Analysis outputs
    if ask_yes_no("Delete analysis outputs (PNG, CSV)?"):
        analysis_files = [
            'training_analysis.png',
            'vehicle_distribution.png',
            'training_summary.csv'
        ]
        delete_files(analysis_files, "analysis output")
    else:
        print("  Skipped analysis outputs")
    
    print()
    
    # Python cache
    if ask_yes_no("Delete Python cache files?"):
        delete_directory('__pycache__', "Python cache")
        cache_files = [f for f in os.listdir('.') if f.endswith('.pyc')]
        if cache_files:
            delete_files(cache_files, "Python cache")
        else:
            print("  No Python cache files found")
    else:
        print("  Skipped Python cache files")
    
    print()
    print("=" * 60)
    print("Cleanup complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()