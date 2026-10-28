import os
import sys
import shutil
import tempfile
from typing import Optional
try:
    import winreg
except ImportError:
    winreg = None
import yaml
import threading
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("OrganizerLogger")

config_lock = threading.RLock()

def root_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    return os.path.join(base_path, relative_path)

def appdata_path():
    """Returns the path to the user's AppData/Roaming directory."""
    if sys.platform == "win32":
        return os.getenv('APPDATA')
    else:
        return os.path.join(os.path.expanduser('~'), '.organizer')

def config_directory():
    """Return the platform's per-user configuration directory."""
    if sys.platform == "win32":
        base_path = os.getenv("APPDATA") or os.path.join(
            os.path.expanduser("~"), "AppData", "Roaming"
        )
        return os.path.join(base_path, "Organizer")
    base_path = os.getenv("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config"
    )
    return os.path.join(base_path, "organizer")

def get_config_path():
    """Return the location of the user's editable configuration."""
    return os.path.join(config_directory(), "config.yaml")

def _legacy_config_paths():
    paths = [root_path(os.path.join("resources", "config.yaml"))]
    if getattr(sys, "frozen", False):
        paths.insert(0, os.path.join(os.path.dirname(sys.executable), "config.yaml"))
    return paths

def _migrate_legacy_config(config_file):
    with config_lock:
        if os.path.exists(config_file):
            return
        for legacy_path in _legacy_config_paths():
            if os.path.isfile(legacy_path):
                os.makedirs(os.path.dirname(config_file), exist_ok=True)
                shutil.copy2(legacy_path, config_file)
                logger.info(
                    "Migrated configuration from %s to %s",
                    legacy_path,
                    config_file,
                )
                return

def setup_logging():
    """Sets up a rotating log file in the AppData directory."""
    appdata = appdata_path()
    log_dir = os.path.join(appdata, "Organizer")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, "organizer.log")

    # Create a logger
    logger = logging.getLogger("OrganizerLogger")
    logger.setLevel(logging.INFO)

    # Create a rotating file handler
    handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)

    # Create a formatter and set it for the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the handler to the logger
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger

def locate_folder_path() -> Optional[str]:
    """ Returns Downloads folder path """
    if sys.platform == "win32": # Windows
        try:
            # Open the registry key that stores user shell folder paths
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                # The GUID for the Downloads folder is {374DE290-123F-4565-9164-39C4925E467B}
                downloads_guid = "{374DE290-123F-4565-9164-39C4925E467B}"
                path_str, _ = winreg.QueryValueEx(key, downloads_guid)
                return os.path.expandvars(path_str)
        except FileNotFoundError:
            # Fallback in case the registry key is not found
            return os.path.join(os.path.expanduser('~'), 'Downloads')
        except Exception as e:
            logger.exception(f"Error occurred while reading the registry: {e}")
            return None
    else: # macOS and Linux
        return os.path.join(os.path.expanduser('~'), 'Downloads')

def load_config():
    """Load the user's configuration, migrating the bundled file if needed."""
    config_file = get_config_path()
    with config_lock:
        if not os.path.exists(config_file):
            _migrate_legacy_config(config_file)

        if not os.path.exists(config_file):
            logger.error(f"'{config_file}' not found. Please create it.")
            return None
        with open(config_file, "r", encoding="utf-8") as f:
            try:
                config = yaml.safe_load(f)
                return config
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML file: {e}")
                return None

def get_rules():
    """Returns just the rules from the config."""
    config = load_config()
    if config and "rules" in config and isinstance(config["rules"], list):
        return config["rules"]
    else:
        logger.error(f"Error: config.yaml is missing the 'rules' list.")
        return None

def get_interval():
    """Returns the sorting interval in minutes from the config."""
    config = load_config()
    return config.get("interval", 5) if config else 5

def save_interval(interval_minutes):
    """Saves the sorting interval to the config.yaml file."""
    if interval_minutes <= 0:
        interval_minutes = 5
    with config_lock:
        # Reload the config inside the lock to get the latest version
        config = load_config()
        if config is None:
            config = {'rules': [], 'interval': 5}
        config["interval"] = interval_minutes
        # The save_config function will handle the file writing safely
        save_config(config)
        logger.info("Interval updated in config.yaml")

def save_config(config):
    """Save the config to the user's per-user configuration file."""
    config_file = get_config_path()
    config_directory_path = os.path.dirname(config_file)
    os.makedirs(config_directory_path, exist_ok=True)
    with config_lock:
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=config_directory_path,
                delete=False,
            ) as config_file_handle:
                temporary_path = config_file_handle.name
                yaml.safe_dump(config, config_file_handle, default_flow_style=False)
            os.replace(temporary_path, config_file)
        finally:
            if temporary_path and os.path.exists(temporary_path):
                os.remove(temporary_path)

def update_rule(updated_rule):
    """Update an existing rule in the config."""
    with config_lock:
        config = load_config()
        if config is not None:
            rules = config.get("rules", [])
            for i, rule in enumerate(rules):
                if rule.get("name") == updated_rule.get("name"):
                    rules[i] = updated_rule
                    config["rules"] = rules
                    save_config(config)
                    logger.info(f"{rule.get("name")} rule updated")
                    return True
    return False

def delete_rule_from_config(rule_name):
    """Delete a rule from the config by its name."""
    with config_lock:
        config = load_config()
        if config is not None:
            rules = config.get("rules", [])
            original_len = len(rules)
            rules = [rule for rule in rules if rule.get("name") != rule_name]
            if len(rules) < original_len:
                config["rules"] = rules
                save_config(config)
                logger.info(f"{rule_name} rule deleted")
                return True
    return False

def add_rule(new_rule):
    """Appends a new rule to the config."""
    with config_lock:
        config = load_config()
        if new_rule.get("sub"):
            create_folder(new_rule.get("destination"))
        if config is not None:
            rules = config.get("rules", [])
            rules.append(new_rule)
            config["rules"] = rules
            save_config(config)
            logger.info(f"Added {new_rule} rule to config.yaml")

def get_sort_plan(downloads_dir=None, rules=None):
    """Return planned source/destination paths without changing any files."""
    if downloads_dir is None:
        downloads_dir = locate_folder_path()
    if rules is None:
        rules = get_rules()
    if not downloads_dir or not rules:
        return []

    planned_moves = []
    reserved_paths = set()
    for filename in os.listdir(downloads_dir):
        file_path = os.path.join(downloads_dir, filename)
        if not os.path.isfile(file_path):
            continue

        file_name, file_extension = os.path.splitext(filename)
        for rule in rules:
            match_extension = file_extension in rule.get("extensions", [])
            match_keyword = bool(rule.get("keywords")) and any(
                keyword.lower() in file_name for keyword in rule["keywords"]
            )
            if not (match_extension or match_keyword):
                continue

            if rule["sub"]:
                destination_folder = os.path.join(downloads_dir, rule["destination"])
            else:
                destination_folder = rule["destination"]
            if not os.path.isdir(destination_folder):
                continue

            destination_path = get_final_name(
                file_name, file_extension, destination_folder, reserved_paths
            )
            reserved_paths.add(os.path.normcase(destination_path))
            planned_moves.append((file_path, destination_path))
            break
    return planned_moves

def file_sorter():
    """Move files according to the configured sorting rules."""
    downloads_dir = locate_folder_path()
    rules = get_rules()
    if not rules:
        return

    try:
        for source_path, destination_path in get_sort_plan(downloads_dir, rules):
            try:
                shutil.move(source_path, destination_path)
                logger.info("Moved %s to %s.", source_path, destination_path)
            except Exception:
                logger.exception("Error moving %s.", source_path)
    except PermissionError:
        logger.error("Permission denied accessing downloads folder")
    except Exception as e:
        logger.exception("Unexpected error in file_sorter")

def get_final_name(file_name, file_extension, destination_folder, reserved_paths=None) -> str:
    """Return an unused destination path without changing the source file."""
    if reserved_paths is None:
        reserved_paths = set()
    count = 1
    destination_path = os.path.join(destination_folder, file_name + file_extension)
    while (
        os.path.exists(destination_path)
        or os.path.normcase(destination_path) in reserved_paths
    ):
        destination_path = os.path.join(
            destination_folder, f"{file_name}({count}){file_extension}"
        )
        count += 1
    return destination_path

def create_folder(new_path):
    """Create folder in the Download folder"""
    downloads_dir = locate_folder_path()
    directory = os.path.join(downloads_dir, new_path)
    try:
        # Create the entire path.
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Directory '{directory}' is ready.")
    except Exception as e:
        logger.exception(f"An error occurred while trying to create directory '{directory}'.")

def create_folders():
    """Create the deafult folders named in the default config.yaml"""
    types = ["Images", "Documents", "Installers", "Archives"]

    for type in types:
        create_folder(type)