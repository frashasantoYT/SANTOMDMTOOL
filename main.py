from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QGridLayout, QLabel,
    QPushButton, QTextEdit, QHBoxLayout, QFileDialog
)
import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from PyQt5.QtWidgets import (
    QDialog, QLabel, QVBoxLayout
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import subprocess
import sys
import qrcode
from PIL import Image, ImageQt
import random
from PyQt5.QtGui import QPixmap, QFont, QImage
from io import BytesIO  
from PyQt5.QtCore import QByteArray
import sys
import json
import qrcode
import random
from PIL import Image
from io import BytesIO
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget, QGridLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QInputDialog
import threading
import queue
import os
import json
import time
from threading import Thread
import queue


class RunInteractiveThread(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def enqueue_output(self, stream, queue):
        for line in iter(stream.readline, ''):
            queue.put(line)
        stream.close()

    def run(self):
        self.run_sant1_interactive()

    def run_sant1_interactive(self):
        """Run sant1 interactively and execute subsequent commands."""
       
        try:
            # Start the adb shell subprocess
            adb_shell = subprocess.Popen(
                ["adb", "shell"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout_queue = queue.Queue()
            stderr_queue = queue.Queue()

            stdout_thread = Thread(target=self.enqueue_output, args=(adb_shell.stdout, stdout_queue))
            stderr_thread = Thread(target=self.enqueue_output, args=(adb_shell.stderr, stderr_queue))
            stdout_thread.start()
            stderr_thread.start()

            # Write the command to execute 'sant1'
            adb_shell.stdin.write("/data/local/tmp/sant1\n")
            adb_shell.stdin.flush()
          

            # Wait for initialization
            time.sleep(5)

            # Define interactive commands
            interactive_commands = [
                ("Executing service call 36...", '"service call knoxguard_service 36"'),
                ("Executing service call 40 (bypass)...", '"service call knoxguard_service 40 s16 \'null\'"'),
                ("Executing service call 39 (finalizing)...", '"service call knoxguard_service 39"'),
                ("Exiting interactive mode...", "exit"),
            ]

            # Execute each interactive command
            for log, command in interactive_commands:
               
                adb_shell.stdin.write(command + "\n")
                adb_shell.stdin.flush()
                time.sleep(2)

            # Exit the adb shell
            adb_shell.stdin.write("exit\n")
            adb_shell.stdin.flush()

            # Process remaining output
            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)

            while not stdout_queue.empty():
                self.parent.log_signal.emit(f"<span style='color:green;'>STDOUT: {stdout_queue.get()}</span>")
            while not stderr_queue.empty():
                self.parent.log_signal.emit(f"<span style='color:red;'>STDERR: {stderr_queue.get()}</span>")

            adb_shell.wait()

        except Exception as e:
            print(f'{str(e)}')

        # Once the interactive portion is complete, run the remaining commands
        self.run_remaining_commands()

    def run_remaining_commands(self):
        """Run commands after sant1 interactive mode."""
        commands = [
            ("Checking KG lock state (knox.kg.state)...", "adb shell getprop knox.kg.state"),
            ("Checking KG lock state (kg.knox.state)...", "adb shell getprop kg.knox.state"),
            ("Removing temporary files...", "adb shell rm /data/local/tmp/*.*"),
            ("Removing 'sant1' file...", "adb shell rm -rf /data/local/tmp/sant1"),
            ("Stopping FOTA agent service...", "adb shell am force-stop --user 0 com.sdet.fotaagent"),
            ("Uninstalling FOTA agent app...", "adb shell pm uninstall --user 0 com.sdet.fotaagent"),
            ("Checking KG lock state one last time...", "adb shell getprop knox.kg.state"),
            ("Rebooting the device...", "adb reboot"),
        ]

        # Start a new CommandThread for the remaining commands
        self.command_thread = CommandThread(commands=commands, delay=1.0)
        self.command_thread.log_signal.connect(self.parent.append_log)
        self.command_thread.finished.connect(self.parent.enable_buttons)
        self.command_thread.start()


class RunKgActiveOS13Thread(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def enqueue_output(self, stream, queue):
        for line in iter(stream.readline, ''):
            queue.put(line)
        stream.close()

    def run(self):
        self.run_Sys3_interactive()

    def run_Sys3_interactive(self):
        """Run sant1 interactively and execute subsequent commands."""
        try:
            # Start the adb shell subprocess
            adb_shell = subprocess.Popen(
                ["adb", "shell"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Queues to capture stdout and stderr asynchronously
            stdout_queue = queue.Queue()
            stderr_queue = queue.Queue()

            # Threads for reading stdout and stderr
            stdout_thread = Thread(target=self.enqueue_output, args=(adb_shell.stdout, stdout_queue))
            stderr_thread = Thread(target=self.enqueue_output, args=(adb_shell.stderr, stderr_queue))
            stdout_thread.start()
            stderr_thread.start()

            # Step 1: Run `sy3` to initialize
            adb_shell.stdin.write("/data/local/tmp/sys3\n")
            adb_shell.stdin.flush()

            # Wait for `sy3` to initialize
            time.sleep(5)

            # Step 2: Define the interactive commands
            interactive_commands = [
                ("Running SANTO kg Bypass tool...", "am start -n com.samsung.android.FactoryTestLauncher/com.samsung.android.FactoryTestLauncher.addons.Shell.ShellActivity"),
                ("Executing service call 36...", "service call knoxguard_service 37"),
                ("Executing service call 40 (bypass)...", "service call knoxguard_service 41 s16 'null'"),
                ("Executing service call 39 (finalizing)...", "service call knoxguard_service 40"),
            ]

            # Step 3: Execute the commands in the adb shell
            for log, command in interactive_commands:
               
                adb_shell.stdin.write(command + "\n")
                adb_shell.stdin.flush()
                time.sleep(2)  # Add a delay to ensure the command processes correctly

            # Step 4: Exit the adb shell
            adb_shell.stdin.write("exit\n")
            adb_shell.stdin.flush()
          

            # Wait for threads to finish processing remaining output
            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)

            # Log any remaining output
            while not stdout_queue.empty():
                self.parent.log_signal.emit(f"<span style='color:green;'>STDOUT: {stdout_queue.get()}</span>")
            while not stderr_queue.empty():
                self.parent.log_signal.emit(f"<span style='color:green;'>STDOUT: {stdout_queue.get()}</span>")

            adb_shell.wait()

        except Exception as e:
            print(f"<span style='color:red;'>Error: {str(e)}</span>")

        # Step 5: Once the interactive portion is complete, run the remaining commands
        self.run_remaining_commands()

    def run_remaining_commands(self):
        """Run commands after sant1 interactive mode."""
        commands = [
            ("Checking KG lock state (knox.kg.state)...", "adb shell getprop knox.kg.state"),
            ("Removing 'sant1' file...", "adb shell rm -rf /data/local/tmp/sys3"),
            ("Rebooting the device...", "adb reboot"),
            
        ]

        # Start a new CommandThread for the remaining commands
        self.command_thread = CommandThread(commands=commands, delay=1.0)
        self.command_thread.log_signal.connect(self.parent.append_log)
        self.command_thread.finished.connect(self.parent.enable_buttons)
        self.command_thread.start()

class CommandThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, commands=None, delay=1.0, parent=None):
        super().__init__(parent)
        self.commands = commands if commands else []
        self.delay = delay  # Delay in seconds
        self.should_stop = False  # Flag to indicate if the thread should stop

    def run(self):
        # Execute each command in the provided list with a delay
        for description, command in self.commands:
            if self.should_stop:
                self.log_signal.emit("Thread was stopped.")
                break  # Exit the loop if should_stop is True

            self.log_signal.emit(description)  # Send log message
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()

            if process.returncode != 0:
                self.log_signal.emit(f"Error: {error.decode('utf-8').strip()}")
            else:
                self.log_signal.emit(f"{description} completed.")

            time.sleep(self.delay)

    def stop(self):
        """Set the flag to stop the thread"""
        self.should_stop = True
        


  
    

def random_color():
    """Generate a random RGB color."""
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

# Function to generate a QR code with random colors
def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=20,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Generate the QR code with a high-contrast color scheme
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((400, 400), Image.LANCZOS)
    
    # Display the generated QR code
    img.show()


class UnlockToolUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        
        # My Main Window Setting
        self.setWindowTitle("SANTO MDM TOOL VERSION 2.0.1 - Dark Mode")
        self.setGeometry(200, 200, 1000, 600)
        class UnlockToolUI:
        # Initialize button_widgets as an empty list (or appropriate data structure)
            self.button_widgets = []

      
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; color: white; }
            QLabel { color: white; font-size: 14px; }
            QPushButton { background-color: #3b3b3b; color: white; border: 1px solid #5a5a5a; padding: 10px; font-size: 12px; }
            QPushButton:hover { background-color: #5a5a5a; }
            QTextEdit { background-color: #1e1e1e; color: white; border: 1px solid #5a5a5a; }
            QTabWidget::pane { border: 1px solid #5a5a5a; }
            
            /* Tab styling */
            QTabBar::tab {
                background: #3a3a3a;
                color: #cccccc;
                padding: 10px;
                margin: 2px;
                font-size: 12px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 100px;
            }
            
            QTabBar::tab:selected {
                background-color: #4b8bed;  /* Bright color for selected tab */
                color: #ffffff;             /* White text on the selected tab */
                font-weight: bold;
            }
            
            QTabBar::tab:hover {
                background-color: #5a5a5a;  /* Slightly brighter on hover */
            }

            QTabBar::tab:!selected {
                background-color: #3b3b3b;  /* Darker shade for non-selected tabs */
                color: #cccccc;
            }
        """)


        # Font for the application
        self.general_font = QFont("Arial", 10)
        
        # Create the main layout
        main_layout = QHBoxLayout()
        
        # Create the tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_adb_tab(), "ADB")
        self.tabs.addTab(self.create_fastboot_tab(), "Fastboot")
        self.tabs.addTab(self.create_samsung_tab(), "Samsung")
        self.tabs.addTab(self.create_infinix_itel_tecno_tab(), "Infinix/iTel/Tecno")
        self.tabs.addTab(self.create_honor_tab(), "Honor")
        self.tabs.addTab(self.create_xiaomi_tab(), "Xiaomi")
        
        # Log area on the right side
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(self.general_font)
        self.log_area.setPlaceholderText("Logs will appear here...")

         # Footer text
        footer_label = QLabel("Developed by Frasha Santo. Contact us on WhatsApp 0793712942")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #ffcc00; font-size: 12px; margin-top: 10px;")
        
        # Add widgets to the main layout
        main_layout.addWidget(self.tabs, stretch=3)
        main_layout.addWidget(self.log_area, stretch=2)

        
        # Main container widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)


        # Command Thread for executing ADB commands
        self.command_thread = CommandThread()
        self.command_thread.log_signal.connect(self.append_log)

    

    def append_log(self, message):
        # Log formatting to match the color style you wanted
        if "Error" in message:
            self.log_area.append(f"<span style='color:red;'>{message}</span>")
        else:
            self.log_area.append(f"<span style='color:green;'>{message}</span>")
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def create_adb_tab(self):
        tab = QWidget()
        layout = QGridLayout()
        
        # Add buttons and connect each to its action
        buttons = [
            ("Read Info", self.read_device_info),
            ("List Devices", self.list_devices),
            ("Reboot Device", lambda: self.run_adb_command("reboot")),
            ("Reboot to Bootloader", lambda: self.run_adb_command("reboot download")),
            ("Reboot to Fastboot", lambda: self.run_adb_command("reboot fastboot")),
            ("Install APK", self.install_apk),
            ("Pull File from Device", self.pull_file_from_device)
        ]
        
        # Add buttons to the grid layout
        for i, (label, func) in enumerate(buttons):
            button = QPushButton(label)
            button.clicked.connect(func)
            layout.addWidget(button, i // 2, i % 2)  # 2 buttons per row

        tab.setLayout(layout)
        return tab

    def create_fastboot_tab(self):
        tab = QWidget()
        layout = QGridLayout()

      
        fastboot_buttons = [
            ("Read Fastboot info", self.read_fastboot_info),
            ("Unlock Bootloader", self.unlock_bootloader),
            ("Lock Bootloader", self.lock_bootloader),
            ("Flash Recovery", self.flash_recovery_with_selection),
            ("Flash System", self.flash_system_with_selection),
            ("Erase Cache", self.erase_cache),
            ("Erase User Data", self.erase_userdata),
            ("Boot Custom Image", self.boot_custom_image_with_selection),
            # ("Fastboot Devices", self.fastboot_devices),
        ]

        # Add buttons to the grid layout
        for i, (label, func) in enumerate(fastboot_buttons):
            button = QPushButton(label)
            button.clicked.connect(func)
            layout.addWidget(button, i // 2, i % 2)

        tab.setLayout(layout)
        return tab
    # def fastboot_devices(self):
    #     self.append_log("Listing Fastboot devices...")
    #     self.run_command("fastboot devices")

    def create_samsung_tab(self):
        tab = QWidget() 
        layout = QGridLayout() 

          # Add buttons and connect each to its action
        buttons = [
            ("Read Info", self.read_device_info),
            ("Generate QR code OS 12 - 14", self.generate_qr_code_dialog),
            ("Kg Locked to Active 01", self.KgLockToActive),
            ("Kg active os 13", self.KgActiveOs13),
            ("Remove Kg Os 14", self.remove_kg_os_14),
            ("Remove Kg OS 13",  self.removeKgOs13),
            ("Kg fix", self.kgFix),
            ("Bypass Knox Services", self.BypassKnoxServices),
             ("Disable Factory reset", self.disable_factory_reset1),

        ]

    
        
        # Add buttons to the grid layout
        for i, (label, func) in enumerate(buttons):
            button = QPushButton(label)
            button.clicked.connect(func)
            layout.addWidget(button, i // 2, i % 2)  

        tab.setLayout(layout)
        return tab
    
    def disable_buttons(self):
            for button in self.button_widgets:
                button.setDisabled(True)

    def enable_buttons(self):
        for button in self.button_widgets:
            button.setDisabled(False)
    
    def run_commands(self, commands, on_complete=None):
        self.command_thread = CommandThread(commands)
        self.command_thread.log_signal.connect(self.append_log)
        self.command_thread.finished.connect(lambda: self.on_commands_complete(on_complete))
        self.command_thread.start()

    def on_commands_complete(self, on_complete=None):
        self.enable_buttons()  # Re-enable buttons after completion
        if on_complete:
          on_complete()


    def generate_qr_code_dialog(self):
        """Generate QR code with specific data when the button is clicked."""
        data = '''{
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME": "com.skamdm.knox/com.skamdm.knox.AdminReceiver",
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM": "9HpyskSThzfZ1QB2t3VM9vC2SP3v71auDyScIbnvmB0=",
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION": "https://tdunlock.net/adb3.apk",
        "android.app.extra.PROVISIONING_SKIP_ENCRYPTION": true,
        "android.app.extra.PROVISIONING_LEAVE_ALL_SYSTEM_APPS_ENABLED": true,
        "android.app.extra.PROVISIONING_ADMIN_EXTRAS_BUNDLE": {}
    }'''
        generate_qr_code(data)

    def remove_kg_os_14(self):
        self.command_thread.stop()
        self.clear_log()
        self.disable_buttons
        commands = [

            ("Wait for device...", "adb wait-for-device"),
            # Blocking system update services
            ("Blocking System Update Services...", "adb shell pm uninstall --user 0 com.android.ons"),
            ("Blocking Dynamic System Updates...", "adb shell pm uninstall --user 0 com.android.dynsystem"),
            ("Blocking Samsung Update Center...", "adb shell pm uninstall --user 0 com.samsung.android.app.updatecenter"),
            ("Blocking Transsion System Update...", "adb shell pm uninstall --user 0 com.transsion.systemupdate"),
            ("Blocking WSSyncMLDM...", "adb shell pm uninstall --user 0 com.wssyncmldm"),
            
            # Blocking and disabling Knox components
            ("Blocking Knox Agent...", "adb shell pm uninstall --user 0 com.samsung.klmsagent"),
            ("Blocking Knox Cloud...", "adb shell pm uninstall --user 0 com.sec.enterprise.knox.cloudmdm.smdms"),
            ("Inactivating Knox...", "adb shell am set-inactive com.samsung.android.kgclient true"),
            ("Killing Knox...", "adb shell am kill com.samsung.android.kgclient"),
            
            # Removing and stopping Knox
            ("Removing KG...", "adb shell am crash com.samsung.android.kgclient"),
            ("Stopping Knox...", "adb shell am stop-app com.samsung.android.kgclient"),
            ("Stopping Knox Updates...", "adb shell pm uninstall-system-updates com.samsung.android.kgclient"),
            ("Disabling Knox...", "adb shell pm disable-user --user 0 com.samsung.android.kgclient"),
            ("Enabling KG...", "adb shell pm enable --user 0 com.samsung.android.kgclient"),
            
            # Bypassing Knox and MDM
            ("Bypassing Knox...", "adb shell pm uninstall-system-updates com.samsung.android.kgclient"),
            ("Bypassing KG App...", "adb shell pm suspend com.samsung.android.kgclient"),
            ("Removing MDM...", "adb shell pm uninstall --user 0 com.samsung.android.kgclient"),
            
            # Modifying permissions for KG client
            ("Killing Permissions...", "adb shell pm install-existing --restrict-permissions --user 0 com.samsung.android.kgclient"),
            
            # Managing app operations to limit background functionality
            ("Disabling Run in Background for KG...", "adb shell cmd appops set com.samsung.android.kgclient RUN_IN_BACKGROUND ignore"),
            ("Killing Run BG...", "adb shell cmd appops set com.samsung.android.kgclient RUN_IN_BACKGROUND deny"),
            ("Killing Any BG...", "adb shell cmd appops set com.samsung.android.kgclient RUN_ANY_IN_BACKGROUND deny"),
            ("Killing Wake Lock...", "adb shell cmd appops set com.samsung.android.kgclient WAKE_LOCK deny"),
            ("Killing Post Notification...", "adb shell cmd appops set com.samsung.android.kgclient POST_NOTIFICATION deny"),
            ("Killing Restricted Access...", "adb shell cmd appops set com.samsung.android.kgclient ACCESS_RESTRICTED_SETTINGS deny"),
            ("Killing Schedule Exact Alarm...", "adb shell cmd appops set com.samsung.android.kgclient SCHEDULE_EXACT_ALARM deny"),
            ("Killing Bluetooth Connect...", "adb shell cmd appops set com.samsung.android.kgclient BLUETOOTH_CONNECT deny"),
            ("Killing System Exempt Notifications...", "adb shell cmd appops set com.samsung.android.kgclient SYSTEM_EXEMPT_FROM_DISMISSIBLE_NOTIFICATIONS deny"),
            
            # Updating provisioning settings
            ("Setting Device Provisioned...", "adb shell settings put global device_provisioned 1"),
            ("Setting User Setup Complete...", "adb shell settings put secure user_setup_complete 1"),
            
            # Rebooting device
            ("Rebooting device...", "adb reboot"),
        ]
        
        # Display a starting log in orange
        self.log_area.append("<span style='color:white;'>Starting KG Removal Process...</span>")
        
        # Run the commands with delay between each
        self.run_commands(commands, on_complete=self.enable_buttons)

    def removeKgOs13(self): 
        self.command_thread.stop()
        self.clear_log()
        self.disable_buttons
        commands = [
            ("Waiting for device", "adb wait-for-device"),
            ("Bypass_1: Set inactive KG client...", "adb shell am set-inactive com.samsung.android.kgclient true"),
            ("Bypass_1: Crash KG client...", "adb shell am crash com.samsung.android.kgclient"),
            ("Bypass_1: Stop KG app...", "adb shell am stop-app com.samsung.android.kgclient"),
            ("Bypass_1: Uninstall KG system updates...", "adb shell pm uninstall-system-updates com.samsung.android.kgclient"),
            ("Bypass_1: Disable KG user...", "adb shell pm disable-user --user 0 com.samsung.android.kgclient"),
            ("Bypass_1: Uninstall KG client...", "adb shell pm uninstall --user 0 com.samsung.android.kgclient"),
            ("Bypass_1: Clear KG client data...", "adb shell pm clear com.samsung.android.kgclient"),
            ("Bypass_1: Enable KG client...", "adb shell pm enable --user 0 com.samsung.android.kgclient"),
            ("Bypass_1: Reinstall KG client with restricted permissions...", "adb shell pm install-existing --restrict-permissions --user 0 com.samsung.android.kgclient"),
            ("Bypass_1: Set RUN_IN_BACKGROUND ignore...", "adb shell cmd appops set com.samsung.android.kgclient RUN_IN_BACKGROUND ignore"),
            ("Bypass_2: Clear KG client data again...", "adb shell pm clear com.samsung.android.kgclient"),
            ("Bypass_2: Set RUN_IN_BACKGROUND ignore again...", "adb shell cmd appops set com.samsung.android.kgclient RUN_IN_BACKGROUND ignore"),
            ("Bypass_2: Suspend KG client...", "adb shell pm suspend com.samsung.android.kgclient"),
            ("Bypass_2: Set RUN_IN_BACKGROUND ignore again...", "adb shell cmd appops set com.samsung.android.kgclient RUN_IN_BACKGROUND ignore"),
            ("Bypass 2: running santo kg inactive" ,"adb shell am set-inactive com.samsung.android.kgclient true"), 
            ("Bypass_2: santo killing kgclient", "adb shell am kill com.samsung.android.kgclient"), 
            ("Bypass_2: santo crashing kgclient", "adb crash com.samsung.android.kgclient"), 
            ("Bypass_2: santo crashing kgclient", "adb clear com.samsung.android.kgclient"),
            ("Bypass_2: Set RUN_ANY_IN_BACKGROUND deny...", "adb shell cmd appops set com.samsung.android.kgclient RUN_IN_BACKGROUND deny"),
            ("Bypass_2: Set RUN_ANY_IN_BACKGROUND deny...", "adb shell cmd appops set com.samsung.android.kgclient RUN_ANY_IN_BACKGROUND deny"),
            ("Bypass_2: Deny WAKE_LOCK permissions...", "adb shell cmd appops set com.samsung.android.kgclient WAKE_LOCK deny"),
            ("Bypass_2: Deny POST_NOTIFICATION permissions...", "adb shell cmd appops set com.samsung.android.kgclient POST_NOTIFICATION deny"),
            ("Bypass_2: Deny POST_NOTIFICATION permissions...", "adb shell cmd appops set com.samsung.android.kgclient ACCESS_RESTRICTED_SETTINGS deny"),
            ("Bypass_2: Deny POST_NOTIFICATION permissions...", "adb shell cmd appops set com.samsung.android.kgclient SCHEDULE_EXACT_ALARM deny"),
            ("Bypass_2: Deny POST_NOTIFICATION permissions...", "adb shell cmd appops set com.samsung.android.kgclient BLUETOOTH_CONNECT deny"),
            ("Bypass_2: santo restoring system ui", "adb shell pm install-existing --restrict-permissions --user 0 com.android.systemui"), 
            ("Bypass_3: Uninstall Knox components...", "adb shell pm uninstall --user 0 com.samsung.klmsagent"),
            ("Bypass_3: Uninstall Knox push manager...", "adb shell pm uninstall --user 0 com.samsung.android.knox.pushmanager"),
            ("Bypass_3: Uninstall Google setup wizard...", "adb shell pm uninstall --user 0 com.google.android.setupwizard"),
            ("Bypass_3: Uninstall system updater components...", "adb shell pm uninstall --user 0 com.android.dynsystem"),
            ("Bypass_3: Uninstall Knox analytics uploader...", "adb shell pm uninstall --user 0 com.samsung.android.knox.analytics.uploader"),
            ("Finalizing...", 'timeout /t 2'),
            ("Wait for device...", "adb wait-for-device"),
            # Blocking system update services
            ("Blocking System Update Services...", "adb shell pm uninstall --user 0 com.android.ons"),
            ("Blocking Dynamic System Updates...", "adb shell pm uninstall --user 0 com.android.dynsystem"),
            ("Blocking Samsung Update Center...", "adb shell pm uninstall --user 0 com.samsung.android.app.updatecenter"),
            ("Blocking Transsion System Update...", "adb shell pm uninstall --user 0 com.transsion.systemupdate"),
            ("Blocking WSSyncMLDM...", "adb shell pm uninstall --user 0 com.wssyncmldm"),
            
            # Blocking and disabling Knox components
            ("Blocking Knox Agent...", "adb shell pm uninstall --user 0 com.samsung.klmsagent"),
            ("Blocking Knox Cloud...", "adb shell pm uninstall --user 0 com.sec.enterprise.knox.cloudmdm.smdms"),
            ("Inactivating Knox...", "adb shell am set-inactive com.samsung.android.kgclient true"),
            ("Killing Knox...", "adb shell am kill com.samsung.android.kgclient"),
            
            # Removing and stopping Knox
            ("Removing KG...", "adb shell am crash com.samsung.android.kgclient"),
            ("Stopping Knox...", "adb shell am stop-app com.samsung.android.kgclient"),
            ("Stopping Knox Updates...", "adb shell pm uninstall-system-updates com.samsung.android.kgclient"),
            ("Disabling Knox...", "adb shell pm disable-user --user 0 com.samsung.android.kgclient"),
            ("Enabling KG...", "adb shell pm enable --user 0 com.samsung.android.kgclient"),
            
            # Bypassing Knox and MDM
            ("Bypassing Knox...", "adb shell pm uninstall-system-updates com.samsung.android.kgclient"),
            ("Bypassing KG App...", "adb shell pm suspend com.samsung.android.kgclient"),
            ("Removing MDM...", "adb shell pm uninstall --user 0 com.samsung.android.kgclient"),
            
            # Modifying permissions for KG client
            ("Killing Permissions...", "adb shell pm install-existing --restrict-permissions --user 0 com.samsung.android.kgclient"),
            
            # Managing app operations to limit background functionality
            ("Disabling Run in Background for KG...", "adb shell cmd appops set com.samsung.android.kgclient RUN_IN_BACKGROUND ignore"),
            ("Killing Run BG...", "adb shell cmd appops set com.samsung.android.kgclient RUN_IN_BACKGROUND deny"),
            ("Killing Any BG...", "adb shell cmd appops set com.samsung.android.kgclient RUN_ANY_IN_BACKGROUND deny"),
            ("Killing Wake Lock...", "adb shell cmd appops set com.samsung.android.kgclient WAKE_LOCK deny"),
            ("Killing Post Notification...", "adb shell cmd appops set com.samsung.android.kgclient POST_NOTIFICATION deny"),
            ("Killing Restricted Access...", "adb shell cmd appops set com.samsung.android.kgclient ACCESS_RESTRICTED_SETTINGS deny"),
            ("Killing Schedule Exact Alarm...", "adb shell cmd appops set com.samsung.android.kgclient SCHEDULE_EXACT_ALARM deny"),
            ("Killing Bluetooth Connect...", "adb shell cmd appops set com.samsung.android.kgclient BLUETOOTH_CONNECT deny"),
            ("Killing System Exempt Notifications...", "adb shell cmd appops set com.samsung.android.kgclient SYSTEM_EXEMPT_FROM_DISMISSIBLE_NOTIFICATIONS deny"),
            
            # Updating provisioning settings
            ("Setting Device Provisioned...", "adb shell settings put global device_provisioned 1"),
            ("Setting User Setup Complete...", "adb shell settings put secure user_setup_complete 1"),
            
            # Rebooting device
            ("Rebooting device...", "adb reboot"),
        ]
        
        # Display a starting log in orange
        self.log_area.append("<span style='color:white;'>Starting KG OS 13 Removal Process...</span>")
        
        # Run the commands with delay between each
        self.run_commands(commands, on_complete=self.enable_buttons)

    def kgFix(self):
        self.command_thread.stop()
        self.clear_log()
        self.disable_buttons()

        # Define the commands
        commands = [
            ("Waiting for device", "adb wait-for-device"),
            
            # Blocking KLMS Agent
            ("Blocking KLMS Agent...", "adb shell pm uninstall --user 0 com.samsung.klmsagent"),
            
            # Blocking Knox Cloud
            ("Blocking Knox Cloud...", "adb shell pm uninstall --user 0 com.sec.enterprise.knox.cloudmdm.smdms"),
            # Deactivating Knox
            ("Deactivating Knox...", "adb shell am set-inactive com.samsung.android.kgclient true"),
            ("Killing Knox...", "adb shell am kill com.samsung.android.kgclient"),
            ("Removing Knox...", "adb shell am crash com.samsung.android.kgclient"),
            ("Stopping Knox...", "adb shell am stop-app com.samsung.android.kgclient"),
            ("Stopping Knox Updates...", "adb shell pm uninstall-system-updates com.samsung.android.kgclient"),
            ("Disabling Knox...", "adb shell pm disable-user --user 0 com.samsung.android.kgclient"),
            ("Activating KG...", "adb shell pm enable --user 0 com.samsung.android.kgclient"),
            ("Bypassing Knox...", "adb shell pm uninstall-system-updates com.samsung.android.kgclient"),
            ("Suspending KG App...", "adb shell pm suspend com.samsung.android.kgclient"),
            ("Removing MDM...", "adb shell pm uninstall --user 0 com.samsung.android.kgclient"),
            
            # Additional Knox client handling
            ("Killing Permissions...", "adb shell pm install-existing --restrict-permissions --user 0 com.samsung.android.kgclient"),
            ("Disabling RUN_IN_BACKGROUND...", "adb shell cmd appops set com.samsung.android.kgclient RUN_IN_BACKGROUND ignore"),
            ("Disabling RUN_ANY_IN_BACKGROUND...", "adb shell cmd appops set com.samsung.android.kgclient RUN_ANY_IN_BACKGROUND deny"),
            ("Disabling WAKE_LOCK...", "adb shell cmd appops set com.samsung.android.kgclient WAKE_LOCK deny"),
            ("Disabling POST_NOTIFICATION...", "adb shell cmd appops set com.samsung.android.kgclient POST_NOTIFICATION deny"),
            ("Disabling ACCESS_RESTRICTED_SETTINGS...", "adb shell cmd appops set com.samsung.android.kgclient ACCESS_RESTRICTED_SETTINGS deny"),
            ("Disabling SCHEDULE_EXACT_ALARM...", "adb shell cmd appops set com.samsung.android.kgclient SCHEDULE_EXACT_ALARM deny"),
            ("Disabling BLUETOOTH_CONNECT...", "adb shell cmd appops set com.samsung.android.kgclient BLUETOOTH_CONNECT deny"),
            ("Disabling SYSTEM_EXEMPT_FROM_DISMISSIBLE_NOTIFICATIONS...", "adb shell cmd appops set com.samsung.android.kgclient SYSTEM_EXEMPT_FROM_DISMISSIBLE_NOTIFICATIONS deny"),
            
            # Reinstalling System UI and handling Fota Agent
            ("Reinstalling System UI...", "adb shell pm install-existing --restrict-permissions --user 0 com.android.systemui"),
            ("Stopping Fota Agent...", "adb shell am force-stop --user 0 com.sdet.fotaagent"),
            ("Uninstalling Fota Agent...", "adb shell pm uninstall --user 0 com.sdet.fotaagent"),
            
            # Finalizing setup
            ("Finalizing Setup...", "adb shell settings put global device_provisioned 1"),
            ("Completing User Setup...", "adb shell settings put secure user_setup_complete 1"),
            
            # Rebooting device
            ("Rebooting Device...", "adb reboot"),
            ]


        # Execute commands in a separate thread
        def execute_commands():
            for description, command in commands:
                self.append_log(description)  # Log description
                process = self.run_command(command)  # Execute command
                if process:
                    self.append_log(process)  # Log command output if any
            self.append_log("KG fix operation completed.")
            self.enable_buttons()  # Re-enable buttons after completion

        # Start the command execution thread
        self.command_thread = threading.Thread(target=execute_commands, daemon=True)
        self.command_thread.start()




    def KgLockToActive(self):
        self.command_thread.stop()
        self.clear_log()
        self.disable_buttons()

        ag_apk_path = self.get_asset_path("santo1")

        # Define all commands with log messages for each step
        commands = [
            ("Waiting for ADB devices...", "adb devices"),
            ("Pushing santo1...", f'adb push "{self.get_asset_path("sant1")}" /data/local/tmp/sant1'),
            ("Setting executable permissions for 'sant1'...", "adb shell chmod +x /data/local/tmp/sant1"),
        ]

        # Log the start of the process
        self.log_area.append("<span style='color:white;'>Starting KG Lock to Active...</span>")

        # Start CommandThread with initial commands
        self.command_thread = CommandThread(commands=commands, delay=1.0)
        self.command_thread.log_signal.connect(self.append_log)

        # After the initial commands are completed, run the interactive thread
        self.command_thread.finished.connect(self.start_interactive_thread)
        self.command_thread.start()

    def start_interactive_thread(self):
        self.interactive_thread = RunInteractiveThread(self)
        self.interactive_thread.start()




    def BypassKnoxServices(self): 
        self.command_thread.stop()
        self.clear_log() 
        self.disable_buttons()


        commands = [ 
            ("Waiting for the device", "adb wait-for-device"),
            ("Uninstalling Knox Bridge", "adb shell pm uninstall -k --user 0 com.sec.knox.bridge"),
            ("Uninstalling Knox Switch", "adb shell pm uninstall -k --user 0 com.sec.knox.switchknoxll"),
            ("Uninstalling Knox Cloud MDM", "adb shell pm uninstall -k --user 0 com.sec.enterprise.knox.cloudmdm.smdms"),
            ("Uninstalling Knox Push Manager", "adb shell pm uninstall --user 0 com.samsung.android.knox.pushmanager"),
            ("Uninstalling Knox Switcher", "adb shell pm uninstall -k --user 0 com.sec.knox.switcher"),
            ("Uninstalling Samsung MDM", "adb shell pm uninstall -k --user 0 com.samsung.android.mdm"),
            ("Uninstalling Security Agent", "adb shell pm uninstall -k --user 0 com.samsung.android.securityResultTxtagent"),
            ("Stopping Knox Setup Wizard Client", "adb shell am force-stop com.sec.knox.knoxsetupwizardclient"),
            ("Uninstalling MDM SIM PIN Services", "adb shell pm uninstall --user 0 com.sec.enterprise.mdm.services.simpin"),
            ("Uninstalling Secure Folder", "adb shell pm uninstall --user 0 com.samsung.knox.securefolder"),
            ("Modifying system settings (OPTION_SCREEN_LOCK)", "adb shell settings put system OPTION_SCREEN_LOCK 1"),
            ("Modifying system settings (strong_protection)", "adb shell settings put system strong_protection 0"),
            ("Disabling KG Client", "adb shell pm disable-user --user 0 com.samsung.android.kgclient"),
            ("Disabling Knox Cloud MDM", "adb shell pm disable-user --user 0 com.sec.enterprise.knox.cloudmdm.smdms"),
            ("Disabling Samsung MDM", "adb shell pm disable-user --user 0 com.samsung.android.mdm"),
            ("Uninstalling Knox Container Core", "adb shell pm uninstall --user 0 com.samsung.android.knox.containercore"),
        ]

        # Log the start of the process
        self.log_area.append("<span style='color:white;'>Starting Bypass Knox Services process...</span>")

        # Execute the commands and re-enable buttons when complete
        self.run_commands(commands, on_complete=self.enable_buttons)

   


    def KgActiveOs13(self):
        self.command_thread.stop()
        self.clear_log()
        self.disable_buttons()

        # Define the paths for APKs using get_asset_path
        path_1_apk = self.get_asset_path("a.apk")
        path_2_apk = self.get_asset_path("santo1.apk")
        path_3_sys = self.get_asset_path("sys3")
            # Define all commands with log messages for each step
        commands = [
            # Install APKs on the device
            ("Installing santo1.apk on the device...", f'adb install -i PrePackageInstaller "{path_1_apk}"'),
            ("Installing santo2.apk on the device...", f'adb install -i PrePackageInstaller "{path_2_apk}"'),
            ("Running kg bypass tool", f'adb shell am start -n com.sec.android.app.audiocoredebug/com.sec.android.app.audiocoredebug.MainActivity'),
            ("Installing santo2 on the device.. wait", f' adb push "{path_3_sys}" /data/local/tmp/'),
            ("Preparing santo2...", f'adb shell chmod +x /data/local/tmp/sys3')
            
            

        ]

            # Start CommandThread with initial commands
        self.command_thread = CommandThread(commands=commands, delay=1.0)
        self.command_thread.log_signal.connect(self.append_log)
        
        self.command_thread.finished.connect(self.start_kgos13_thread)
        self.command_thread.start()

    def start_kgos13_thread(self):
        self.interactive_thread = RunKgActiveOS13Thread(self)
        self.interactive_thread.start()
        


        

      

        




    # def run_commands(self, commands, on_complete):
    #     """Executes a list of ADB commands with logging and error checking."""
    #     for description, command in commands:
    #         try:
    #             # Log the current step
    #             self.log_area.append(f"<span style='color:white;'>{description}</span>")
    #             output = subprocess.check_output(command, shell=True, text=True)
    #             if "No such file" in output:
    #                 # Log if a file was not found after pushing
    #                 self.log_area.append(f"<span style='color:red;'>Error: {description} - File not found on device.</span>")
    #             else:
    #                 # Log successful command output
    #                 self.log_area.append(f"<span style='color:green;'>{output}</span>")
    #         except subprocess.CalledProcessError as e:
    #             # Log command errors
    #             self.log_area.append(f"<span style='color:red;'>Error: {description} - {str(e)}</span>")
        
    #     # Enable buttons once all commands are complete
    #     on_complete()

    
    def disable_factory_reset(self):
        self.command_thread.stop()
        self.clear_log()
        self.disable_buttons()
        
        # Define the commands with log messages
        commands = [

            ("wait for adb device..", "adb wait-for-device"),
            
            # Install santo.apk
            (f"Installing santo.apk...", f'adb install "{self.get_asset_path('santo.apk')}"'),
            
            # Set as device administrator
            ("Setting santo.apk as a device administrator...", 
            "adb shell dpm set-device-owner com.afwsamples.testdpc/.DeviceAdminReceiver"),
            
            # Final instruction log for user
            ("Please open TestDPC app on your device and search for 'Disallow Factory Reset'.", "")
        ]
        
        # Run the commands and log each step
        self.run_commands(commands, on_complete=self.enable_buttons)
        self.append_log("'Disable Factory Reset' process completed.")


    def disable_factory_reset1(self):
        self.command_thread.stop()
        self.clear_log()
        self.disable_buttons()

        # Define the sequence of commands and corresponding log messages
        commands = [
            # Check for connected devices
            ("Waiting for ADB devices...", "adb wait-for-device"),

            # Check if device is unauthorized
            ("Checking device authorization...", "adb devices"),
            
            # Install APK
            ("Installing santo.apk...", f'adb install "{self.get_asset_path("dis.apk")}"'),

            # Set as device administrator
            ("Activating device owner mode...", 
            "adb shell dpm set-device-owner com.mdmfixtool.mdmfixtool/.DeviceAdmin"),

            # Disable factory reset
            ("Disabling factory reset...", 
            "adb shell am start -S com.mdmfixtool.mdmfixtool/.DisableFactoryReset")
        ]

        # Run each command and log the results
        self.run_commands(commands, on_complete=self.enable_buttons)

        # Final log message
        self.append_log("'Disable Factory Reset' process completed.")




    def create_infinix_itel_tecno_tab(self):
        tab = QWidget() 
        layout = QGridLayout() 

          # Add buttons and connect each to its action
        buttons = [
            ("Read Info", self.read_device_info),
            ("SPD MDM UNLOCK", self.spd_mdm_Unlock),
            ("MTK SPD MDM UNLOCK OS 11 - 14", self.mtkSpdUnlock),
            ("IT ADMIN REMOVE OS 11 - 14",self.it_adminRemove),
            ("Black Screen Fix", self.blackScreenFix),
            ("Disable Factory reset", self.disable_factory_reset),
           

        ]
        
        # Add buttons to the grid layout
        for i, (label, func) in enumerate(buttons):
            button = QPushButton(label)
            button.clicked.connect(func)
            layout.addWidget(button, i // 2, i % 2)  # 2 buttons per row

        tab.setLayout(layout)
        return tab
    

    def spd_mdm_Unlock(self):
        self.command_thread.stop()
        self.clear_log()
        self.disable_buttons()

        # Define all the commands with log messages for each step
        commands = [
            ("Wait for device...", "adb wait-for-device"),
            
            # Clear Google Play Services data
            ("Clearing Google Play Services data...", "adb shell pm clear com.google.android.gms"),
            ("Sending key event 0...", "adb shell input keyevent 0"),
            ("Disabling Google Play Services...", "adb shell pm disable-user com.google.android.gms"),
            
            # Enable GMS and check status
            ("Enabling Google Play Services...", "adb shell pm enable com.google.android.gms"),
            
            # Remove security
            ("Removing Security plugin...", "adb shell pm uninstall com.scorpio.securitycom"),
            
            # Block system update services
            ("Blocking system update services...", "adb shell pm uninstall --user 0 com.transsion.systemupdate"),
            ("Blocking Transsion platform app update...", "adb shell pm uninstall --user 0 com.transsion.plat.appupdate"),
            ("Blocking Google ConfigUpdater...", "adb shell pm uninstall --user 0 com.google.android.configupdater"),
            ("Blocking Dynamic System...", "adb shell pm uninstall --user 0 com.android.dynsystem"),
            ("Blocking Carrier Default App...", "adb shell pm uninstall --user 0 com.android.carrierdefaultapp"),
            ("Blocking Carrier Config...", "adb shell pm uninstall --user 0 com.android.carrierconfig"),
            ("Blocking Proxy Handler...", "adb shell pm uninstall --user 0 com.android.proxyhandler"),
            
            # Install APK

            # MDM removal methods
            ("MDM Remove Method 1...", "adb shell service call package 135 s16 com.scorpio.securitycom i32 0 i32 0"),
            ("MDM Remove Method 2...", "adb shell service call package 131 s16 com.scorpio.securitycom i32 0 i32 0"),
            ("MDM Remove Method 3...", "adb shell service call package 134 s16 com.scorpio.securitycom i32 0 i32 0"),
            ("Final removal of MDM Security plugin...", "adb shell pm uninstall --user 0 com.scorpio.securitycom"),
        ]

        # Display a starting log in orange
        self.log_area.append("<span style='color:white;'>Starting Spd Mdm Removal Process...</span>")
        
        # Run the commands with delay between each
        self.run_commands(commands, on_complete=self.enable_buttons)

    def mtkSpdUnlock(self):
        self.command_thread.stop()
        self.clear_log()
        self.disable_buttons()

    # Define all the commands with log messages for each step
        commands = [
            ("Wait for device...", "adb wait-for-device"),
            
            # Bypass
            ("Bypassing security...", "adb shell service call package 133 s16 com.scorpio.securitycom i32 0 i32 0"),
            
            # MDM removal steps
            ("Removing MDM...", "adb shell service call package 131 s16 com.scorpio.securitycom i32 0 i32 0"),
            ("Removing MDM step 2...", "adb shell service call package 132 s16 com.scorpio.securitycom i32 0 i32 0"),
            ("Removing MDM step 3...", "adb shell service call package 133 s16 com.scorpio.securitycom i32 0 i32 0"),
            ("Removing MDM step 4...", "adb shell service call package 134 s16 com.scorpio.securitycom i32 0 i32 0"),
            ("Removing MDM step 5...", "adb shell service call package 135 s16 com.scorpio.securitycom i32 0 i32 0"),
            ("Removing MDM step 6...", "adb shell service call package 136 s16 com.scorpio.securitycom i32 0 i32 0"),
            
            # Check if removal succeeded
            ("Uninstalling MDM security plugin...", "adb shell pm uninstall --user 0 com.scorpio.securitycom"),
            
            # Enable Google Play Services
            ("Enabling Google Play Services...", "adb shell pm enable com.google.android.gms"),
            
            # Final removal of security plugin
            ("Removing security plugin...", "adb shell pm uninstall com.scorpio.securitycom"),
            
            # Block system update services
            ("Blocking system update services...", "adb shell pm uninstall --user 0 com.transsion.systemupdate"),
            ("Blocking Transsion platform app update...", "adb shell pm uninstall --user 0 com.transsion.plat.appupdate"),
            ("Blocking Google ConfigUpdater...", "adb shell pm uninstall --user 0 com.google.android.configupdater"),
            ("Blocking Dynamic System...", "adb shell pm uninstall --user 0 com.android.dynsystem"),
            ("Blocking Carrier Default App...", "adb shell pm uninstall --user 0 com.android.carrierdefaultapp"),
            ("Blocking Carrier Config...", "adb shell pm uninstall --user 0 com.android.carrierconfig"),
            ("Blocking Proxy Handler...", "adb shell pm uninstall --user 0 com.android.proxyhandler"),
            ("Blocking Transsion platform app update duplicate...", "adb shell pm uninstall --user 0 com.transsion.plat.appupdate"),
        

            # Additional MDM removal methods
            ("MDM Remove Method 1...", "adb shell service call package 135 s16 com.scorpio.securitycom i32 0 i32 0"),
            ("MDM Remove Method 2...", "adb shell service call package 131 s16 com.scorpio.securitycom i32 0 i32 0"),
            ("MDM Remove Method 3...", "adb shell pm uninstall --user 0 com.scorpio.securitycom"),
            ("Final MDM removal...", "adb shell pm uninstall com.scorpio.securitycom"),
            ("Final MDM removal confirmation...", "adb shell service call package 134 s16 com.scorpio.securitycom i32 0 i32 0"),
            ("Uninstalling MDM security plugin (confirmation)...", "adb shell pm uninstall --user 0 com.scorpio.securitycom"),
        ]

        # Display a starting log in orange
        self.log_area.append("<span style='color:white;'>Starting Plugin Removal Process...</span>")
        
        # Run the commands with delay between each
        self.run_commands(commands, on_complete=self.enable_buttons)



    def it_adminRemove(self):
        self.command_thread.stop()
        self.clear_log()
        self.disable_buttons()

        # Define all the commands with log messages for each step
        commands = [
            ("Wait for device...", "adb wait-for-device"),

            # Check if ADB is accessible
            ("Checking if ADB is accessible...", "adb devices"),

           
            ("Blocking Google Services Framework (G)...", "adb shell pm disable --user 0 com.google.android.gsf"),
            
         
            ("Blocking Google Services Framework (G2)...", "adb shell pm disable-user com.google.android.gsf"),

            # Block G3
            ("Blocking Google Services Framework (G3)...", "adb shell pm disable --user 0 com.google.android.gsf"),

            # Remove Provisioning
            ("Removing provisioning...", "adb shell pm uninstall -k --user 0 com.android.managedprovisioning"),

            # Create Profile
            ("Creating profile...", "adb shell pm create-user --profileOf 0 --managed FRASHASANTO"),

            # Set Device Name
            ("Setting device name to FRASHASANTO...", "adb shell settings put global device_name FRASHASANTO"),

            # Set Default Device Name
            ("Setting default device name to FRASHASANTO...", "adb shell settings put global default_device_name FRASHASANTO"),

            # Reboot Device
            ("Rebooting device...", "adb reboot"),
        ]

        # Display a starting log in orange
        self.log_area.append("<span style='color:white;'>Starting KG Removal Process...</span>")
        
        # Run the commands with delay between each
        self.run_commands(commands, on_complete=self.enable_buttons)


    def blackScreenFix(self):
        self.command_thread.stop()
        self.clear_log()
        self.disable_buttons()

        # Define all the commands with log messages for each step
        commands = [
            ("Wait for device...", "adb wait-for-device"),

            # Check if ADB is accessible
            ("Checking if ADB is accessible...", "adb devices"),

            # Bypassing Now: Uninstall com.transsion.overlaysuw
            ("Bypassing Now...", "adb shell pm uninstall --user 0 com.transsion.overlaysuw"),

            # Block System Update: Uninstall com.transsion.systemupdate
            ("Blocking system update...", "adb shell pm uninstall --user 0 com.transsion.systemupdate"),
        ]

        # Display a starting log in orange
        self.log_area.append("<span style='color:white;'>Starting Black Screen Fix Process...</span>")
        
        # Run the commands with delay between each
        self.run_commands(commands, on_complete=self.enable_buttons)
        self.log_area.append("<span style='color:lime;'>Bypass done.</span>")
    


    



    def create_honor_tab(self):
        return self.create_tab_template("Honor")

    def create_xiaomi_tab(self):
        return self.create_tab_template("Xiaomi")
    
    def create_tab_template(self, title):
        tab = QWidget()
        layout = QVBoxLayout()
        label = QLabel(f"{title} Functions")
        layout.addWidget(label)
        tab.setLayout(layout)
        return tab

    def clear_log(self):
        """Clears the log area."""
        self.log_area.clear()
    def log_action(self, message):
    
        self.clear_log()  # Clear previous log

        # Apply color styling for titles (green) and attributes (orange)
        formatted_message = ""
        for line in message.splitlines():
            if ": " in line:
                title, attribute = line.split(": ", 1)
                formatted_message += f"<span style='color: green;'>{title}:</span> <span style='color: orange;'>{attribute}</span><br>"
            else:
                # For lines without "title: attribute" format, display them in orange as general logs
                formatted_message += f"<span style='color: orange;'>{line}</span><br>"

        # Append formatted message to the log area
        self.log_area.append(formatted_message)






    def read_device_info(self):
        self.clear_log()
        self.command_thread.stop()

        properties = {
            "ro.product.model": "Model",
            "ro.product.manufacturer": "Manufacturer",
            "ro.product.cpu.abi": "CPU Architecture",
            "ro.board.platform": "Platform",
            "ro.product.board": "Board",
            "ro.product.name": "Product Name",
            "ro.product.brand": "Brand",
            "ro.build.id": "Build ID",
            "ro.build.version.release": "Android Version",
            "ro.build.date": "Build Date",
            "ro.build.version.security_patch": "Security Patch",
            "ro.build.description": "Build Description",
            "knox.kg.state": "Kg State",
        }

        device_info = {}
        for prop, label in properties.items():
            command = ["adb", "shell", "getprop", prop]
            try:
                # Suppress the console window
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                output = subprocess.check_output(
                    command,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW
                ).decode("utf-8").strip()
                device_info[label] = output if output else "N/A"
            except subprocess.CalledProcessError:
                device_info[label] = "N/A"

        log_message = "\n".join(f"{label}: {value}" for label, value in device_info.items())
        self.log_action(f"Device Info:\n{log_message}")



        
            
        

    def list_devices(self):
        self.command_thread.stop()
        """Lists connected devices."""
        try:
            output = subprocess.check_output(["adb", "devices"]).decode("utf-8")
            self.log_action(f"Connected Devices:\n{output}")
        except subprocess.CalledProcessError:
            self.log_action("Failed to list devices.")

    def run_adb_command(self, command):
        self.command_thread.stop()
        """Runs a simple ADB command like reboot or reboot to bootloader."""
        try:
            output = subprocess.check_output(["adb", command]).decode("utf-8")
            self.log_action(f"Executed '{command}':\n{output}")
        except subprocess.CalledProcessError:
            self.log_action(f"Failed to execute '{command}'.")

    def install_apk(self):
        self.command_thread.stop()
        """Installs an APK on the connected device."""
        apk_path, _ = QFileDialog.getOpenFileName(self, "Select APK File", "", "APK Files (*.apk)")
        if apk_path:
            try:
                output = subprocess.check_output(["adb", "install", apk_path]).decode("utf-8")
                self.log_action(f"APK Install Output:\n{output}")
            except subprocess.CalledProcessError:
                self.log_action("Failed to install APK.")

    
    def pull_file_from_device(self):
        self.command_thread.stop()
        """Pulls a file from the connected device to the local machine."""
        # Use QInputDialog to get text input from the user
        device_file, ok = QInputDialog.getText(self, "Enter Device File Path", "Path on Device:")
        
        if ok and device_file:
            local_path = QFileDialog.getExistingDirectory(self, "Select Local Folder")
            if local_path:
                try:
                    output = subprocess.check_output(["adb", "pull", device_file, local_path]).decode("utf-8")
                    self.log_action(f"File Pull Output:\n{output}")
                except subprocess.CalledProcessError:
                    self.log_action("Failed to pull file from device.")

    def get_asset_path(self, filename):
        """Get the absolute path to the bundled APKs."""
        if getattr(sys, 'frozen', False):  # Check if the app is frozen/bundled
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, 'assets', filename)
    
    
    def generate_qr_code_image(self, data):
        # Generate a QR code as a PIL image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        return img
    

    def generate_qr_code_image(self, data):
        # Generate a QR code as a PIL image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        return img
    
    def run_command(self,command):
        """Run a system command and capture the output and errors."""
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr.strip()}"

    # Fastboot Functions   

    def read_fastboot_info(self):
        # Clear the log area and show starting message
        self.clear_log()
        self.append_log("Reading Fastboot Info...")
        serial_number_result = self.run_command("fastboot getvar serialno")
        self.append_log(f"Serial Number: {serial_number_result.strip()}")
        model_result = self.run_command("fastboot getvar model")
        self.append_log(f"Model: {model_result.strip()}")
        bootloader_result = self.run_command("fastboot getvar bootloader")
        self.append_log(f"Bootloader Version: {bootloader_result.strip()}")
        self.append_log("Fastboot Info Retrieved.")

    def unlock_bootloader(self):
        self.append_log("Unlocking bootloader...")
        self.run_command("fastboot oem unlock")

    def lock_bootloader(self):
        self.append_log("Locking bootloader...")
        self.run_command("fastboot oem lock")

    def flash_recovery(self):
        self.append_log("Flashing recovery...")
        self.run_command("fastboot flash recovery recovery.img")

    def flash_system(self):
        self.append_log("Flashing system...")
        self.run_command("fastboot flash system system.img")

    def erase_cache(self):
        self.append_log("Erasing cache...")
        self.run_command("fastboot erase cache")

    def erase_userdata(self):
        self.append_log("Erasing user data...")
        self.run_command("fastboot erase userdata")

    def flash_recovery_with_selection(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Recovery Image", "", "Image Files (*.img)")
        if file_path:
            self.append_log(f"Flashing recovery image from {file_path}...")
            self.run_command(f"fastboot flash recovery {file_path}")

    def flash_system_with_selection(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select System Image", "", "Image Files (*.img)")
        if file_path:
            self.append_log(f"Flashing system image from {file_path}...")
            self.run_command(f"fastboot flash system {file_path}")

    def boot_custom_image_with_selection(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Boot Image", "", "Image Files (*.img)")
        if file_path:
            self.append_log(f"Booting custom image from {file_path}...")
            self.run_command(f"fastboot boot {file_path}")

    def fastboot_devices(self):
        self.append_log("Listing Fastboot devices...")
        self.run_command("fastboot devices")



class PasswordDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Authentication Required")
        self.setFixedSize(400, 200)
        self.init_ui()

    def init_ui(self):
        # Set layout
        layout = QVBoxLayout()

        # Add title label
        title_label = QLabel("Enter Password")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Add input field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont("Arial", 12))
        layout.addWidget(self.password_input)

        # Add button
        submit_button = QPushButton("Submit")
        submit_button.setFont(QFont("Arial", 12))
        submit_button.setStyleSheet(
            """
            QPushButton {
                background-color: #0078d4; 
                color: white; 
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            """
        )
        submit_button.clicked.connect(self.verify_password)
        layout.addWidget(submit_button)

        # Set layout to dialog
        self.setLayout(layout)

    def verify_password(self):
        correct_password = "INFOSHOULDBEFREESANTO254"
        entered_password = self.password_input.text()

        if entered_password == correct_password:
            QMessageBox.information(self, "Access Granted", "Welcome!")
            self.accept()  # Close the dialog and allow the app to continue
        else:
            QMessageBox.warning(self, "Access Denied", "Incorrect password. Please try again.")
            self.password_input.clear()  # Clear
  


if __name__ == '__main__':
   
    
    
    app = QApplication(sys.argv)
    dialog = PasswordDialog()
    if dialog.exec_() == QDialog.Accepted:
        # Your main application logic goes here
        print("Running the main application...")
        # Replace this print statement with your app logic
        window = UnlockToolUI()
        window.show()
    sys.exit(app.exec_())
