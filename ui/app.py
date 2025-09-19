import streamlit as st
import os
import sys
import time
import logging
import shutil
from PIL import Image
import tempfile
import datetime
from typing import Union, Optional

# Add the parent directory to the path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ocr_processor import OCRProcessor
from src.ai_processor import AIProcessor
from src.notes_saver import NotesSaver
from src.camera_utils import enhance_image_for_text, detect_text_focus_quality, show_camera_help, process_camera_image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="SAT/ACT Notes Organizer",
    page_icon="📚",
    layout="wide"
)

def clear_processed_data():
    """Clear all processed data (notes and vector database) while preserving raw images."""
    try:
        # Show confirmation dialog
        st.sidebar.warning("⚠️ This will delete all processed data!")
        st.sidebar.info("Raw images in data/raw/ will be preserved.")

        # Show current directory status
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        st.sidebar.subheader("Current Status:")

        # Check notes directory
        notes_dir = os.path.join(project_root, "data", "notes")
        if os.path.exists(notes_dir) and os.path.isdir(notes_dir):
            notes_count = len([f for f in os.listdir(notes_dir) if f.endswith('.md')])
            st.sidebar.text(f"📝 Notes: {notes_count} files")
        else:
            st.sidebar.text("📝 Notes: Directory not found")

        # Check vector DB directory
        vector_db_dir = os.path.join(project_root, "data", "vector_db")
        if os.path.exists(vector_db_dir) and os.path.isdir(vector_db_dir):
            vector_files = len(os.listdir(vector_db_dir))
            st.sidebar.text(f"🗂️ Vector DB: {vector_files} files")
        else:
            st.sidebar.text("🗂️ Vector DB: Directory not found")

        # Check OCR directory
        ocr_dir = os.path.join(project_root, "data", "ocr")
        if os.path.exists(ocr_dir) and os.path.isdir(ocr_dir):
            ocr_files = len(os.listdir(ocr_dir))
            st.sidebar.text(f"🔍 OCR: {ocr_files} files")
        else:
            st.sidebar.text("🔍 OCR: Directory not found")

        # Create columns for buttons
        col1, col2 = st.sidebar.columns(2)

        if col1.button("Confirm Clear", type="primary", key="confirm_clear"):
            # Get absolute paths from project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

            # Debug: Show what directories we're trying to clear
            st.sidebar.info(f"Project root: {project_root}")

            cleared_count = 0

            # Clear notes directory
            notes_dir = os.path.join(project_root, "data", "notes")
            st.sidebar.info(f"Checking notes dir: {notes_dir}")
            if os.path.exists(notes_dir):
                try:
                    files_before = len(os.listdir(notes_dir)) if os.path.isdir(notes_dir) else 0
                    shutil.rmtree(notes_dir)
                    os.makedirs(notes_dir, exist_ok=True)
                    st.sidebar.success(f"✅ Notes directory cleared ({files_before} files removed)")
                    cleared_count += 1
                except Exception as e:
                    st.sidebar.error(f"Error clearing notes: {str(e)}")
            else:
                st.sidebar.info("Notes directory doesn't exist")

            # Clear vector database directory
            vector_db_dir = os.path.join(project_root, "data", "vector_db")
            st.sidebar.info(f"Checking vector DB dir: {vector_db_dir}")
            if os.path.exists(vector_db_dir):
                try:
                    files_before = len(os.listdir(vector_db_dir)) if os.path.isdir(vector_db_dir) else 0
                    shutil.rmtree(vector_db_dir)
                    os.makedirs(vector_db_dir, exist_ok=True)
                    st.sidebar.success(f"✅ Vector database cleared ({files_before} files removed)")
                    cleared_count += 1
                except Exception as e:
                    st.sidebar.error(f"Error clearing vector DB: {str(e)}")
            else:
                st.sidebar.info("Vector DB directory doesn't exist")

            # Clear OCR directory
            ocr_dir = os.path.join(project_root, "data", "ocr")
            st.sidebar.info(f"Checking OCR dir: {ocr_dir}")
            if os.path.exists(ocr_dir):
                try:
                    files_before = len(os.listdir(ocr_dir)) if os.path.isdir(ocr_dir) else 0
                    shutil.rmtree(ocr_dir)
                    os.makedirs(ocr_dir, exist_ok=True)
                    st.sidebar.success(f"✅ OCR directory cleared ({files_before} files removed)")
                    cleared_count += 1
                except Exception as e:
                    st.sidebar.error(f"Error clearing OCR: {str(e)}")
            else:
                st.sidebar.info("OCR directory doesn't exist")

            # Clear results in session state
            if 'results' in st.session_state:
                st.session_state.results = []
            if 'uploaded_images' in st.session_state:
                st.session_state.uploaded_images = []
            if 'processing' in st.session_state:
                st.session_state.processing = False

            # Reset clear_data flag
            st.session_state.clear_data = False

            if cleared_count > 0:
                st.sidebar.success(f"🎉 Successfully cleared {cleared_count} directories!")
            else:
                st.sidebar.warning("No directories were found to clear")

            time.sleep(2)
            st.rerun()

        if col2.button("Cancel", type="secondary", key="cancel_clear"):
            st.session_state.clear_data = False
            st.rerun()

    except Exception as e:
        st.sidebar.error(f"Error clearing data: {str(e)}")
        logger.error(f"Error clearing processed data: {str(e)}")
        st.session_state.clear_data = False

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'results' not in st.session_state:
    st.session_state.results = []
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
if 'processing_progress' not in st.session_state:
    st.session_state.processing_progress = 0
if 'current_step' not in st.session_state:
    st.session_state.current_step = ""
if 'camera_image' not in st.session_state:
    st.session_state.camera_image = None

def save_camera_image(image_data) -> Optional[str]:
    """Save camera image to raw folder with timestamp filename."""
    try:
        # Create raw directory if it doesn't exist
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        raw_dir = os.path.join(project_root, "data", "raw")
        os.makedirs(raw_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"camera_{timestamp}.png"
        file_path = os.path.join(raw_dir, filename)

        # Save image
        image = Image.open(image_data)
        image.save(file_path, "PNG")

        return file_path
    except Exception as e:
        st.error(f"Error saving camera image: {str(e)}")
        logger.error(f"Error saving camera image: {str(e)}")
        return None

def main():
    st.title("📚 SAT/ACT Notes Organizer")

    # Add configuration sidebar
    with st.sidebar:
        st.header("Configuration")
        st.markdown("Adjust processing options:")

        preprocess_option = st.checkbox("Preprocess Images", value=True,
                                       help="Apply image preprocessing to improve OCR accuracy")
        watch_mode = st.checkbox("Watch Mode", value=False,
                                help="Continuously monitor for new images")
        show_debug = st.checkbox("Show Debug Info", value=False,
                                help="Display detailed processing information")

        st.markdown("---")
        st.header("Data Management")

        # Add clear data button
        if st.button("Clear All Processed Data", type="secondary",
                    help="Delete all notes and vector database (raw images preserved)",
                    key="main_clear_button"):
            st.session_state.clear_data = True

        if st.session_state.get('clear_data', False):
            clear_processed_data()

        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This tool helps organize SAT/ACT study materials by:
        1. Extracting text from images
        2. Classifying content as notes or wrong questions
        3. Generating structured markdown files
        """)

    st.markdown("""
    Upload your SAT/ACT study materials images and automatically generate organized notes.
    The system will extract text, classify content, and create structured markdown files.
    """)

    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["Upload Images", "Processing Status", "View Results", "Camera Capture"])

    with tab1:
        upload_section(str(preprocess_option).lower())

    with tab2:
        processing_section()

    with tab3:
        results_section(show_debug)

    with tab4:
        camera_section()

def upload_section(preprocess_option: Union[str, bool]):
    st.header("Upload Study Material Images")

    # Store preprocess option in session state
    st.session_state.preprocess_option = preprocess_option

    # File uploader
    uploaded_files = st.file_uploader(
        "Choose images to process",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.subheader("Image Preview")
        cols = st.columns(3)

        for i, uploaded_file in enumerate(uploaded_files):
            with cols[i % 3]:
                # Display image preview
                image = Image.open(uploaded_file)
                st.image(image, caption=uploaded_file.name, use_column_width=True)

                # Show file info
                st.caption(f"Size: {uploaded_file.size / 1024:.1f} KB")

                # Save to temporary file for processing
                temp_dir = tempfile.mkdtemp()
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Store in session state
                if 'uploaded_images' not in st.session_state:
                    st.session_state.uploaded_images = []

                st.session_state.uploaded_images.append({
                    'name': uploaded_file.name,
                    'path': temp_path,
                    'size': uploaded_file.size
                })

        # Process button
        if st.button("Process Images", type="primary", disabled=st.session_state.processing):
            if 'uploaded_images' in st.session_state and st.session_state.uploaded_images:
                st.session_state.processing = True
                st.session_state.results = []
                st.session_state.processing_progress = 0
                process_images()
            else:
                st.warning("Please upload at least one image to process.")
    else:
        st.info("Upload PNG, JPG, or JPEG images of your SAT/ACT study materials.")

def process_images():
    try:
        # Get preprocess option from session state
        preprocess_option = st.session_state.get('preprocess_option', True)

        # Initialize processors
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        ocr_processor = OCRProcessor()
        ai_processor = AIProcessor(config_path)
        notes_saver = NotesSaver("data/notes")

        # Test AI connection first
        st.session_state.current_status = "Testing AI connection..."
        st.session_state.current_step = "Testing AI connection"
        st.session_state.processing_progress = 5
        time.sleep(0.5)  # Small delay to show status update

        connection_success = ai_processor.test_connection()
        if not connection_success:
            st.error("Failed to connect to AI API. Please check your configuration.")
            st.session_state.processing = False
            return

        # Process each image
        total_images = len(st.session_state.uploaded_images)
        for i, image_info in enumerate(st.session_state.uploaded_images):
            if not st.session_state.processing:
                break

            image_name = image_info['name']
            image_path = image_info['path']

            # Update status
            st.session_state.current_status = f"Processing image {i+1}/{total_images}: {image_name}"
            st.session_state.current_image = image_name
            st.session_state.processing_progress = 10 + int((i / total_images) * 80)

            try:
                # Step 1: Extract text using OCR
                st.session_state.current_step = "OCR Extraction"
                st.session_state.processing_progress = 15 + int((i / total_images) * 20)
                # Handle preprocess option conversion
                preprocess_bool = preprocess_option if isinstance(preprocess_option, bool) else preprocess_option.lower() == "true"
                ocr_result = ocr_processor.extract_text(image_path, preprocess=preprocess_bool)
                ocr_text, doc_id = ocr_result

                if not ocr_text.strip():
                    st.warning(f"No text extracted from {image_name}")
                    continue

                # Step 2: Classify content using AI
                st.session_state.current_step = "AI Classification"
                st.session_state.processing_progress = 35 + int((i / total_images) * 30)
                classification_result = ai_processor.classify_content(ocr_text)

                # Step 3: Save individual classification result
                st.session_state.current_step = "Saving Results"
                st.session_state.processing_progress = 65 + int((i / total_images) * 25)
                saved_path = notes_saver.save_classification_result(ocr_text, classification_result, image_name)

                # Store result
                st.session_state.results.append({
                    'image_name': image_name,
                    'image_path': image_path,
                    'ocr_text': ocr_text,
                    'classification': classification_result,
                    'saved_path': saved_path
                })

            except Exception as e:
                st.error(f"Error processing {image_name}: {str(e)}")
                logger.error(f"Error processing {image_name}: {str(e)}")

        # Processing complete
        st.session_state.processing = False
        st.session_state.current_status = "Processing complete!"
        st.session_state.current_step = "Done"
        st.session_state.processing_progress = 100
        st.success("All images processed successfully!")

    except Exception as e:
        st.error(f"Error during processing: {str(e)}")
        logger.error(f"Error during processing: {str(e)}")
        st.session_state.processing = False

def processing_section():
    st.header("Processing Status")

    if st.session_state.processing:
        # Show progress bar
        st.progress(st.session_state.processing_progress)

        # Show current status
        if 'current_status' in st.session_state:
            st.subheader(st.session_state.current_status)

        # Show current step with spinner
        if 'current_step' in st.session_state:
            st.markdown(f"**Current step:** {st.session_state.current_step}")
            with st.spinner("Processing..."):
                time.sleep(0.1)  # This is just to show the spinner

        # Show current image
        if st.session_state.current_image:
            st.caption(f"Currently processing: {st.session_state.current_image}")

    else:
        if 'current_status' in st.session_state and st.session_state.current_status == "Processing complete!":
            st.success(st.session_state.current_status)
            st.progress(100)
        else:
            st.info("No processing in progress. Upload images and click 'Process Images' to start.")

def results_section(show_debug: bool):
    st.header("Processing Results")

    if st.session_state.results:
        # Show summary
        st.subheader(f"Processed {len(st.session_state.results)} images")

        # Display results in tabs
        result_tabs = st.tabs([result['image_name'] for result in st.session_state.results])

        for i, (tab, result) in enumerate(zip(result_tabs, st.session_state.results)):
            with tab:
                # Create columns for image and results
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Original Image")
                    image = Image.open(result['image_path'])
                    st.image(image, use_column_width=True)

                    # Image info
                    st.caption(f"File: {result['image_name']}")
                    st.caption(f"Size: {os.path.getsize(result['image_path']) / 1024:.1f} KB")

                with col2:
                    st.subheader("Classification Result")
                    classification = result['classification']
                    st.metric("Content Type", classification.get('classification', 'Unknown').title())
                    st.metric("Confidence", f"{classification.get('confidence', 0.0):.2f}")
                    st.write(f"**Reasoning:** {classification.get('reasoning', 'No reasoning provided')}")

                    if 'related_to_context' in classification:
                        st.write(f"**Related to Context:** {classification.get('related_to_context', '')}")

                # Show extracted text and saved results
                st.subheader("Extracted Content")
                with st.expander("View Extracted Text"):
                    st.text(result['ocr_text'])

                # Show saved markdown file content if it exists
                if os.path.exists(result['saved_path']):
                    st.subheader("Generated Markdown File")
                    with st.expander("View Generated Markdown"):
                        try:
                            with open(result['saved_path'], 'r', encoding='utf-8') as f:
                                markdown_content = f.read()
                                st.markdown(markdown_content)
                        except Exception as e:
                            st.error(f"Error reading markdown file: {str(e)}")

                # Show file path
                st.caption(f"Saved to: `{result['saved_path']}`")

                # Option to download the markdown file
                if os.path.exists(result['saved_path']):
                    with open(result['saved_path'], 'r', encoding='utf-8') as f:
                        st.download_button(
                            label="Download Markdown File",
                            data=f.read(),
                            file_name=os.path.basename(result['saved_path']),
                            mime="text/markdown"
                        )

                # Show debug information if enabled
                if show_debug:
                    st.subheader("Debug Information")
                    with st.expander("View Debug Details"):
                        st.write("**Classification Result (Raw):**")
                        st.json(result['classification'])
                        st.write("**File Path:**", result['saved_path'])
                        st.write("**Image Path:**", result['image_path'])
    else:
        st.info("No results available. Process some images to see results here.")

def camera_section():
    st.header("📸 Enhanced Camera Capture")

    # Show helpful tips
    show_camera_help()

    # Add mobile camera optimization script
    st.markdown("""
    <script>
    // Optimize camera for document scanning on mobile
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const constraints = {
            video: {
                focusMode: { ideal: "continuous" },
                facingMode: { ideal: "environment" },
                width: { ideal: 1920 },
                height: { ideal: 1080 }
            }
        };
    }
    </script>
    """, unsafe_allow_html=True)

    st.markdown("### 📱 Camera Instructions:")
    st.info("🎯 **Before taking the photo:** Tap on the document in your camera view to focus, then take the picture")

    # Add enable checkbox
    enable = st.checkbox("Enable camera", value=True, key="camera_enable")

    # Camera input widget with better instructions
    picture = st.camera_input(
        "Take a picture of your notes or questions",
        disabled=not enable,
        key="camera_input",
        help="Tap on the document in the camera view to focus before capturing"
    )

    if picture:
        # Process and analyze the image
        enhanced_image, focus_info = process_camera_image(picture)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.image(enhanced_image, caption="Enhanced Image (Ready for OCR)", use_column_width=True)

        with col2:
            st.markdown("### Image Analysis")

            # Show focus quality
            if focus_info['score'] >= 3:
                st.success(f"✅ **Quality:** {focus_info['quality']}")
                st.markdown("Perfect for text recognition!")
            elif focus_info['score'] == 2:
                st.warning(f"⚠️ **Quality:** {focus_info['quality']}")
                st.markdown("Usable, but consider retaking for best results")
            else:
                st.error(f"❌ **Quality:** {focus_info['quality']}")
                st.markdown("Please retake with better focus")

            st.caption(f"Focus score: {focus_info.get('variance', 0):.1f}")

        # Action buttons
        st.markdown("### Actions")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("💾 Save Enhanced Image", key="save_camera"):
                file_path = save_camera_image(picture)
                if file_path:
                    st.success(f"Image saved to: {os.path.basename(file_path)}")
                else:
                    st.error("Failed to save image")

        with col2:
            if st.button("🔍 Process This Image", key="process_camera"):
                file_path = save_camera_image(picture)
                if file_path:
                    st.success("Added to processing queue!")
                    # Store in session state for processing
                    if 'uploaded_images' not in st.session_state:
                        st.session_state.uploaded_images = []

                    st.session_state.uploaded_images.append({
                        'name': os.path.basename(file_path),
                        'path': file_path,
                        'size': picture.size if hasattr(picture, 'size') else len(picture.getvalue())
                    })

                    # Switch to processing tab
                    st.session_state.processing = True
                    st.session_state.results = []
                    st.session_state.processing_progress = 0
                    st.rerun()
                else:
                    st.error("Failed to save image for processing")

        with col3:
            if st.button("📸 Take Another", key="reset_camera"):
                st.session_state.pop("camera_input", None)
                st.rerun()

        # Show tips for improvement if quality is low
        if focus_info['score'] < 3:
            st.markdown("### 💡 Tips to Improve:")
            st.markdown("• **Tap to focus** on the document before capturing")
            st.markdown("• **Get closer** (6-12 inches from the text)")
            st.markdown("• **Use better lighting** (avoid shadows)")
            st.markdown("• **Keep phone steady** (use both hands)")
            st.markdown("• **Make sure document is flat** and phone is parallel")

if __name__ == "__main__":
    main()
