import time
import threading
from pystray import MenuItem as item
import pystray
from PIL import Image
import utils
import gui
import logging
import os
import sys

# Get the logger from utils
logger = utils.setup_logging()
stop_event = threading.Event()

def organize_files_loop():
    """Run file sorter every set amount of time read from config file"""
    while not stop_event.is_set():
        utils.file_sorter()
        # Use a short sleep and check the interval inside the loop
        # to make it responsive to changes.
        interval_seconds = utils.get_interval() * 60
        # This creates a more responsive way to wait that respects the stop_event
        for _ in range(interval_seconds):
            if stop_event.is_set():
                break
            time.sleep(1)

def exit_action():
    """Stops all threads and exits the application."""
    logger.info("Exit action called. Stopping threads.")
    stop_event.set()
    # A more forceful exit to ensure the container stops
    os._exit(0)

def run_tray_icon():
    """Function to set up and run the system tray icon."""
    try:
        image_path = utils.root_path("resources/broom.png")
        image = Image.open(image_path)
        # Use a lambda to avoid issues with passing the icon object to the exit function
        menu = (item('Configure Rules', gui.open_config_window_threaded), item('Exit', lambda: exit_action()))
        icon = pystray.Icon("Organizer", image, "Organizer", menu)
        logger.info("Attempting to start system tray icon.")
        icon.run()
    except Exception as e:
        # This error is expected in environments without a system tray (like Docker)
        logger.warning(f"Failed to create system tray icon: {e}")
        logger.warning("This is expected in Docker. The application will continue without a tray icon.")
        # The thread will simply exit if the icon cannot be created.

def main():
    """Main function to start the application."""
    if "--check-config" in sys.argv[1:]:
        config = utils.load_config()
        if not isinstance(config, dict):
            logger.error("Configuration is missing or invalid.")
            return 1
        logger.info("Configuration loaded successfully from %s.", utils.get_config_path())
        return 0

    # Start the background file organizer thread
    organization_thread = threading.Thread(target=organize_files_loop)
    organization_thread.daemon = True
    organization_thread.start()

    # Start the system tray icon in its own thread.
    # If it fails, it will not block the main application.
    tray_thread = threading.Thread(target=run_tray_icon)
    tray_thread.daemon = True
    tray_thread.start()

    # Start the main GUI window. This is a blocking call that starts
    # the tkinter main loop. The application will run until this window is closed.
    gui.open_config_window()

    # When the GUI window is closed, the script will continue from here.
    logger.info("Main GUI window closed. Shutting down.")
    exit_action()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())