# Image Viewer Program

This is a simple image viewing program that allows users to navigate through images in a folder, move or copy images to numbered subfolders, and delete images.

## Features

- Full-screen image display
- Navigation with left and right arrow keys
- Moving/Copying images to numbered subfolders (1-9)
- Deleting images
- Error handling for file operations and image loading
- On-screen messages for user feedback
- Help message (press 'H' to display)
- MOVE/COPY toggle controlled by the CAPS LOCK key
- Background processing for image move/copy operations

## Usage

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the program:
   ```
   python main.py [folder_path]
   ```
   If no folder path is provided, the current working directory will be used.

3. Controls:
   - Left/Right arrow keys: Navigate between images
   - Number keys (1-9): Move/Copy image to corresponding subfolder
   - Delete key: Delete the current image
   - 'H' key: Display help message
   - CAPS LOCK: Toggle between MOVE and COPY mode
   - 'Q' key: Quit the program

## Requirements

See `requirements.txt` for the list of required packages.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
