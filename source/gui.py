import tkinter as tk
import ttkbootstrap as ttk
import threading
import utils
import sys
from tkinter import messagebox

def _rule_frames(parent_frame):
    ordered_frames = getattr(parent_frame, "rule_frame_order", None)
    if ordered_frames is not None:
        return [frame for frame in ordered_frames if frame.winfo_exists()]
    return [
        child
        for child in parent_frame.winfo_children()
        if hasattr(child, "rule_data")
    ]


def _update_rule_order_controls(parent_frame):
    frames = _rule_frames(parent_frame)
    for index, frame in enumerate(frames, start=1):
        frame.order_label.configure(text=f"{index:02}")
        frame.move_up_button.configure(
            state="normal" if index > 1 else "disabled"
        )
        frame.move_down_button.configure(
            state="normal" if index < len(frames) else "disabled"
        )


def _animate_rule_order(parent_frame, original_order, ordered_frames):
    """Slide the reordered rule cards into their new positions."""
    parent_frame.rule_frame_order = ordered_frames
    parent_frame.update_idletasks()

    start_positions = {
        frame: frame.winfo_y()
        for frame in original_order
    }
    card_heights = {frame: frame.winfo_height() for frame in original_order}
    first_position = min(start_positions.values())
    target_positions = {}
    next_position = first_position
    for frame in ordered_frames:
        target_positions[frame] = next_position
        next_position += card_heights[frame] + 12

    parent_height = max(parent_frame.winfo_reqheight(), next_position)
    parent_frame.pack_propagate(False)
    parent_frame.configure(height=parent_height)

    for frame in original_order:
        frame.pack_forget()
        frame.place(
            x=4,
            y=start_positions[frame],
            relwidth=1,
            width=-8,
            height=card_heights[frame],
        )
        frame.move_up_button.configure(state="disabled")
        frame.move_down_button.configure(state="disabled")

    step_count = 12

    def finish_animation():
        if not parent_frame.winfo_exists():
            return
        for frame in ordered_frames:
            frame.place_forget()
            frame.pack(pady=6, padx=4, fill="x")
        parent_frame.pack_propagate(True)
        _update_rule_order_controls(parent_frame)
        parent_frame.reorder_animation_active = False

    def animate_step(step):
        if not parent_frame.winfo_exists():
            return
        progress = step / step_count
        eased_progress = 1 - (1 - progress) ** 3
        for frame in ordered_frames:
            start = start_positions[frame]
            target = target_positions[frame]
            position = round(start + (target - start) * eased_progress)
            frame.place_configure(y=position)

        if step >= step_count:
            finish_animation()
        else:
            parent_frame.after(16, lambda: animate_step(step + 1))

    animate_step(1)


def move_rule(rule_frame, direction):
    """Move a rule by one position and save its new priority."""
    if direction not in (-1, 1):
        raise ValueError("Rule movement direction must be -1 or 1.")

    parent_frame = rule_frame.master
    if getattr(parent_frame, "reorder_animation_active", False):
        return
    original_order = _rule_frames(parent_frame)
    current_index = original_order.index(rule_frame)
    target_index = current_index + direction
    if not 0 <= target_index < len(original_order):
        return

    ordered_frames = original_order.copy()
    ordered_frames.insert(target_index, ordered_frames.pop(current_index))

    try:
        config = utils.load_config()
        if not isinstance(config, dict):
            raise ValueError("The configuration could not be loaded.")
        config["rules"] = [frame.rule_data for frame in ordered_frames]
        utils.save_config(config)
    except Exception as error:
        utils.logger.exception("Could not save the new rule order.")
        messagebox.showerror(
            "Could not reorder rules",
            f"The new order was not saved.\n\n{error}",
            parent=parent_frame.winfo_toplevel(),
        )
        return

    parent_frame.reorder_animation_active = True
    _animate_rule_order(parent_frame, original_order, ordered_frames)

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
        ttk.Label(
            frame,
            text=(
                "Could not load the configuration."
                if rules is None
                else "No rules found. Add a rule to get started."
            ),
            bootstyle="secondary",
            padding=20,
        ).pack(anchor="center", pady=30)

def create_rule_cards(parent_frame, rules):
    """Create the rule cards in priority order."""
    parent_frame.rule_frame_order = []
    config_window = parent_frame.winfo_toplevel()
    for index, rule in enumerate(rules, start=1):
        rule_frame = ttk.LabelFrame(
            parent_frame,
            padding=(14, 12),
            bootstyle="secondary",
        )
        rule_frame.rule_data = rule
        parent_frame.rule_frame_order.append(rule_frame)
        rule_frame.pack(pady=6, padx=4, fill="x")
        rule_frame.columnconfigure(1, weight=1)

        header = ttk.Frame(rule_frame)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        header.columnconfigure(2, weight=1)

        rule_frame.order_label = ttk.Label(
            header,
            text=f"{index:02}",
            bootstyle="primary",
            width=3,
            anchor="center",
        )
        rule_frame.order_label.grid(row=0, column=0, padx=(0, 8))
        movement_controls = ttk.Frame(header)
        movement_controls.grid(row=0, column=1, padx=(0, 8))
        rule_frame.move_up_button = ttk.Button(
            movement_controls,
            text="↑",
            takefocus=False,
            command=lambda card=rule_frame: move_rule(card, -1),
            bootstyle="light",
            width=2,
            padding=0,
        )
        rule_frame.move_up_button.pack()
        rule_frame.move_down_button = ttk.Button(
            movement_controls,
            text="↓",
            takefocus=False,
            command=lambda card=rule_frame: move_rule(card, 1),
            bootstyle="light",
            width=2,
            padding=0,
        )
        rule_frame.move_down_button.pack(pady=(2, 0))
        ttk.Label(
            header,
            text=rule.get("name", "Untitled rule"),
            font=("Segoe UI", 11, "bold"),
        ).grid(row=0, column=2, sticky="w")

        button_frame = ttk.Frame(header)
        button_frame.grid(row=0, column=3, sticky="e")
        ttk.Button(
            button_frame,
            text="Edit",
            command=lambda r=rule: open_edit_window(
                r, config_window, parent_frame
            ),
            bootstyle="primary-outline",
            width=7,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            button_frame,
            text="Delete",
            command=lambda r=rule: open_delete_window(
                r, config_window, parent_frame
            ),
            bootstyle="danger-outline",
            width=7,
        ).pack(side="left")

        ttk.Separator(rule_frame).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8)
        )

        fields = (
            ("Extensions", ", ".join(rule.get("extensions", [])) or "Any"),
            ("Keywords", ", ".join(rule.get("keywords", [])) or "None"),
            ("Destination", rule.get("destination", "Not set")),
        )
        for row, (label, value) in enumerate(fields, start=2):
            ttk.Label(
                rule_frame,
                text=label,
                bootstyle="secondary",
                width=12,
            ).grid(row=row, column=0, sticky="nw", pady=2)
            ttk.Label(
                rule_frame,
                text=value,
                wraplength=620,
                justify="left",
            ).grid(row=row, column=1, sticky="w", pady=2)

    _update_rule_order_controls(parent_frame)

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
    config_window = ttk.Window(themename="cosmo")
    config_window_instance = config_window # Store the instance
    config_window.title("Download Organizer")
    set_window_icon(config_window)
    
    config_window.protocol("WM_DELETE_WINDOW", config_window.withdraw)

    w, h = 960, 680
    ws, hs = config_window.winfo_screenwidth(), config_window.winfo_screenheight()
    x, y = (ws/2) - (w/2), (hs/2) - (h/2)
    config_window.geometry('%dx%d+%d+%d' % (w, h, x, y))
    config_window.minsize(760, 520)

    main_frame = ttk.Frame(config_window)
    main_frame.pack(fill="both", expand=True)

    header = ttk.Frame(main_frame, padding=(20, 18, 20, 10))
    header.pack(fill="x")
    ttk.Label(
        header,
        text="Download Organizer",
        font=("Segoe UI", 18, "bold"),
    ).pack(anchor="w")
    ttk.Label(
        header,
        text="Manage your sorting rules. Rules at the top are checked first.",
        bootstyle="secondary",
    ).pack(anchor="w", pady=(3, 0))
    ttk.Label(
        header,
        text="SORTING RULES",
        font=("Segoe UI", 9, "bold"),
        bootstyle="primary",
    ).pack(anchor="w", pady=(16, 0))

    toolbar = ttk.Frame(main_frame, padding=(20, 10, 20, 14))
    toolbar.pack(side="bottom", fill="x")
    ttk.Button(
        toolbar,
        text="Add rule",
        command=lambda: open_add_window(config_window, scrollable_frame),
        bootstyle="primary",
    ).pack(side="left", padx=(0, 8))
    ttk.Button(
        toolbar,
        text="Sort now",
        command=utils.file_sorter,
        bootstyle="success-outline",
    ).pack(side="left", padx=(0, 8))
    ttk.Button(
        toolbar,
        text="Preview",
        command=lambda: open_sort_preview(config_window),
        bootstyle="secondary-outline",
    ).pack(side="left", padx=(0, 8))
    ttk.Button(
        toolbar,
        text="Create folders",
        command=utils.create_folders,
        bootstyle="secondary-outline",
    ).pack(side="left")

    interval_frame = ttk.Frame(toolbar)
    interval_frame.pack(side="right")
    ttk.Label(interval_frame, text="Check every").pack(side="left", padx=(0, 6))
    interval_var = tk.StringVar(value=str(utils.get_interval()))
    interval_entry = ttk.Entry(interval_frame, textvariable=interval_var, width=5)
    interval_entry.pack(side="left", padx=(0, 4))
    ttk.Label(interval_frame, text="min").pack(side="left", padx=(0, 8))

    def apply_interval(var_to_use):
        try:
            new_interval = int(var_to_use.get())
            if new_interval > 0:
                utils.save_interval(new_interval)
            else:
                raise ValueError("Enter a number greater than zero.")
        except ValueError as error:
            messagebox.showerror(
                "Invalid interval",
                str(error) or "Enter a whole number greater than zero.",
                parent=config_window,
            )
        except Exception as error:
            utils.logger.exception("Could not save the sorting interval.")
            messagebox.showerror(
                "Could not save interval",
                str(error),
                parent=config_window,
            )
            
    ttk.Button(
        interval_frame,
        text="Apply",
        command=lambda: apply_interval(interval_var),
        bootstyle="primary-outline",
    ).pack(side="left")

    rules_container = ttk.Frame(main_frame)
    rules_container.pack(fill="both", expand=True)
    canvas = tk.Canvas(
        rules_container,
        highlightthickness=0,
        background=config_window.style.colors.bg,
    )
    scrollbar = ttk.Scrollbar(rules_container, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas, padding=(16, 8, 16, 16))

    scrollable_frame.bind(
        "<Configure>",
        lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas_window = canvas.create_window(
        (0, 0),
        window=scrollable_frame,
        anchor="nw",
    )
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind(
        "<Configure>",
        lambda event: canvas.itemconfigure(canvas_window, width=event.width),
    )
    canvas.bind_all(
        "<MouseWheel>",
        lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"),
    )
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    rules = utils.get_rules()
    if rules:
        create_rule_cards(scrollable_frame, rules)
    else:
        ttk.Label(
            scrollable_frame,
            text=(
                "Could not load the configuration."
                if rules is None
                else "No rules found. Add a rule to get started."
            ),
            bootstyle="secondary",
            padding=20,
        ).pack(anchor="center", pady=30)

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