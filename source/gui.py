import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import utils
import sys
from tkinter import messagebox

# --- Drag and Drop State ---
# Dictionary to hold information about the widget being dragged
drag_data = {
    "widget": None,
    "start_x": 0,
    "start_y": 0,
}

def on_drag_start(event, widget):
    """Initiates the drag operation."""
    # Record the widget being dragged and the initial mouse position
    drag_data["widget"] = widget
    drag_data["start_x"] = event.x_root
    drag_data["start_y"] = event.y_root
    # Lift the widget to the top of the stacking order
    widget.lift()

def on_drag_motion(event):
    """Moves the widget with the mouse."""
    if drag_data["widget"]:
        # Calculate how much the mouse has moved
        delta_x = event.x_root - drag_data["start_x"]
        delta_y = event.y_root - drag_data["start_y"]
        
        # Get the initial position of the widget
        x = drag_data["widget"].winfo_x()
        y = drag_data["widget"].winfo_y()

        # Calculate the new position
        new_x = x + delta_x
        new_y = y + delta_y
        
        # Move the widget
        drag_data["widget"].place(x=new_x, y=new_y)

        # Update the starting position for the next motion event
        drag_data["start_x"] = event.x_root
        drag_data["start_y"] = event.y_root

def on_drag_end(event, frame):
    """Finalizes the drag, reorders the rules, and refreshes the UI."""
    if drag_data["widget"]:
        # Get all rule frames and sort them by their current y-position
        all_frames = [child for child in frame.winfo_children() if isinstance(child, ttk.LabelFrame)]
        all_frames.sort(key=lambda w: w.winfo_y())
        
        # Get the original rules from the config
        original_rules = utils.get_rules()
        rules_by_name = {rule['name']: rule for rule in original_rules}
        
        # Create the new list of rules based on the sorted frames
        new_rules_order = []
        for f in all_frames:
            rule_name = f.cget("text")
            if rule_name in rules_by_name:
                new_rules_order.append(rules_by_name[rule_name])

        # Save the new order to the config file
        config = utils.load_config()
        config['rules'] = new_rules_order
        utils.save_config(config)

        # Reset the drag data
        drag_data["widget"] = None
        
        # Refresh the entire list of rules to reflect the new order
        refresh_rules_list(frame)

def open_config_window_threaded():
    """Opens the main configuration window in a separate thread."""
    config_thread = threading.Thread(target=open_config_window)
    config_thread.daemon = True
    config_thread.start()

def refresh_rules_list(frame):
    """Clears and redraws all rule cards in the given frame."""
    # Destroy all current widgets in the frame
    for widget in frame.winfo_children():
        widget.destroy()

    # Reload the rules and rebuild the UI
    rules = utils.get_rules()
    if rules:
        create_rule_cards(frame, rules) # Use the refactored card creation logic
    else:
        ttk.Label(frame, text="Could not load or find any rules in config.yaml.").pack(pady=20)

def create_rule_cards(parent_frame, rules):
    """Creates and packs all the rule card widgets into the parent_frame."""
    config_window = parent_frame.winfo_toplevel()
    for rule in rules:
        rule_frame = ttk.LabelFrame(parent_frame, text=f"{rule.get('name', 'N/A')}", padding="10", bootstyle="primary")
        rule_frame.pack(pady=10, padx=10, fill="x")

        # --- Grid Configuration ---
        # Configure column 1 to take up any extra space, pushing the buttons to the right
        rule_frame.columnconfigure(1, weight=1)

        # --- Labels and Values (Columns 0 and 1) ---
        ttk.Label(rule_frame, text="Extensions:").grid(row=0, column=0, sticky="w", pady=2, padx=5)
        ext_text = ", ".join(rule.get('extensions', [])) or "Any"
        ttk.Label(rule_frame, text=ext_text, wraplength=350).grid(row=0, column=1, sticky="w")

        ttk.Label(rule_frame, text="Keywords:").grid(row=1, column=0, sticky="w", pady=2, padx=5)
        key_text = ", ".join(rule.get('keywords', [])) or "None"
        ttk.Label(rule_frame, text=key_text, wraplength=350).grid(row=1, column=1, sticky="w")

        ttk.Label(rule_frame, text="Destination:").grid(row=2, column=0, sticky="w", pady=2, padx=5)
        ttk.Label(rule_frame, text=rule.get('destination', 'N/A')).grid(row=2, column=1, sticky="w")

        # --- Buttons (Column 2) ---
        button_frame = ttk.Frame(rule_frame)
        # Place the frame in the third column, spanning all three rows, and stick it to the top-right
        button_frame.grid(row=0, column=2, rowspan=3, sticky="ne", padx=5, pady=5)

        edit_button = ttk.Button(
            button_frame,
            text="Edit",
            command=lambda r=rule: open_edit_window(r, config_window, parent_frame),
            bootstyle="primary"
        )
        # Pack the buttons to stack them vertically
        edit_button.pack(fill='x')

        delete_button = ttk.Button(
            button_frame,
            text="Delete",
            command=lambda r=rule: open_delete_window(r, config_window, parent_frame),
            bootstyle="danger"
        )
        delete_button.pack(fill='x', pady=5)

        # --- Bindings for Drag and Drop ---
        # Bind events to the main frame of the rule card
        rule_frame.bind("<ButtonPress-1>", lambda e, w=rule_frame: on_drag_start(e, w))
        rule_frame.bind("<B1-Motion>", on_drag_motion)
        rule_frame.bind("<ButtonRelease-1>", lambda e, f=parent_frame: on_drag_end(e, f))

        # Also bind the events to all children, so the drag can be initiated from anywhere inside the card
        for child in rule_frame.winfo_children():
            if isinstance(child, (ttk.Button, ttk.Frame)):
                continue
            child.bind("<ButtonPress-1>", lambda e, w=rule_frame: on_drag_start(e, w))
            child.bind("<B1-Motion>", on_drag_motion)
            child.bind("<ButtonRelease-1>", lambda e, f=parent_frame: on_drag_end(e, f))

def set_window_icon(window):
    """Sets the broom icon for the window based on the OS."""
    try:
        if sys.platform == "win32":
            # .ico is best for Windows
            icon_path = utils.root_path("resources/broom.ico")
            window.iconbitmap(icon_path)
        else:
            # .png is more reliable for Linux/macOS with PhotoImage
            icon_path = utils.root_path("resources/broom.png")
            photo = tk.PhotoImage(file=icon_path)
            # The icon needs to be attached to the window object to prevent garbage collection
            window.iconphoto(True, photo)
    except Exception as e:
        # Log if the icon fails to load, but don't crash the app
        utils.logger.warning(f"Could not set window icon from {icon_path}: {e}")


config_window_instance = None

def open_config_window():
    """
    Opens the configuration window. Creates it if it doesn't exist,
    otherwise, it just shows the existing window.
    """
    global config_window_instance

    # If window exists, just bring it to the front
    if config_window_instance is not None and config_window_instance.winfo_exists():
        config_window_instance.deiconify() # Un-hides the window
        config_window_instance.lift() # Brings to the front
        config_window_instance.focus_set() # Gives it focus
        return

    # If window doesn't exist, create it
    config_window = ttk.Window(themename="litera")
    config_window_instance = config_window # Store the instance
    config_window.title("Configure Rules")
    set_window_icon(config_window)
    
    config_window.protocol("WM_DELETE_WINDOW", config_window.withdraw)

    w, h = 800, 500
    ws, hs = config_window.winfo_screenwidth(), config_window.winfo_screenheight()
    x, y = (ws/2) - (w/2), (hs/2) - (h/2)
    config_window.geometry('%dx%d+%d+%d' % (w, h, x, y))

    main_frame = tk.Frame(config_window)
    main_frame.pack(fill='both', expand=True)

    top_frame = ttk.Frame(main_frame)
    top_frame.pack(fill='x', padx=10, pady=5)

    add_button = ttk.Button(
        top_frame,
        text="Add New Rule",
        # The command will call a new threaded function
        command=lambda: open_add_window(config_window, scrollable_frame),
        bootstyle="success-outline" # Green outline button
    )
    add_button.pack(side="left")
    sort_button = ttk.Button(
        top_frame,
        text="Sort Downloads folder",
        # The command will sort Download folder
        command=lambda: utils.file_sorter(),
        bootstyle="info-outline"
    )
    sort_button.pack(side="left")
    preview_button = ttk.Button(
        top_frame,
        text="Preview sort",
        command=lambda: open_sort_preview(config_window),
        bootstyle="secondary-outline"
    )
    preview_button.pack(side="left")
    create_default_folders_button = ttk.Button(
        top_frame,
        text="Create deafult folders",
        command=lambda: utils.create_folders(),
        bootstyle="primary-outline" # Default outline button
    )
    create_default_folders_button.pack(side="left")
    interval_frame = ttk.Frame(top_frame)
    interval_frame.pack(side="left", padx=5)
    ttk.Label(interval_frame, text="Interval:").pack(side="left")
    interval_var = tk.StringVar(value=str(utils.get_interval()))
    interval_entry = ttk.Entry(interval_frame, textvariable=interval_var, width=5)
    interval_entry.pack(side="left", padx=(0, 5))

    def apply_interval(var_to_use):
        try:
            new_interval = int(var_to_use.get())
            if new_interval > 0:
                utils.save_interval(new_interval)
            else:
                print("Interval must be a positive number.")
        except ValueError:
            print("Invalid interval. Please enter a number.")
            
    apply_button = ttk.Button(
        interval_frame,
        text="Apply",
        command=lambda: apply_interval(interval_var),
        bootstyle="secondary" # A subtle button style
    )
    apply_button.pack(side="left")

    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    scrollbar.pack(side="right", fill="y")

    rules = utils.get_rules()
    if rules:
        # Initial creation of rule cards
        create_rule_cards(scrollable_frame, rules)
    else:
        ttk.Label(scrollable_frame, text="Could not load or find any rules in config.yaml.").pack(pady=20)

    config_window.mainloop()

def open_sort_preview(parent_window):
    """Show planned file moves without changing any files."""
    try:
        planned_moves = utils.get_sort_plan()
    except Exception as error:
        utils.logger.exception("Could not create file sorting preview.")
        messagebox.showerror("Preview failed", str(error), parent=parent_window)
        return

    preview_window = tk.Toplevel(parent_window)
    set_window_icon(preview_window)
    preview_window.title("Preview Sort")
    preview_window.geometry("700x450")
    preview_window.transient(parent_window)

    content = ttk.Frame(preview_window, padding=10)
    content.pack(fill="both", expand=True)
    if not planned_moves:
        ttk.Label(content, text="No files match the current rules.").pack(
            anchor="w", pady=5
        )
    else:
        ttk.Label(
            content,
            text=f"{len(planned_moves)} file(s) would be moved:",
        ).pack(anchor="w", pady=(0, 5))

    text_frame = ttk.Frame(content)
    text_frame.pack(fill="both", expand=True)
    scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
    preview_text = tk.Text(text_frame, wrap="char", yscrollcommand=scrollbar.set)
    scrollbar.configure(command=preview_text.yview)
    scrollbar.pack(side="right", fill="y")
    preview_text.pack(side="left", fill="both", expand=True)
    for source_path, destination_path in planned_moves:
        preview_text.insert(
            "end",
            f"{source_path}\n    -> {destination_path}\n\n",
        )
    preview_text.configure(state="disabled")
    ttk.Button(content, text="Close", command=preview_window.destroy).pack(
        anchor="e", pady=(8, 0)
    )

def open_delete_window(rule, parent_window, frame_to_refresh):
    """Opens a window to delete a rule"""
    delete_window = tk.Toplevel(parent_window)
    set_window_icon(delete_window)
    delete_window.title("Confirm Delete")
    w, h = 350, 100
    ws, hs = delete_window.winfo_screenwidth(), delete_window.winfo_screenheight()
    x, y = (ws/2) - (w/2), (hs/2) - (h/2)
    delete_window.geometry('%dx%d+%d+%d' % (w, h, x, y))

    delete_window.grab_set()
    delete_window.transient(parent_window)

    label = ttk.Label(delete_window, text="Are you sure you want to delete this rule?")
    label.pack(pady=10)

    button_frame = ttk.Frame(delete_window)
    button_frame.pack(pady=5)

    def confirm_delete():
        """Deletes the rule, closes the pop-up, and refreshes the list."""
        utils.delete_rule_from_config(rule.get("name"))
        delete_window.destroy()
        # This is the key change: just refresh the list in the existing window.
        refresh_rules_list(frame_to_refresh)

    yes_button = ttk.Button(button_frame, text="YES", command=confirm_delete)
    yes_button.pack(side="left", padx=10)

    no_button = ttk.Button(button_frame, text="NO", command=delete_window.destroy)
    no_button.pack(side="left", padx=10)

def open_edit_window(rule, parent_window, frame_to_refresh):
    """Opens a window to edit a rule"""
    edit_window = tk.Toplevel(parent_window)
    set_window_icon(edit_window)
    edit_window.title("Edit "+ rule.get("name"))
    w, h = 350, 300
    ws, hs = edit_window.winfo_screenwidth(), edit_window.winfo_screenheight()
    x, y = (ws/2) - (w/2), (hs/2) - (h/2)
    edit_window.geometry('%dx%d+%d+%d' % (w,h,x,y))

    edit_window.grab_set()
    edit_window.transient(parent_window)

    # --- Create a frame for the form ---
    form_frame = ttk.Frame(edit_window, padding="10")
    form_frame.pack(fill="both", expand=True)

    # --- Tkinter variables to hold form data ---
    name_var = tk.StringVar(value=rule.get("name", ""))
    extensions_var = tk.StringVar(value=", ".join(rule.get("extensions", [])))
    keywords_var = tk.StringVar(value=", ".join(rule.get("keywords", [])))
    destination_var = tk.StringVar(value=rule.get("destination", ""))
    sub_var = tk.BooleanVar(value=rule.get("sub", False))

    # --- Form Fields ---
    # Rule Name (read-only, as it's the identifier)
    ttk.Label(form_frame, text="Rule Name:").grid(row=0, column=0, sticky="w", pady=2)
    ttk.Entry(form_frame, textvariable=name_var, state="readonly").grid(row=0, column=1, sticky="ew", pady=2)

    # Extensions
    ttk.Label(form_frame, text="Extensions:").grid(row=1, column=0, sticky="w", pady=2)
    ttk.Entry(form_frame, textvariable=extensions_var).grid(row=1, column=1, sticky="ew", pady=2)

    # Keywords
    ttk.Label(form_frame, text="Keywords:").grid(row=2, column=0, sticky="w", pady=2)
    ttk.Entry(form_frame, textvariable=keywords_var).grid(row=2, column=1, sticky="ew", pady=2)

    # Destination
    ttk.Label(form_frame, text="Destination:").grid(row=3, column=0, sticky="w", pady=2)
    ttk.Entry(form_frame, textvariable=destination_var).grid(row=3, column=1, sticky="ew", pady=2)

    # Sub-folder Checkbox
    ttk.Checkbutton(form_frame, text="Create as sub-folder in Downloads", variable=sub_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=5)

    # Make the second column stretchable
    form_frame.columnconfigure(1, weight=1)

    # --- Save and Cancel Buttons ---
    button_frame = ttk.Frame(edit_window, padding=(0, 0, 10, 10))
    button_frame.pack(fill="x")

    def save_changes():
        """Gathers data, updates the config, and refreshes the main window."""
        # Prepare data from form
        # Split comma-separated strings into lists, stripping whitespace
        extensions_list = [ext.strip() for ext in extensions_var.get().split(',') if ext.strip()]
        keywords_list = [key.strip() for key in keywords_var.get().split(',') if key.strip()]

        # Create the updated rule dictionary
        updated_rule = {
            "name": name_var.get(),
            "extensions": extensions_list,
            "keywords": keywords_list,
            "destination": destination_var.get(),
            "sub": sub_var.get()
        }

        # Save to config file and refresh UI
        utils.update_rule(updated_rule)
        edit_window.destroy()
        refresh_rules_list(frame_to_refresh)

    ttk.Button(button_frame, text="Save", command=save_changes).pack(side="right", padx=5)
    ttk.Button(button_frame, text="Cancel", command=edit_window.destroy).pack(side="right")

def open_add_window(parent_window, frame_to_refresh):
    """Opens a window to create a new rule."""
    add_window = tk.Toplevel(parent_window)
    set_window_icon(add_window)
    add_window.title("Add New Rule")
    w, h = 350, 300
    ws, hs = add_window.winfo_screenwidth(), add_window.winfo_screenheight()
    x, y = (ws/2) - (w/2), (hs/2) - (h/2)
    add_window.geometry('%dx%d+%d+%d' % (w, h, x, y))

    add_window.grab_set()
    add_window.transient(parent_window)

    form_frame = ttk.Frame(add_window, padding="10")
    form_frame.pack(fill="both", expand=True)

    # Variables for the new rule's data
    name_var = tk.StringVar()
    extensions_var = tk.StringVar()
    keywords_var = tk.StringVar()
    destination_var = tk.StringVar()
    sub_var = tk.BooleanVar(value=True) # Default to true

    # --- Form Fields (Name is now editable) ---
    ttk.Label(form_frame, text="Rule Name:").grid(row=0, column=0, sticky="w", pady=2)
    ttk.Entry(form_frame, textvariable=name_var).grid(row=0, column=1, sticky="ew", pady=2)

    ttk.Label(form_frame, text="Extensions:").grid(row=1, column=0, sticky="w", pady=2)
    ttk.Entry(form_frame, textvariable=extensions_var).grid(row=1, column=1, sticky="ew", pady=2)

    ttk.Label(form_frame, text="Keywords:").grid(row=2, column=0, sticky="w", pady=2)
    ttk.Entry(form_frame, textvariable=keywords_var).grid(row=2, column=1, sticky="ew", pady=2)

    ttk.Label(form_frame, text="Destination:").grid(row=3, column=0, sticky="w", pady=2)
    ttk.Entry(form_frame, textvariable=destination_var).grid(row=3, column=1, sticky="ew", pady=2)

    ttk.Checkbutton(form_frame, text="Create as sub-folder in Downloads", variable=sub_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=5)
    form_frame.columnconfigure(1, weight=1)

    # --- Save and Cancel Buttons ---
    button_frame = ttk.Frame(add_window, padding=(0, 0, 10, 10))
    button_frame.pack(fill="x")

    def save_new_rule():
        """Gathers data, creates a new rule, and saves it."""
        rule_name = name_var.get().strip()
        if not rule_name:
            # Simple validation: prevent saving with no name
            utils.logger.warning("Empty name, couldn't save")
            return

        extensions_list = [ext.strip() for ext in extensions_var.get().split(',') if ext.strip()]
        keywords_list = [key.strip() for key in keywords_var.get().split(',') if key.strip()]

        new_rule = {
            "name": rule_name,
            "extensions": extensions_list,
            "keywords": keywords_list,
            "destination": destination_var.get().strip(),
            "sub": sub_var.get()
        }

        utils.add_rule(new_rule) # Call the new utility function
        add_window.destroy()
        refresh_rules_list(frame_to_refresh)

    ttk.Button(button_frame, text="Save", command=save_new_rule).pack(side="right", padx=5)
    ttk.Button(button_frame, text="Cancel", command=add_window.destroy).pack(side="right")