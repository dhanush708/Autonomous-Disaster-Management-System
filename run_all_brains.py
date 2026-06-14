import os
import sys
import subprocess
import time

# List of brain names to run
BRAINS = [
    ("landslide", "Landslide Brain"),
    ("earthquake", "Earthquake Brain"),
    ("cloudburst", "Cloudburst Brain"),
    ("forest_fire", "Forest Fire Brain")
]

def launch_brains():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    brains_dir = os.path.join(script_dir, "brains")

    print("\n" + "=" * 54)
    print("         LAUNCHING DISASTER MONITORING BRAINS")
    print("=" * 54 + "\n")

    for filename, display_name in BRAINS:
        print(f"Starting {display_name}...")
        
        # Build path to brain python script
        brain_script = os.path.join(brains_dir, f"{filename}_brain.py")
        
        # Verify file exists
        if not os.path.exists(brain_script):
            print(f"Error: Could not find script at {brain_script}")
            continue

        # Build command: 'start cmd /k' runs it in a separate Command Prompt window on Windows
        # and keeps the window open so logs/inputs can be viewed.
        cmd = f'start cmd /k "{sys.executable} \\"{brain_script}\\""'
        
        try:
            subprocess.Popen(cmd, shell=True)
            time.sleep(0.5)  # Slight delay to ensure terminal window registration order
        except Exception as e:
            print(f"Failed to launch {display_name}: {e}")

    print("\n" + "=" * 54)
    print("  All Disaster Brains Started Successfully")
    print("=" * 54 + "\n")

if __name__ == "__main__":
    # Ensure this is executed on Windows
    if os.name != 'nt':
        print("This launcher is pre-configured for Windows OS command shells.")
        print("To run on Linux/macOS, use: python brains/<name>_brain.py")
        sys.exit(1)
        
    launch_brains()
