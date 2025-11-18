import subprocess
import sys
import os
import shutil

def run_command(command):
    """Run a command and stream its output"""
    print(f"Running: {command}")
    try:
        # Use shell=False to avoid interference from batch scripts
        result = subprocess.run(command, shell=False, check=True, text=True, 
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(e.output)
        return False
    except FileNotFoundError:
        print(f"Command not found: {command}")
        return False

def main():
    print("Setting up environment with uv...")
    
    # Remove existing virtual environment if it exists
    if os.path.exists("popu_agent_env"):
        print("Removing existing virtual environment...")
        shutil.rmtree("popu_agent_env")
    
    # Create virtual environment with uv
    try:
        result = subprocess.run([sys.executable, "-m", "uv", "venv", "popu_agent_env"], 
                              check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(result.stdout)
        print("Virtual environment created successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtual environment: {e.output}")
        return False
    except FileNotFoundError:
        print("uv not found. Please install uv with 'pip install uv'")
        return False
    
    # Ensure pip is installed in the virtual environment
    try:
        if os.name == 'nt':  # Windows
            python_exe = os.path.join("popu_agent_env", "Scripts", "python.exe")
        else:  # Unix/Linux/Mac
            python_exe = os.path.join("popu_agent_env", "bin", "python")
        
        # Check if python exists
        if not os.path.exists(python_exe):
            print(f"Python executable not found at {python_exe}")
            return False
            
        # Ensure pip is installed
        result = subprocess.run([python_exe, "-m", "ensurepip", "--upgrade"], 
                              check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(result.stdout)
        print("Pip installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install pip: {e.output}")
        return False
    except FileNotFoundError:
        print("Python not found in virtual environment.")
        return False
    
    # Install requirements using python -m pip
    try:
        if os.name == 'nt':  # Windows
            python_exe = os.path.join("popu_agent_env", "Scripts", "python.exe")
        else:  # Unix/Linux/Mac
            python_exe = os.path.join("popu_agent_env", "bin", "python")
        
        # Install requirements using python -m pip
        result = subprocess.run([python_exe, "-m", "pip", "install", "-r", "requirements.txt"], 
                              check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(result.stdout)
        print("Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install requirements: {e.output}")
        return False
    except FileNotFoundError:
        print("Python not found in virtual environment.")
        return False
    
    print("\nSetup complete!")
    print(f"Virtual environment created at: popu_agent_env")
    print(f"To activate the environment, run:")
    if os.name == 'nt':  # Windows
        print(f"  popu_agent_env\\Scripts\\activate.bat")
    else:  # Unix/Linux/Mac
        print(f"  source popu_agent_env/bin/activate")
    print(f"\nTo run the application after activation:")
    print(f"  python main.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)