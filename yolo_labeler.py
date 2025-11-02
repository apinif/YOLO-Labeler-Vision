#!/usr/bin/env python3
"""
YOLO Image Labeler
A simple GUI application for labeling images for YOLO model training
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, colorchooser
from tkinter import font as tkfont
from PIL import Image, ImageTk, ImageDraw
from pathlib import Path
import random


class YOLOLabeler:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO Image Labeler")
        self.root.geometry("1400x900")
        
        # Modern color scheme
        self.colors = {
            'bg_primary': '#2b2b2b',      # Dark gray background
            'bg_secondary': '#3c3c3c',   # Slightly lighter gray
            'bg_panel': '#1e1e1e',       # Dark panel background
            'bg_button': '#0078d4',      # Modern blue
            'bg_button_hover': '#005a9e', # Darker blue for hover
            'bg_button_danger': '#d13438', # Red for delete actions
            'bg_button_success': '#107c10', # Green for success actions
            'bg_button_warning': '#ffaa44', # Orange for warnings
            'text_primary': '#ffffff',    # White text
            'text_secondary': '#cccccc',  # Light gray text
            'text_muted': '#999999',      # Muted gray text
            'border': '#404040',          # Border color
            'canvas_bg': '#1a1a1a',       # Canvas background
        }
        
        # Modern fonts (with fallbacks for cross-platform compatibility)
        # Check available fonts
        available_fonts = list(tkfont.families())
        if 'Segoe UI' in available_fonts:
            font_family = 'Segoe UI'
        elif 'Ubuntu' in available_fonts:
            font_family = 'Ubuntu'
        elif 'DejaVu Sans' in available_fonts:
            font_family = 'DejaVu Sans'
        else:
            font_family = 'Helvetica'
        
        self.fonts = {
            'title': (font_family, 12, 'bold'),
            'heading': (font_family, 11, 'bold'),
            'body': (font_family, 10),
            'small': (font_family, 9),
            'button': (font_family, 9, 'bold'),
        }
        
        # Data structures
        self.image_dir = None
        self.image_files = []
        self.current_index = 0
        self.current_image = None
        self.photo = None
        
        # Supported image formats
        self.supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')
        
        # Classes and annotations
        self.classes = []  # List of class names
        self.class_colors = {}  # class_name -> color
        self.class_ids = {}  # class_name -> custom YOLO ID
        self.selected_class_index = None
        self.annotations = {}  # image_path -> list of {class_id, x1, y1, x2, y2}
        
        # Box editing state
        self.selected_box_index = None
        self.editing_box = False
        self.resizing_box = False
        self.resize_handle = None  # 'tl', 'tr', 'bl', 'br' for corners
        self.drag_start_x = None
        self.drag_start_y = None
        self.original_box = None
        
        # Drawing state
        self.drawing = False
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.temp_rect = None
        
        # Image display properties
        self.display_scale = 1.0
        self.display_offset_x = 0
        self.display_offset_y = 0
        self.display_width = 0
        self.display_height = 0
        
        # Initialize with some default classes
        self.add_class("person", "#FF0000", 0)
        self.add_class("car", "#00FF00", 1)
        self.add_class("bicycle", "#0000FF", 2)
        self.selected_class_index = 0
        
        # Configure root window background
        self.root.configure(bg=self.colors['bg_primary'])
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Top menu bar with modern styling
        menubar = tk.Menu(self.root, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                         activebackground=self.colors['bg_button'], activeforeground=self.colors['text_primary'])
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                           activebackground=self.colors['bg_button'], activeforeground=self.colors['text_primary'])
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Directory", command=self.open_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Save All Annotations", command=self.save_all_annotations)
        file_menu.add_command(label="Load Annotations", command=self.load_all_annotations)
        file_menu.add_command(label="Export Classes", command=self.export_classes)
        file_menu.add_command(label="Import Classes", command=self.import_classes)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                           activebackground=self.colors['bg_button'], activeforeground=self.colors['text_primary'])
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_help)
        
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        # Top info bar with modern styling
        info_frame = tk.Frame(main_frame, bg=self.colors['bg_panel'], relief=tk.FLAT, bd=0)
        info_frame.pack(fill=tk.X, pady=(0, 12))
        
        self.info_label = tk.Label(info_frame, text="No directory selected", 
                                   font=self.fonts['body'], bg=self.colors['bg_panel'],
                                   fg=self.colors['text_secondary'], anchor='w')
        self.info_label.pack(side=tk.LEFT, padx=12, pady=8)
        
        self.image_counter_label = tk.Label(info_frame, text="0 / 0", 
                                           font=self.fonts['body'], bg=self.colors['bg_panel'],
                                           fg=self.colors['text_primary'])
        self.image_counter_label.pack(side=tk.RIGHT, padx=12, pady=8)
        
        # Content area - split into canvas and side panel
        content_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        
        # Image display canvas (left side)
        canvas_frame = tk.Frame(content_frame, bg=self.colors['canvas_bg'], relief=tk.FLAT)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.colors['canvas_bg'], highlightthickness=0, 
                               cursor="cross", bd=0, relief=tk.FLAT)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Bind mouse events for drawing
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        
        # Right side panel with modern dark theme
        side_panel = tk.Frame(content_frame, width=320, bg=self.colors['bg_panel'], relief=tk.FLAT)
        side_panel.pack(side=tk.RIGHT, fill=tk.BOTH)
        side_panel.pack_propagate(False)
        
        # Classes section
        classes_label = tk.Label(side_panel, text="CLASSES", font=self.fonts['heading'], 
                                bg=self.colors['bg_panel'], fg=self.colors['text_primary'],
                                anchor='w')
        classes_label.pack(fill=tk.X, padx=16, pady=(16, 8))
        
        # Class list with scrollbar
        class_list_frame = tk.Frame(side_panel, bg=self.colors['bg_panel'])
        class_list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))
        
        class_scrollbar = tk.Scrollbar(class_list_frame, bg=self.colors['bg_secondary'],
                                       troughcolor=self.colors['bg_panel'], 
                                       activebackground=self.colors['bg_button'])
        class_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.class_listbox = tk.Listbox(class_list_frame, yscrollcommand=class_scrollbar.set, 
                                        height=8, font=self.fonts['body'],
                                        bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                        selectbackground=self.colors['bg_button'],
                                        selectforeground=self.colors['text_primary'],
                                        highlightthickness=0, bd=0,
                                        activestyle='none')
        self.class_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        class_scrollbar.config(command=self.class_listbox.yview)
        self.class_listbox.bind('<<ListboxSelect>>', self.on_class_select)
        
        # Class management buttons
        class_btn_frame = tk.Frame(side_panel, bg=self.colors['bg_panel'])
        class_btn_frame.pack(fill=tk.X, padx=12, pady=8)
        
        add_class_btn = self.create_modern_button(class_btn_frame, "Add Class", 
                                                  self.add_class_dialog, 
                                                  bg_color=self.colors['bg_button_success'])
        add_class_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        
        edit_class_btn = self.create_modern_button(class_btn_frame, "Edit ID", 
                                                   self.edit_class_id,
                                                   bg_color=self.colors['bg_button'])
        edit_class_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 2))
        
        remove_class_btn = self.create_modern_button(class_btn_frame, "Remove", 
                                                     self.remove_class,
                                                     bg_color=self.colors['bg_button_danger'])
        remove_class_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4, 0))
        
        # Current class indicator
        self.current_class_frame = tk.Frame(side_panel, bg=self.colors['bg_secondary'], 
                                           relief=tk.FLAT, bd=0)
        self.current_class_frame.pack(fill=tk.X, padx=12, pady=8)
        
        tk.Label(self.current_class_frame, text="Current:", bg=self.colors['bg_secondary'], 
                font=self.fonts['small'], fg=self.colors['text_muted']).pack(side=tk.LEFT, padx=12, pady=10)
        self.current_class_label = tk.Label(self.current_class_frame, text="None", 
                                           font=self.fonts['heading'], bg=self.colors['bg_secondary'],
                                           fg=self.colors['text_primary'])
        self.current_class_label.pack(side=tk.LEFT, padx=(0, 12), pady=10)
        
        # Separator
        separator = tk.Frame(side_panel, height=1, bg=self.colors['border'], relief=tk.FLAT)
        separator.pack(fill=tk.X, padx=12, pady=12)
        
        # Bounding boxes section
        boxes_label = tk.Label(side_panel, text="BOUNDING BOXES", font=self.fonts['heading'], 
                              bg=self.colors['bg_panel'], fg=self.colors['text_primary'],
                              anchor='w')
        boxes_label.pack(fill=tk.X, padx=16, pady=(0, 8))
        
        # Bounding box list with scrollbar
        box_list_frame = tk.Frame(side_panel, bg=self.colors['bg_panel'])
        box_list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))
        
        box_scrollbar = tk.Scrollbar(box_list_frame, bg=self.colors['bg_secondary'],
                                     troughcolor=self.colors['bg_panel'],
                                     activebackground=self.colors['bg_button'])
        box_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.box_listbox = tk.Listbox(box_list_frame, yscrollcommand=box_scrollbar.set,
                                      height=8, font=self.fonts['small'],
                                      bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                      selectbackground=self.colors['bg_button'],
                                      selectforeground=self.colors['text_primary'],
                                      highlightthickness=0, bd=0,
                                      activestyle='none')
        self.box_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        box_scrollbar.config(command=self.box_listbox.yview)
        
        # Box management buttons
        box_btn_frame = tk.Frame(side_panel, bg=self.colors['bg_panel'])
        box_btn_frame.pack(fill=tk.X, padx=12, pady=8)
        
        delete_box_btn = self.create_modern_button(box_btn_frame, "Delete Selected Box", 
                                                   self.delete_selected_box,
                                                   bg_color=self.colors['bg_button_warning'])
        delete_box_btn.pack(fill=tk.X)
        
        clear_all_btn = self.create_modern_button(box_btn_frame, "Clear All Boxes", 
                                                  self.clear_all_boxes,
                                                  bg_color=self.colors['bg_button_danger'])
        clear_all_btn.pack(fill=tk.X, pady=(8, 0))
        
        # Navigation controls
        control_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        control_frame.pack(fill=tk.X)
        
        self.prev_button = self.create_modern_button(control_frame, "← Previous", 
                                                     self.prev_image, 
                                                     state=tk.DISABLED,
                                                     width=18, height=2)
        self.prev_button.pack(side=tk.LEFT, padx=(0, 8))
        
        self.open_dir_button = self.create_modern_button(control_frame, "📁 Open Directory",
                                                         self.open_directory,
                                                         width=24, height=2,
                                                         bg_color=self.colors['bg_button'])
        self.open_dir_button.pack(side=tk.LEFT, expand=True, padx=4)
        
        self.next_button = self.create_modern_button(control_frame, "Next →", 
                                                     self.next_image,
                                                     state=tk.DISABLED,
                                                     width=18, height=2)
        self.next_button.pack(side=tk.LEFT, padx=(8, 0))
        
        # Keyboard bindings
        self.root.bind('<Left>', lambda e: self.prev_image())
        self.root.bind('<Right>', lambda e: self.next_image())
        self.root.bind('<Control-o>', lambda e: self.open_directory())
        self.root.bind('<Delete>', lambda e: self.delete_selected_box())
        self.root.bind('<BackSpace>', lambda e: self.delete_selected_box())
        self.root.bind('<Escape>', lambda e: self.deselect_box())
        self.root.bind('<Control-s>', lambda e: self.save_all_annotations())
        
        # Number keys for quick class selection (1-9)
        for i in range(1, 10):
            self.root.bind(str(i), lambda e, idx=i-1: self.select_class_by_index(idx))
        
        # Update class list
        self.update_class_list()
    
    def create_modern_button(self, parent, text, command, bg_color=None, state=tk.NORMAL, width=None, height=None):
        """Create a modern styled button"""
        if bg_color is None:
            bg_color = self.colors['bg_button']
        
        btn = tk.Button(parent, text=text, command=command, 
                       bg=bg_color, fg=self.colors['text_primary'],
                       font=self.fonts['button'], relief=tk.FLAT, bd=0,
                       cursor='hand2', state=state,
                       activebackground=self.colors['bg_button_hover'],
                       activeforeground=self.colors['text_primary'],
                       padx=12, pady=8)
        
        if width:
            btn.config(width=width)
        if height:
            btn.config(height=height)
        
        # Add hover effect
        def on_enter(e):
            if btn['state'] == tk.NORMAL:
                btn.config(bg=self.colors['bg_button_hover'])
        
        def on_leave(e):
            if btn['state'] == tk.NORMAL:
                btn.config(bg=bg_color)
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn
        
    def add_class(self, class_name=None, color=None, class_id=None):
        """Add a new class"""
        if class_name is None:
            return
        
        if class_name in self.classes:
            return
        
        if color is None:
            # Generate random color
            color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        
        if class_id is None:
            # Auto-assign next available ID
            class_id = len(self.classes)
        
        self.classes.append(class_name)
        self.class_colors[class_name] = color
        self.class_ids[class_name] = class_id
        
    def add_class_dialog(self):
        """Show dialog to add a new class"""
        class_name = simpledialog.askstring("Add Class", "Enter class name:")
        if class_name and class_name.strip():
            class_name = class_name.strip()
            if class_name in self.classes:
                messagebox.showwarning("Duplicate Class", 
                                      f"Class '{class_name}' already exists!")
                return
            
            # Ask for color
            color = colorchooser.askcolor(title="Choose class color")[1]
            if not color:
                color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            
            self.add_class(class_name, color)
            self.update_class_list()
            
            # Select the newly added class
            self.selected_class_index = len(self.classes) - 1
            self.class_listbox.selection_clear(0, tk.END)
            self.class_listbox.selection_set(self.selected_class_index)
            self.update_current_class_label()
            
    def remove_class(self):
        """Remove selected class"""
        if self.selected_class_index is None or self.selected_class_index >= len(self.classes):
            messagebox.showwarning("No Class Selected", "Please select a class to remove")
            return
        
        class_name = self.classes[self.selected_class_index]
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", 
                                   f"Delete class '{class_name}'?\nAll annotations with this class will be removed."):
            return
        
        # Remove annotations with this class
        class_id = self.selected_class_index
        for img_path in self.annotations:
            self.annotations[img_path] = [box for box in self.annotations[img_path] 
                                         if box['class_id'] != class_id]
            # Update class IDs for remaining boxes
            for box in self.annotations[img_path]:
                if box['class_id'] > class_id:
                    box['class_id'] -= 1
        
        # Remove class
        del self.class_colors[class_name]
        del self.class_ids[class_name]
        self.classes.pop(self.selected_class_index)
        
        # Update selection
        if self.classes:
            self.selected_class_index = min(self.selected_class_index, len(self.classes) - 1)
        else:
            self.selected_class_index = None
        
        self.update_class_list()
        self.display_current_image()
        
    def update_class_list(self):
        """Update the class list display"""
        self.class_listbox.delete(0, tk.END)
        for i, class_name in enumerate(self.classes):
            color = self.class_colors[class_name]
            class_id = self.class_ids[class_name]
            self.class_listbox.insert(tk.END, f"  [{class_id}] {class_name}")
            # Use class color with better contrast
            text_color = 'white' if self.is_dark_color(color) else 'black'
            self.class_listbox.itemconfig(i, bg=color, fg=text_color)
        
        if self.selected_class_index is not None and self.selected_class_index < len(self.classes):
            self.class_listbox.selection_set(self.selected_class_index)
        
        self.update_current_class_label()
        
    def is_dark_color(self, hex_color):
        """Check if a color is dark (for text contrast)"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        luminance = (0.299 * r + 0.587 * g + 0.114 * b)
        return luminance < 128
        
    def on_class_select(self, event):
        """Handle class selection"""
        selection = self.class_listbox.curselection()
        if selection:
            self.selected_class_index = selection[0]
            self.update_current_class_label()
            
    def update_current_class_label(self):
        """Update the current class label"""
        if self.selected_class_index is not None and self.selected_class_index < len(self.classes):
            class_name = self.classes[self.selected_class_index]
            color = self.class_colors[class_name]
            self.current_class_label.config(text=class_name, fg=color)
        else:
            self.current_class_label.config(text="None", fg=self.colors['text_muted'])
    
    def edit_class_id(self):
        """Edit the YOLO ID for the selected class"""
        if self.selected_class_index is None or self.selected_class_index >= len(self.classes):
            messagebox.showwarning("No Class Selected", "Please select a class to edit")
            return
        
        class_name = self.classes[self.selected_class_index]
        current_id = self.class_ids[class_name]
        
        new_id = simpledialog.askinteger("Edit Class ID", 
                                         f"Enter YOLO ID for '{class_name}':\n(Current: {current_id})",
                                         initialvalue=current_id,
                                         minvalue=0,
                                         maxvalue=999)
        
        if new_id is not None:
            self.class_ids[class_name] = new_id
            self.update_class_list()
            messagebox.showinfo("Updated", f"Class '{class_name}' now has YOLO ID: {new_id}")
            
    def on_mouse_down(self, event):
        """Handle mouse button press"""
        if not self.image_files:
            return
        
        # Convert screen coords to image coords
        img_x, img_y = self.screen_to_image_coords(event.x, event.y)
        if img_x is None:
            return
        
        # Check if clicking on an existing box
        image_path = str(self.image_files[self.current_index])
        if image_path in self.annotations:
            # Check for resize handle first (corners)
            for idx, box in enumerate(self.annotations[image_path]):
                handle = self.get_resize_handle(img_x, img_y, box)
                if handle:
                    self.resizing_box = True
                    self.selected_box_index = idx
                    self.resize_handle = handle
                    self.drag_start_x = img_x
                    self.drag_start_y = img_y
                    self.original_box = box.copy()
                    self.update_box_list()
                    return
            
            # Check if clicking inside a box (for moving)
            for idx, box in enumerate(self.annotations[image_path]):
                if self.point_in_box(img_x, img_y, box):
                    self.editing_box = True
                    self.selected_box_index = idx
                    self.drag_start_x = img_x
                    self.drag_start_y = img_y
                    self.original_box = box.copy()
                    self.display_current_image()
                    self.update_box_list()
                    # Highlight the box in the listbox
                    self.box_listbox.selection_clear(0, tk.END)
                    self.box_listbox.selection_set(idx)
                    return
        
        # Not clicking on a box, start drawing a new one
        if self.selected_class_index is None:
            return
        
        self.drawing = True
        self.start_x = event.x
        self.start_y = event.y
        self.selected_box_index = None
        
    def on_mouse_drag(self, event):
        """Handle mouse drag"""
        img_x, img_y = self.screen_to_image_coords(event.x, event.y)
        if img_x is None:
            return
        
        image_path = str(self.image_files[self.current_index])
        
        # Handle resizing
        if self.resizing_box and self.selected_box_index is not None:
            if image_path in self.annotations:
                box = self.annotations[image_path][self.selected_box_index]
                self.resize_box(box, img_x, img_y)
                self.display_current_image()
            return
        
        # Handle moving
        if self.editing_box and self.selected_box_index is not None:
            if image_path in self.annotations:
                box = self.annotations[image_path][self.selected_box_index]
                dx = img_x - self.drag_start_x
                dy = img_y - self.drag_start_y
                
                # Move the box
                box['x1'] = self.original_box['x1'] + dx
                box['y1'] = self.original_box['y1'] + dy
                box['x2'] = self.original_box['x2'] + dx
                box['y2'] = self.original_box['y2'] + dy
                
                # Clamp to image bounds
                img_width = self.current_image.width
                img_height = self.current_image.height
                box['x1'] = max(0, min(box['x1'], img_width - 1))
                box['y1'] = max(0, min(box['y1'], img_height - 1))
                box['x2'] = max(0, min(box['x2'], img_width - 1))
                box['y2'] = max(0, min(box['y2'], img_height - 1))
                
                self.display_current_image()
            return
        
        # Handle drawing new box
        if not self.drawing:
            return
        
        # Remove previous temporary rectangle
        if self.temp_rect:
            self.canvas.delete(self.temp_rect)
        
        # Draw temporary rectangle
        color = self.class_colors[self.classes[self.selected_class_index]]
        self.temp_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline=color, width=2, dash=(5, 5)
        )
        
    def on_mouse_up(self, event):
        """Handle mouse button release"""
        # Handle end of resizing
        if self.resizing_box:
            self.resizing_box = False
            self.resize_handle = None
            self.original_box = None
            # Auto-save after resize
            if self.image_files:
                self.save_annotation_for_image(self.image_files[self.current_index])
            return
        
        # Handle end of moving
        if self.editing_box:
            self.editing_box = False
            self.original_box = None
            # Auto-save after move
            if self.image_files:
                self.save_annotation_for_image(self.image_files[self.current_index])
            return
        
        # Handle end of drawing
        if not self.drawing:
            return
        
        self.drawing = False
        
        # Remove temporary rectangle
        if self.temp_rect:
            self.canvas.delete(self.temp_rect)
            self.temp_rect = None
        
        # Calculate bounding box coordinates
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        
        # Check if box is too small
        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            return
        
        # Convert screen coordinates to image coordinates
        img_x1, img_y1 = self.screen_to_image_coords(x1, y1)
        img_x2, img_y2 = self.screen_to_image_coords(x2, y2)
        
        if img_x1 is None:  # Image coordinates invalid
            return
        
        # Add annotation
        image_path = str(self.image_files[self.current_index])
        if image_path not in self.annotations:
            self.annotations[image_path] = []
        
        self.annotations[image_path].append({
            'class_id': self.selected_class_index,
            'x1': img_x1,
            'y1': img_y1,
            'x2': img_x2,
            'y2': img_y2
        })
        
        # Redraw image with annotations
        self.display_current_image()
        
        # Auto-save annotation for current image
        if self.image_files:
            self.save_annotation_for_image(self.image_files[self.current_index])
        
    def cancel_drawing(self):
        """Cancel current drawing operation"""
        if self.temp_rect:
            self.canvas.delete(self.temp_rect)
            self.temp_rect = None
        self.drawing = False
    
    def deselect_box(self):
        """Deselect the currently selected box"""
        self.selected_box_index = None
        self.editing_box = False
        self.resizing_box = False
        self.drawing = False
        if self.temp_rect:
            self.canvas.delete(self.temp_rect)
            self.temp_rect = None
        self.box_listbox.selection_clear(0, tk.END)
        self.display_current_image()
    
    def select_class_by_index(self, index):
        """Select a class by its index (for keyboard shortcuts)"""
        if 0 <= index < len(self.classes):
            self.selected_class_index = index
            self.class_listbox.selection_clear(0, tk.END)
            self.class_listbox.selection_set(index)
            self.class_listbox.see(index)
            self.update_current_class_label()
        
    def screen_to_image_coords(self, screen_x, screen_y):
        """Convert screen coordinates to image coordinates"""
        if not self.current_image:
            return None, None
        
        # Convert to image coordinates
        img_x = int((screen_x - self.display_offset_x) / self.display_scale)
        img_y = int((screen_y - self.display_offset_y) / self.display_scale)
        
        # Clamp to image bounds
        img_x = max(0, min(img_x, self.current_image.width - 1))
        img_y = max(0, min(img_y, self.current_image.height - 1))
        
        return img_x, img_y
        
    def image_to_screen_coords(self, img_x, img_y):
        """Convert image coordinates to screen coordinates"""
        screen_x = int(img_x * self.display_scale + self.display_offset_x)
        screen_y = int(img_y * self.display_scale + self.display_offset_y)
        return screen_x, screen_y
    
    def point_in_box(self, x, y, box):
        """Check if a point is inside a bounding box"""
        return box['x1'] <= x <= box['x2'] and box['y1'] <= y <= box['y2']
    
    def get_resize_handle(self, x, y, box):
        """Check if point is near a corner (resize handle) of the box"""
        # Define handle size (in image coordinates)
        handle_size = max(10, int(15 / self.display_scale))  # Scale handle size
        
        x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
        
        # Check corners
        if abs(x - x1) <= handle_size and abs(y - y1) <= handle_size:
            return 'tl'  # top-left
        if abs(x - x2) <= handle_size and abs(y - y1) <= handle_size:
            return 'tr'  # top-right
        if abs(x - x1) <= handle_size and abs(y - y2) <= handle_size:
            return 'bl'  # bottom-left
        if abs(x - x2) <= handle_size and abs(y - y2) <= handle_size:
            return 'br'  # bottom-right
        
        return None
    
    def resize_box(self, box, new_x, new_y):
        """Resize box based on the resize handle being dragged"""
        if self.resize_handle == 'tl':
            box['x1'] = new_x
            box['y1'] = new_y
        elif self.resize_handle == 'tr':
            box['x2'] = new_x
            box['y1'] = new_y
        elif self.resize_handle == 'bl':
            box['x1'] = new_x
            box['y2'] = new_y
        elif self.resize_handle == 'br':
            box['x2'] = new_x
            box['y2'] = new_y
        
        # Ensure x1 < x2 and y1 < y2
        if box['x1'] > box['x2']:
            box['x1'], box['x2'] = box['x2'], box['x1']
        if box['y1'] > box['y2']:
            box['y1'], box['y2'] = box['y2'], box['y1']
        
        # Clamp to image bounds
        img_width = self.current_image.width
        img_height = self.current_image.height
        box['x1'] = max(0, min(box['x1'], img_width - 1))
        box['y1'] = max(0, min(box['y1'], img_height - 1))
        box['x2'] = max(0, min(box['x2'], img_width - 1))
        box['y2'] = max(0, min(box['y2'], img_height - 1))
        
    def delete_selected_box(self):
        """Delete the selected bounding box"""
        selection = self.box_listbox.curselection()
        if not selection:
            return
        
        box_index = selection[0]
        image_path = str(self.image_files[self.current_index])
        
        if image_path in self.annotations and box_index < len(self.annotations[image_path]):
            self.annotations[image_path].pop(box_index)
            self.display_current_image()
            
            # Auto-save after deletion
            if self.image_files and self.image_dir:
                self.save_annotation_for_image(self.image_files[self.current_index])
            
    def clear_all_boxes(self):
        """Clear all bounding boxes for current image"""
        if not self.image_files:
            return
        
        if not messagebox.askyesno("Confirm Clear", 
                                   "Clear all bounding boxes for this image?"):
            return
        
        image_path = str(self.image_files[self.current_index])
        if image_path in self.annotations:
            self.annotations[image_path] = []
            self.display_current_image()
            
            # Auto-save after clearing
            if self.image_files and self.image_dir:
                self.save_annotation_for_image(self.image_files[self.current_index])
            
    def update_box_list(self):
        """Update the bounding box list"""
        self.box_listbox.delete(0, tk.END)
        
        if not self.image_files:
            return
        
        image_path = str(self.image_files[self.current_index])
        if image_path not in self.annotations:
            return
        
        for i, box in enumerate(self.annotations[image_path]):
            class_name = self.classes[box['class_id']]
            self.box_listbox.insert(tk.END, f"{i+1}. {class_name}")
            color = self.class_colors[class_name]
            self.box_listbox.itemconfig(i, fg=color)
    
    def open_directory(self):
        """Open a directory containing images"""
        directory = filedialog.askdirectory(title="Select Image Directory")
        
        if not directory:
            return
            
        self.image_dir = Path(directory)
        
        # Check for classes.txt file
        classes_file = self.image_dir / 'classes.txt'
        if classes_file.exists():
            response = messagebox.askyesno("Classes File Found", 
                                          "Found classes.txt in directory.\nLoad class definitions?")
            if response:
                try:
                    with open(classes_file, 'r') as f:
                        lines = f.readlines()
                    
                    # Clear existing classes
                    self.classes.clear()
                    self.class_colors.clear()
                    self.class_ids.clear()
                    self.annotations.clear()
                    
                    # Load new classes
                    colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', 
                             '#00FFFF', '#FF8800', '#8800FF', '#00FF88']
                    
                    for i, line in enumerate(lines):
                        class_name = line.strip()
                        if class_name:
                            color = colors[i % len(colors)] if i < len(colors) else \
                                   "#{:06x}".format(random.randint(0, 0xFFFFFF))
                            # Use line index as YOLO ID (standard YOLO format)
                            self.add_class(class_name, color, i)
                    
                    self.selected_class_index = 0 if self.classes else None
                    self.update_class_list()
                except Exception as e:
                    messagebox.showerror("Error Loading Classes", str(e))
        
        # Find all image files in the directory
        self.image_files = []
        for ext in self.supported_formats:
            self.image_files.extend(sorted(self.image_dir.glob(f'*{ext}')))
            self.image_files.extend(sorted(self.image_dir.glob(f'*{ext.upper()}')))
        
        # Remove duplicates and sort
        self.image_files = sorted(list(set(self.image_files)))
        
        if not self.image_files:
            messagebox.showwarning("No Images", 
                                  f"No supported image files found in {directory}")
            return
        
        # Reset index
        self.current_index = 0
        labels_dir = self.get_labels_dir()
        labels_path = labels_dir.name if labels_dir else "labels"
        self.info_label.config(text=f"Images: {self.image_dir.name} | Labels: {labels_path}")
        
        # Try to load existing annotations from labels directory
        annotations_found = False
        labels_dir = self.get_labels_dir()
        if labels_dir:
            for image_path in self.image_files:
                txt_filename = image_path.stem + '.txt'
                txt_path = labels_dir / txt_filename
                if txt_path.exists():
                    annotations_found = True
                    break
        
        if annotations_found and self.classes:
            response = messagebox.askyesno("Annotations Found", 
                                          "Found existing annotation files.\nLoad annotations?")
            if response:
                loaded_count = 0
                for image_path in self.image_files:
                    self.load_annotation_for_image(image_path)
                    if str(image_path) in self.annotations and self.annotations[str(image_path)]:
                        loaded_count += 1
                
                messagebox.showinfo("Load Complete", 
                                  f"Found {len(self.image_files)} images\n" +
                                  f"Loaded annotations for {loaded_count} images")
            else:
                labels_dir = self.get_labels_dir()
                messagebox.showinfo("Images Loaded", 
                              f"Found {len(self.image_files)} images\n\n" +
                              f"Labels will be saved to:\n{labels_dir}")
        else:
            labels_dir = self.get_labels_dir()
            messagebox.showinfo("Images Loaded", 
                              f"Found {len(self.image_files)} images\n\n" +
                              f"Labels will be saved to:\n{labels_dir}")
        
        # Display first image
        self.update_navigation_buttons()
        self.display_current_image()
        
    def display_current_image(self):
        """Display the current image on the canvas with bounding boxes"""
        if not self.image_files or self.current_index >= len(self.image_files):
            return
            
        image_path = self.image_files[self.current_index]
        
        try:
            # Load and display the image
            self.current_image = Image.open(image_path)
            
            # Get canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # If canvas hasn't been drawn yet, use default size
            if canvas_width <= 1:
                canvas_width = 1000
            if canvas_height <= 1:
                canvas_height = 600
            
            # Calculate scaling to fit image in canvas while maintaining aspect ratio
            img_width, img_height = self.current_image.size
            scale_w = canvas_width / img_width
            scale_h = canvas_height / img_height
            scale = min(scale_w, scale_h, 1.0)  # Don't scale up
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Store display properties for coordinate conversion
            self.display_scale = scale
            self.display_width = new_width
            self.display_height = new_height
            self.display_offset_x = (canvas_width - new_width) // 2
            self.display_offset_y = (canvas_height - new_height) // 2
            
            # Create a copy of the image to draw bounding boxes on
            display_image = self.current_image.copy()
            draw = ImageDraw.Draw(display_image)
            
            # Draw existing bounding boxes
            img_path_str = str(image_path)
            if img_path_str in self.annotations:
                for idx, box in enumerate(self.annotations[img_path_str]):
                    class_name = self.classes[box['class_id']]
                    color = self.class_colors[class_name]
                    
                    # Use thicker outline for selected box
                    width = 5 if idx == self.selected_box_index else 3
                    
                    # Draw rectangle
                    coords = [(box['x1'], box['y1']), (box['x2'], box['y2'])]
                    draw.rectangle(coords, outline=color, width=width)
                    
                    # Draw resize handles for selected box
                    if idx == self.selected_box_index:
                        handle_size = 8
                        # Top-left
                        draw.rectangle([box['x1'] - handle_size, box['y1'] - handle_size, 
                                      box['x1'] + handle_size, box['y1'] + handle_size], 
                                     fill=color, outline='white', width=2)
                        # Top-right
                        draw.rectangle([box['x2'] - handle_size, box['y1'] - handle_size,
                                      box['x2'] + handle_size, box['y1'] + handle_size],
                                     fill=color, outline='white', width=2)
                        # Bottom-left
                        draw.rectangle([box['x1'] - handle_size, box['y2'] - handle_size,
                                      box['x1'] + handle_size, box['y2'] + handle_size],
                                     fill=color, outline='white', width=2)
                        # Bottom-right
                        draw.rectangle([box['x2'] - handle_size, box['y2'] - handle_size,
                                      box['x2'] + handle_size, box['y2'] + handle_size],
                                     fill=color, outline='white', width=2)
                    
                    # Draw label background and text
                    label = class_name
                    # Use a default font size
                    bbox = draw.textbbox((box['x1'], box['y1'] - 20), label)
                    draw.rectangle([bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2], 
                                 fill=color)
                    text_color = 'white' if self.is_dark_color(color) else 'black'
                    draw.text((box['x1'], box['y1'] - 20), label, fill=text_color)
            
            # Resize image with annotations
            resized_image = display_image.resize((new_width, new_height), 
                                                 Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(resized_image)
            
            # Clear canvas and display image
            self.canvas.delete("all")
            x = self.display_offset_x + new_width // 2
            y = self.display_offset_y + new_height // 2
            self.canvas.create_image(x, y, image=self.photo, anchor=tk.CENTER)
            
            # Update counter
            self.image_counter_label.config(
                text=f"{self.current_index + 1} / {len(self.image_files)} - {image_path.name}"
            )
            
            # Update box list
            self.update_box_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
            
    def next_image(self):
        """Display the next image"""
        if self.current_index < len(self.image_files) - 1:
            # Save current image annotations before moving
            if self.image_files and self.image_dir:
                self.save_annotation_for_image(self.image_files[self.current_index])
            
            self.current_index += 1
            self.display_current_image()
            self.update_navigation_buttons()
            
    def prev_image(self):
        """Display the previous image"""
        if self.current_index > 0:
            # Save current image annotations before moving
            if self.image_files and self.image_dir:
                self.save_annotation_for_image(self.image_files[self.current_index])
            
            self.current_index -= 1
            self.display_current_image()
            self.update_navigation_buttons()
            
    def update_navigation_buttons(self):
        """Enable/disable navigation buttons based on current position"""
        if not self.image_files:
            self.prev_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            return
            
        # Enable/disable previous button
        if self.current_index > 0:
            self.prev_button.config(state=tk.NORMAL)
        else:
            self.prev_button.config(state=tk.DISABLED)
            
        # Enable/disable next button
        if self.current_index < len(self.image_files) - 1:
            self.next_button.config(state=tk.NORMAL)
        else:
            self.next_button.config(state=tk.DISABLED)
    
    def box_to_yolo_format(self, box, image_width, image_height):
        """Convert bounding box to YOLO format (normalized center coordinates)"""
        # Get box coordinates
        x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
        
        # Calculate center, width, height
        x_center = (x1 + x2) / 2.0
        y_center = (y1 + y2) / 2.0
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        # Normalize by image dimensions
        x_center_norm = x_center / image_width
        y_center_norm = y_center / image_height
        width_norm = width / image_width
        height_norm = height / image_height
        
        # Clamp values to [0, 1]
        x_center_norm = max(0.0, min(1.0, x_center_norm))
        y_center_norm = max(0.0, min(1.0, y_center_norm))
        width_norm = max(0.0, min(1.0, width_norm))
        height_norm = max(0.0, min(1.0, height_norm))
        
        # Use custom class ID instead of class index
        class_name = self.classes[box['class_id']]
        yolo_class_id = self.class_ids[class_name]
        
        return f"{yolo_class_id} {x_center_norm:.6f} {y_center_norm:.6f} {width_norm:.6f} {height_norm:.6f}"
    
    def yolo_to_box(self, yolo_line, image_width, image_height):
        """Convert YOLO format line to bounding box coordinates"""
        try:
            parts = yolo_line.strip().split()
            if len(parts) != 5:
                return None
            
            yolo_class_id = int(parts[0])
            x_center_norm = float(parts[1])
            y_center_norm = float(parts[2])
            width_norm = float(parts[3])
            height_norm = float(parts[4])
            
            # Map YOLO class ID to internal class index
            class_index = None
            for idx, class_name in enumerate(self.classes):
                if self.class_ids[class_name] == yolo_class_id:
                    class_index = idx
                    break
            
            # If class ID not found in our mapping, try to use it as direct index
            if class_index is None:
                if 0 <= yolo_class_id < len(self.classes):
                    class_index = yolo_class_id
                else:
                    return None  # Skip boxes with unknown class IDs
            
            # Denormalize coordinates
            x_center = x_center_norm * image_width
            y_center = y_center_norm * image_height
            width = width_norm * image_width
            height = height_norm * image_height
            
            # Calculate corner coordinates
            x1 = int(x_center - width / 2)
            y1 = int(y_center - height / 2)
            x2 = int(x_center + width / 2)
            y2 = int(y_center + height / 2)
            
            # Clamp to image bounds
            x1 = max(0, min(x1, image_width - 1))
            y1 = max(0, min(y1, image_height - 1))
            x2 = max(0, min(x2, image_width - 1))
            y2 = max(0, min(y2, image_height - 1))
            
            return {
                'class_id': class_index,
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2
            }
        except (ValueError, IndexError):
            return None
    
    def get_labels_dir(self):
        """Get the labels directory following YOLOv8 structure"""
        if not self.image_dir:
            return None
        
        # Check if we're in an 'images' directory - if so, use parallel 'labels' dir
        if self.image_dir.name == 'images' or 'images' in str(self.image_dir):
            # Navigate up and create labels directory
            parent = self.image_dir.parent
            labels_dir = parent / 'labels'
        else:
            # Create labels subdirectory in the same directory
            labels_dir = self.image_dir / 'labels'
        
        # Create directory if it doesn't exist
        labels_dir.mkdir(parents=True, exist_ok=True)
        return labels_dir
    
    def save_annotation_for_image(self, image_path):
        """Save annotation for a single image in YOLO format"""
        if not self.image_dir:
            return
        
        image_path_str = str(image_path)
        
        # Get labels directory
        labels_dir = self.get_labels_dir()
        if not labels_dir:
            return
        
        # Get annotation file path in labels directory
        txt_filename = image_path.stem + '.txt'
        txt_path = labels_dir / txt_filename
        
        # If no annotations, remove the txt file if it exists
        if image_path_str not in self.annotations or not self.annotations[image_path_str]:
            if txt_path.exists():
                txt_path.unlink()
            return
        
        # Load image to get dimensions
        try:
            with Image.open(image_path) as img:
                img_width, img_height = img.size
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return
        
        # Convert annotations to YOLO format
        yolo_lines = []
        for box in self.annotations[image_path_str]:
            yolo_line = self.box_to_yolo_format(box, img_width, img_height)
            yolo_lines.append(yolo_line)
        
        # Write to file
        try:
            with open(txt_path, 'w') as f:
                f.write('\n'.join(yolo_lines))
        except Exception as e:
            print(f"Error saving annotation file {txt_path}: {e}")
    
    def save_all_annotations(self):
        """Save all annotations to YOLO format files"""
        if not self.image_dir:
            messagebox.showwarning("No Directory", "Please open a directory first")
            return
        
        try:
            # Save annotations for all images
            saved_count = 0
            for image_path in self.image_files:
                self.save_annotation_for_image(image_path)
                if str(image_path) in self.annotations and self.annotations[str(image_path)]:
                    saved_count += 1
            
            # Save classes file
            self.export_classes(auto=True)
            
            labels_dir = self.get_labels_dir()
            labels_path = str(labels_dir) if labels_dir else "labels directory"
            
            messagebox.showinfo("Save Complete", 
                              f"Saved annotations for {saved_count} images\n" + 
                              f"Labels saved to: {labels_path}\n" +
                              f"Classes saved to classes.txt")
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving annotations: {str(e)}")
    
    def load_annotation_for_image(self, image_path):
        """Load annotation for a single image from YOLO format"""
        # Get labels directory
        labels_dir = self.get_labels_dir()
        if not labels_dir:
            return
        
        # Get annotation file path in labels directory
        txt_filename = image_path.stem + '.txt'
        txt_path = labels_dir / txt_filename
        
        if not txt_path.exists():
            return
        
        # Load image to get dimensions
        try:
            with Image.open(image_path) as img:
                img_width, img_height = img.size
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return
        
        # Read annotation file
        try:
            with open(txt_path, 'r') as f:
                lines = f.readlines()
            
            image_path_str = str(image_path)
            self.annotations[image_path_str] = []
            
            for line in lines:
                box = self.yolo_to_box(line, img_width, img_height)
                if box and 0 <= box['class_id'] < len(self.classes):
                    self.annotations[image_path_str].append(box)
        except Exception as e:
            print(f"Error loading annotation file {txt_path}: {e}")
    
    def load_all_annotations(self):
        """Load all annotations from YOLO format files"""
        if not self.image_dir:
            messagebox.showwarning("No Directory", "Please open a directory first")
            return
        
        if not self.classes:
            messagebox.showwarning("No Classes", 
                                  "Please import or add classes before loading annotations")
            return
        
        try:
            # Load annotations for all images
            loaded_count = 0
            for image_path in self.image_files:
                self.load_annotation_for_image(image_path)
                if str(image_path) in self.annotations and self.annotations[str(image_path)]:
                    loaded_count += 1
            
            # Refresh display
            self.display_current_image()
            
            messagebox.showinfo("Load Complete", 
                              f"Loaded annotations for {loaded_count} images")
        except Exception as e:
            messagebox.showerror("Load Error", f"Error loading annotations: {str(e)}")
    
    def export_classes(self, auto=False):
        """Export class names to classes.txt file"""
        if not self.image_dir and not auto:
            messagebox.showwarning("No Directory", "Please open a directory first")
            return
        
        if not self.classes:
            if not auto:
                messagebox.showwarning("No Classes", "No classes to export")
            return
        
        # Save to image directory or current directory
        if self.image_dir:
            classes_path = self.image_dir / 'classes.txt'
        else:
            classes_path = Path('classes.txt')
        
        try:
            with open(classes_path, 'w') as f:
                for class_name in self.classes:
                    f.write(f"{class_name}\n")
            
            if not auto:
                messagebox.showinfo("Export Complete", 
                                  f"Classes exported to {classes_path}")
        except Exception as e:
            if not auto:
                messagebox.showerror("Export Error", f"Error exporting classes: {str(e)}")
    
    def import_classes(self):
        """Import class names from classes.txt file"""
        # Ask user to select classes file
        file_path = filedialog.askopenfilename(
            title="Select classes.txt file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Clear existing classes
            if self.classes:
                if not messagebox.askyesno("Replace Classes", 
                                          "Replace existing classes?\nAll current annotations will be lost."):
                    return
                self.classes.clear()
                self.class_colors.clear()
                self.class_ids.clear()
                self.annotations.clear()
            
            # Load new classes
            colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', 
                     '#00FFFF', '#FF8800', '#8800FF', '#00FF88']
            
            for i, line in enumerate(lines):
                class_name = line.strip()
                if class_name:
                    color = colors[i % len(colors)] if i < len(colors) else \
                           "#{:06x}".format(random.randint(0, 0xFFFFFF))
                    # Use line index as YOLO ID (standard YOLO format)
                    self.add_class(class_name, color, i)
            
            # Update UI
            self.selected_class_index = 0 if self.classes else None
            self.update_class_list()
            
            messagebox.showinfo("Import Complete", 
                              f"Imported {len(self.classes)} classes")
        except Exception as e:
            messagebox.showerror("Import Error", f"Error importing classes: {str(e)}")
    
    def show_help(self):
        """Show help dialog with keyboard shortcuts"""
        help_text = """
YOLO Image Labeler - Keyboard Shortcuts

Navigation:
  ← / → : Previous/Next image
  Ctrl+O : Open directory
  Ctrl+S : Save all annotations

Drawing & Editing:
  1-9 : Quick select class (1 for first, 2 for second, etc.)
  Click & Drag : Draw new bounding box
  Click on Box : Select box for editing
  Drag Selected Box : Move box
  Drag Corner Handles : Resize box
  Delete/Backspace : Delete selected box
  Esc : Deselect/Cancel

Class Management:
  • Click on class in list to select it
  • Use "Edit ID" button to set custom YOLO class ID
  • Class IDs are saved in YOLO format files

YOLOv8 Directory Structure:
  • Images: Located in your selected directory
  • Labels: Automatically saved to 'labels' subdirectory
  • If images are in 'images' dir, labels go to parallel 'labels' dir
  • Classes: Saved as classes.txt in image directory

Tips:
  • Click inside a box to select and move it
  • Click on corners (handles) of selected box to resize
  • Selected boxes show corner handles and thicker outline
  • Annotations auto-save when navigating between images
"""
        messagebox.showinfo("Keyboard Shortcuts & Help", help_text)


def main():
    root = tk.Tk()
    app = YOLOLabeler(root)
    root.mainloop()


if __name__ == "__main__":
    main()

