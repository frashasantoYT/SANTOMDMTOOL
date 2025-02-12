import subprocess
import time

class RunKgActiveOS13Thread:
    def run(self):
        # Step 1: Install APKs
        self.install_apks()

        # Step 2: Run sy3 interactively
        self.run_Sys3_interactive()

    def install_apks(self):
        """Install required APKs before running sy3."""
        apk_commands = [
            ["adb", "install", "-i", "PrePackageInstaller", "a.apk"],
            ["adb", "install", "-i", "PrePackageInstaller", "santoapk1.apk"],
            ["adb", "shell", "am", "start", "-n", "com.sec.android.app.audiocoredebug/com.sec.android.app.audiocoredebug.MainActivity"]
        ]

        for command in apk_commands:
            try:
                print(f"Executing: {' '.join(command)}")
                result = subprocess.run(command, capture_output=True, text=True)
                print(result.stdout)
                if result.stderr:
                    print(f"Error: {result.stderr}")
            except Exception as e:
                print(f"Installation failed: {str(e)}")

    def run_Sys3_interactive(self):
        """Run sy3 interactively and execute subsequent commands."""
        try:
            # Start adb shell
            adb_shell = subprocess.Popen(
                ["adb", "shell"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Step 1: Run `sy3`
            adb_shell.stdin.write("/data/local/tmp/sy3\n")
            adb_shell.stdin.flush()
            print("Running sy3...")

            # Give time for `sy3` to start
            time.sleep(3)

            # Step 2: Send interactive commands after `sy3` starts
            interactive_commands = [
                "service call knoxguard_service 37",
                "service call knoxguard_service 41 s16 'null'",
                "service call knoxguard_service 40",
            ]

            for command in interactive_commands:
                print(f"Executing: {command}")
                adb_shell.stdin.write(command + "\n")
                adb_shell.stdin.flush()
                time.sleep(2)  # Allow time for execution

            # Step 3: Exit the adb shell
            adb_shell.stdin.write("exit\n")
            adb_shell.stdin.flush()
            print("Exiting adb shell...")

            adb_shell.wait()

        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    runner = RunKgActiveOS13Thread()
    runner.run()
