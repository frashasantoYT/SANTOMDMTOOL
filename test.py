import subprocess
import queue
from threading import Thread
import time


def run_sant1_interactive():
    def enqueue_output(stream, output_queue):
        for line in iter(stream.readline, ''):
            output_queue.put(line)
        stream.close()

    try:
        adb_shell = subprocess.Popen(
            ["adb", "shell"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout_queue = queue.Queue()
        stderr_queue = queue.Queue()

        stdout_thread = Thread(target=enqueue_output, args=(adb_shell.stdout, stdout_queue))
        stderr_thread = Thread(target=enqueue_output, args=(adb_shell.stderr, stderr_queue))
        stdout_thread.start()
        stderr_thread.start()

        # Write the command to execute 'sant1'
        adb_shell.stdin.write("/data/local/tmp/sant1\n")
        adb_shell.stdin.flush()

        # Wait for the initialization prompt
        time.sleep(3)
        while not stdout_queue.empty():
            line = stdout_queue.get()
            print(f"Output: {line.strip()}")
            if "type quit to exit" in line:
                break

        # Commands to execute in the interactive shell
        interactive_commands = [
            ("Executing service call 36...", "service call knoxguard_service 36"),
            ("Executing service call 40 (bypass)...", "service call knoxguard_service 40 s16 'null'"),
            ("Executing service call 39 (finalizing)...", "service call knoxguard_service 39"),
            ("Exiting interactive mode...", "quit"),
        ]

        results = []  # To store output for each command

        for log, command in interactive_commands:
            print(log)
            adb_shell.stdin.write(command + "\n")
            adb_shell.stdin.flush()

            # Allow time for the command to execute and capture output
            time.sleep(2)

            # Collect output after each command
            command_output = []
            while not stdout_queue.empty():
                line = stdout_queue.get().strip()
                command_output.append(line)
                print(f"Command Output: {line}")

            results.append((command, "\n".join(command_output)))

        adb_shell.stdin.write("exit\n")
        adb_shell.stdin.flush()

        # Process remaining output
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)

        while not stdout_queue.empty():
            print(f"Final Output: {stdout_queue.get().strip()}")
        while not stderr_queue.empty():
            print(f"Error: {stderr_queue.get().strip()}")

        adb_shell.wait()

        # Return results for further use in the Qt application
        return results

    except Exception as e:
        print(f"Exception: {str(e)}")
        return []


# Example usage for integration
if __name__ == "__main__":
    command_results = run_sant1_interactive()
    for command, output in command_results:
        print(f"\nCommand: {command}")
        print(f"Output:\n{output}")
