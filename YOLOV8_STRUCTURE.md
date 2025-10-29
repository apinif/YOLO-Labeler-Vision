# YOLOv8 Directory Structure Guide

This document explains how the YOLO Labeler organizes your dataset according to YOLOv8 specifications.

## Why Separate Directories?

YOLOv8 (and many YOLO variants) expect images and labels to be in separate directories. This makes it easier to:
- Organize training/validation splits
- Share datasets without mixing file types
- Integrate with YOLOv8 training pipelines
- Keep your workspace clean and organized

## Automatic Directory Creation

The YOLO Labeler **automatically creates** the appropriate directory structure when you:
1. Open a directory with images
2. Save your first annotation

You don't need to manually create the labels directory!

## Directory Structures Supported

### Option 1: Parallel Directories (Recommended for YOLOv8)

**Best for:** Training with YOLOv8, Ultralytics projects

```
my_dataset/
├── images/
│   ├── train/
│   │   ├── img001.jpg
│   │   ├── img002.jpg
│   │   └── ...
│   └── val/
│       ├── img101.jpg
│       └── ...
└── labels/
    ├── train/
    │   ├── img001.txt
    │   ├── img002.txt
    │   └── ...
    └── val/
        ├── img101.txt
        └── ...
```

**How to use:**
- Point the labeler to: `my_dataset/images/train/`
- Labels will be saved to: `my_dataset/labels/train/`

### Option 2: Subdirectory Structure

**Best for:** Simple projects, single directory

```
my_project/
├── img001.jpg
├── img002.jpg
├── img003.jpg
└── labels/
    ├── img001.txt
    ├── img002.txt
    └── img003.txt
```

**How to use:**
- Point the labeler to: `my_project/`
- Labels will be saved to: `my_project/labels/`

## Working with Existing YOLOv8 Datasets

If you already have a YOLOv8 dataset structure, the labeler will:
1. Detect the existing `labels` directory
2. Load annotations from the correct location
3. Save new annotations to the same location

## Integration with YOLOv8

After labeling, your dataset is ready for YOLOv8 training!

### 1. Create a YAML configuration file

```yaml
# dataset.yaml
path: /path/to/my_dataset  # root directory
train: images/train
val: images/val

# Classes (copy from classes.txt)
names:
  0: person
  1: car
  2: bicycle
```

### 2. Train with YOLOv8

```python
from ultralytics import YOLO

# Load a model
model = YOLO('yolov8n.pt')

# Train the model
results = model.train(data='dataset.yaml', epochs=100)
```

## File Naming

- **Images:** Can have any name with supported extensions (.jpg, .png, etc.)
- **Labels:** Automatically named to match the image
  - `image001.jpg` → `image001.txt`
  - `photo.png` → `photo.txt`
  - `IMG_20231015.JPG` → `IMG_20231015.txt`

## Classes File

The `classes.txt` file is saved in your **image directory** (not in labels):

```
my_dataset/
├── classes.txt      # ← Saved here
├── images/
│   └── train/
└── labels/
    └── train/
```

This file contains one class name per line, where the line number is the class ID:
```
person    # ID: 0
car       # ID: 1
bicycle   # ID: 2
```

## Troubleshooting

### Labels not appearing?
- Check that you're loading from the correct directory
- Verify the `labels` directory exists parallel to your `images` directory
- Ensure label files have the same name as images (but .txt extension)

### YOLOv8 can't find labels?
- Verify your YAML file points to the correct paths
- Make sure the `labels` directory is parallel to `images`
- Check that class IDs in labels match your `names` in YAML

### Moving an existing dataset?
If you have labels next to images (old structure), organize them:
```bash
mkdir -p my_dataset/images my_dataset/labels
mv *.jpg my_dataset/images/
mv *.txt my_dataset/labels/
```

## Benefits of This Structure

✅ **YOLOv8 Compatible**: Works directly with Ultralytics YOLOv8  
✅ **Organized**: Clean separation of images and annotations  
✅ **Flexible**: Supports train/val splits easily  
✅ **Standard**: Follows machine learning dataset conventions  
✅ **Version Control**: Easy to .gitignore images while keeping labels  

## Example Workflow

1. **Create directory structure:**
   ```bash
   mkdir -p my_dataset/images/train
   # Copy your images to my_dataset/images/train/
   ```

2. **Label with YOLO Labeler:**
   - Open `my_dataset/images/train/`
   - Draw bounding boxes
   - Labels auto-save to `my_dataset/labels/train/`

3. **Create dataset YAML:**
   ```yaml
   path: /path/to/my_dataset
   train: images/train
   val: images/val
   names:
     0: person
     1: car
   ```

4. **Train:**
   ```python
   from ultralytics import YOLO
   model = YOLO('yolov8n.pt')
   model.train(data='dataset.yaml', epochs=100)
   ```

Done! Your dataset is properly structured and ready for training.

