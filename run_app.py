import subprocess
import sys
import os

def main():
    # Determine the path to the Python executable in the virtual environment
    if os.name == 'nt':  # Windows
        python_exe = os.path.join("popu_agent_env", "Scripts", "python.exe")
    else:  # Unix/Linux/Mac
        python_exe = os.path.join("popu_agent_env", "bin", "python")
    
    # Check if the virtual environment exists
    if not os.path.exists(python_exe):
        print("Virtual environment not found. Please run setup_env.py first.")
        return 1
    
    # Run the main application using the virtual environment's Python
    try:
        print("Starting the Popu Agent application...")
        result = subprocess.run([python_exe, "main.py"], check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error running the application: {e}")
        return e.returncode
    except FileNotFoundError:
        print("Python executable not found in virtual environment.")
        return 1
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)