import subprocess
import time

def execute_interactive_commands():
    # Launch an ADB shell
    adb_shell = subprocess.Popen(
        ["adb", "shell"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Initial commands to prepare
    preparation_commands = [
        "chmod +x /data/local/tmp/sant1",
        "/data/local/tmp/sant1"
    ]

    # Commands to execute after entering the sant1 prompt
    interactive_commands = [
        "service call knoxguard_service 36",
        "service call knoxguard_service 40 s16 'null'",
        "service call knoxguard_service 39"
    ]

    # Execute preparation commands
    for command in preparation_commands:
        print(f"Executing: {command}")
        adb_shell.stdin.write(command + "\n")  # Send the command
        adb_shell.stdin.flush()
        time.sleep(2)  # Wait briefly to allow the command to execute

    # Simulate interactive commands after sant1 prompt
    print("Entering sant1 interactive mode...")
    for command in interactive_commands:
        print(f"Sending command: {command}")
        adb_shell.stdin.write(command + "\n")  # Send the interactive command
        adb_shell.stdin.flush()
        time.sleep(2)  # Adjust delay as needed for stability

    # Exit the shell after completing commands
    adb_shell.stdin.write("exit\n")
    adb_shell.stdin.flush()
    adb_shell.wait()

    # Capture and display output (if any)
    stdout, stderr = adb_shell.communicate()
    print("STDOUT:", stdout)
    print("STDERR:", stderr)

if __name__ == "__main__":
    execute_interactive_commands()
