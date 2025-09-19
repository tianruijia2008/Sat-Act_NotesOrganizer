import os
import logging
from typing import Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

class ImageFileHandler(FileSystemEventHandler):
    """
    Handler for image file events.
    """

    def __init__(self, callback: Callable[[str], None], image_extensions: Optional[list[str]] = None):
        """
        Initialize the image file handler.

        Args:
            callback (Callable[[str], None]): Function to call when an image file is created
            image_extensions (list[str], optional): List of image file extensions to watch
        """
        self.callback: Callable[[str], None] = callback
        self.image_extensions: list[str] = image_extensions or ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif']
        self.logger: logging.Logger = logging.getLogger(__name__)

    def on_created(self, event: FileSystemEvent):
        """
        Handle file creation events.

        Args:
            event: The file system event
        """
        if not event.is_directory:
            file_extension = os.path.splitext(event.src_path)[1].lower()
            if file_extension in self.image_extensions:
                self.logger.info(f"New image file detected: {event.src_path}")
                try:
                    # Ensure src_path is a string
                    file_path = str(event.src_path)
                    self.callback(file_path)
                except Exception as e:
                    self.logger.error(f"Error processing new image file {event.src_path}: {str(e)}")

class FileWatcher:
    """
    File watcher to monitor the raw image directory for new images.
    """

    def __init__(self, watch_directory: str, callback: Callable[[str], None],
                 image_extensions: Optional[list[str]] = None):
        """
        Initialize the file watcher.

        Args:
            watch_directory (str): Directory to watch for new files
            callback (Callable[[str], None]): Function to call when an image file is created
            image_extensions (list[str], optional): List of image file extensions to watch
        """
        self.watch_directory: str = watch_directory
        self.callback: Callable[[str], None] = callback
        self.image_extensions: list[str] = image_extensions or ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif']
        self.observer = Observer()
        self.logger: logging.Logger = logging.getLogger(__name__)

    def start(self):
        """
        Start watching the directory for new files.
        """
        if not os.path.exists(self.watch_directory):
            self.logger.warning(f"Watch directory does not exist: {self.watch_directory}")
            self.logger.info(f"Creating directory: {self.watch_directory}")
            os.makedirs(self.watch_directory, exist_ok=True)

        event_handler = ImageFileHandler(self.callback, self.image_extensions)
        _ = self.observer.schedule(event_handler, self.watch_directory, recursive=False)
        self.observer.start()
        self.logger.info(f"Started watching directory: {self.watch_directory}")

    def stop(self):
        """
        Stop watching the directory.
        """
        self.observer.stop()
        self.observer.join()
        self.logger.info("Stopped watching directory")

    def watch_once(self) -> list[str]:
        """
        Scan the directory once for existing image files.

        Returns:
            list[str]: List of image file paths
        """
        image_files: list[str] = []
        if os.path.exists(self.watch_directory):
            for filename in os.listdir(self.watch_directory):
                file_path = os.path.join(self.watch_directory, filename)
                if os.path.isfile(file_path):
                    file_extension = os.path.splitext(filename)[1].lower()
                    if file_extension in self.image_extensions:
                        image_files.append(file_path)

        self.logger.info(f"Found {len(image_files)} image files in {self.watch_directory}")
        return image_files

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    def process_new_image(image_path: str):
        """Example callback function to process new images."""
        print(f"Processing new image: {image_path}")

    # Initialize file watcher
    watcher = FileWatcher("data/raw", process_new_image)

    # Watch once for existing files
    existing_images = watcher.watch_once()
    for image_path in existing_images:
        process_new_image(image_path)

    # Start continuous watching (uncomment to use)
    # print("Starting continuous file watching. Press Ctrl+C to stop.")
    # try:
    #     watcher.start()
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     print("Stopping file watcher...")
    #     watcher.stop()
