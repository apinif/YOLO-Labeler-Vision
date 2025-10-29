# YOLO Image Labeler

A Python GUI application for labeling images to train YOLO object detection models.

## Features

### Current Features (v2.0)
- ✅ Open and browse image directories
- ✅ Display images one at a time
- ✅ Navigate between images using buttons or keyboard arrows
- ✅ Support for multiple image formats (JPG, PNG, BMP, GIF, TIFF)
- ✅ Automatic image scaling to fit display area
- ✅ Image counter showing current position
- ✅ **Draw bounding boxes by click and drag**
- ✅ **Edit existing bounding boxes** (move, resize, delete)
- ✅ **Visual resize handles on selected boxes**
- ✅ **Multiple class support with custom colors**
- ✅ **Custom YOLO class IDs** (not just sequential)
- ✅ **Add/remove classes dynamically**
- ✅ **Visual bounding box display with class labels**
- ✅ **Delete individual or all bounding boxes**
- ✅ **List all bounding boxes for current image**
- ✅ **Auto-save annotations in YOLO format** (.txt files)
- ✅ **Auto-load existing annotations**
- ✅ **Export/import class definitions** (classes.txt)
- ✅ **YOLO format support** (normalized center coordinates)
- ✅ **YOLOv8 directory structure** (separate labels directory)
- ✅ **Extensive keyboard shortcuts**

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python yolo_labeler.py
```

### Controls

#### Navigation
- **File → Open Directory** (or Ctrl+O): Select a directory containing images
- **Previous/Next buttons** (or Left/Right arrow keys): Navigate between images
- **File → Exit**: Close the application

#### Labeling
- **Click and Drag** on empty space: Draw a new bounding box for the selected class
- **Click on Box**: Select an existing box for editing
- **Drag Selected Box**: Move the box to a new position
- **Drag Corner Handles**: Resize the selected box
- **Select Class**: Click on a class in the Classes list to make it active
- **Number Keys (1-9)**: Quick select classes
- **Add Class**: Add a new class with custom name and color
- **Edit ID**: Set custom YOLO class ID for selected class
- **Remove Class**: Delete selected class and all its annotations
- **Delete Selected Box**: Remove the selected bounding box (Delete/Backspace key)
- **Clear All Boxes**: Remove all bounding boxes from current image
- **ESC key**: Deselect box / cancel current operation
- **Ctrl+S**: Save all annotations

#### Workflow
1. Open a directory with images (File → Open Directory)
2. If classes.txt exists, it will be loaded automatically
3. If annotation .txt files exist, they will be loaded automatically
4. Select or add a class from the right panel
5. Click and drag on the image to draw bounding boxes
6. Switch classes to label different objects
7. Navigate between images to label the entire dataset
8. Annotations are auto-saved as you work
9. Use File → Save All Annotations to ensure everything is saved

### YOLO Format & Directory Structure

Annotations are saved following **YOLOv8 specification**:

#### Directory Structure
```
your_dataset/
├── images/              # Your image files (or any directory name)
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
├── labels/              # Auto-created for annotations
│   ├── image1.txt
│   ├── image2.txt
│   └── ...
└── classes.txt          # Class definitions
```

**Key points:**
- Labels are saved in a **separate `labels` directory** (auto-created)
- If images are in an `images` directory, labels go to a parallel `labels` directory
- Otherwise, labels go to a `labels` subdirectory

See [YOLOV8_STRUCTURE.md](YOLOV8_STRUCTURE.md) for detailed information.

#### Annotation Format

**For each image `image.jpg`, a corresponding `labels/image.txt` file is created with:**
```
<class_id> <x_center> <y_center> <width> <height>
```

Where:
- `class_id`: Integer class ID (customizable via "Edit ID" button)
- `x_center`, `y_center`: Normalized coordinates of box center (0.0 to 1.0)
- `width`, `height`: Normalized dimensions of box (0.0 to 1.0)

**classes.txt file:**
```
person
car
bicycle
```

Each line corresponds to a class ID (line 0 = class 0, etc.)

## Requirements

- Python 3.7+
- Pillow (PIL)
- tkinter (usually included with Python)

## Image Formats Supported

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- GIF (.gif)
- TIFF (.tiff)

## Documentation

- **[FEATURES.md](FEATURES.md)** - Detailed feature documentation including editing capabilities
- **[YOLOV8_STRUCTURE.md](YOLOV8_STRUCTURE.md)** - Complete guide to YOLOv8 directory structure
- **Help Menu** - Built-in keyboard shortcuts reference (Help → Keyboard Shortcuts)

## New in v2.0

### Box Editing
- Click on any bounding box to select it
- Selected boxes show corner handles for resizing
- Drag inside a box to move it
- Drag corner handles to resize
- Delete key to remove selected box

### Custom Class IDs
- Set custom YOLO class IDs for each class
- No longer limited to sequential numbering
- Compatible with existing YOLO datasets

### YOLOv8 Structure
- Labels saved in separate `labels` directory
- Follows YOLOv8/Ultralytics standard structure
- Auto-creates directory structure
- Ready for YOLOv8 training

### Enhanced UX
- Keyboard shortcuts (1-9 for class selection)
- Visual feedback for selected boxes
- Auto-save on all editing operations
- Help menu with complete documentation

## License

MIT License - Feel free to use and modify as needed.

