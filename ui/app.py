import streamlit as st
import os
import sys
import time
from PIL import Image

# Add the parent directory to the path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Ensure project root is in Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # Import from new modular structure
    from services.note_processing_service import NoteProcessingService
    from services.ocr_service import OCRService
    from services.storage_service import StorageService
    from services.ai_service import AIService
    from src.utils import get_resource_path, get_folder_size
    from data.models.note import ImageInfo

    # Initialize services
    ocr_service = OCRService()
    ai_service = AIService()
    storage_service = StorageService()
    processing_service = NoteProcessingService()
except ImportError as e:
    st.error(f"❌ Import error: {e}")
    st.error("Please make sure all required modules are installed and the project structure is correct.")
    st.stop()
except Exception as e:
    st.error(f"❌ Service initialization error: {e}")
    st.error("There was a problem initializing the application services.")
    st.stop()

# Set page configuration with mobile-friendly settings
st.set_page_config(
    page_title="SAT/ACT Notes Organizer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add mobile-friendly CSS
st.markdown(
    """
    <style>
    .stApp {
        margin: 0;
        max-width: 100%;
        overflow-x: hidden;
    }
    .stFileUploader > div > div > div > div {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 20px;
    }
    /* Mobile-specific styles */
    @media (max-width: 768px) {
        .stApp {
            padding: 0.5rem;
        }
        .stFileUploader {
            width: 100%;
        }
        .stSidebar {
            width: 100% !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

def initialize_session_state():
    """Initialize session state variables."""
    if 'uploaded_images' not in st.session_state:
        st.session_state.uploaded_images = []
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'show_file_browser' not in st.session_state:
        st.session_state.show_file_browser = False
    if 'selected_images' not in st.session_state:
        st.session_state.selected_images = []
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    if 'ocr_results' not in st.session_state:
        st.session_state.ocr_results = {}
    if 'debug_confirmed' not in st.session_state:
        st.session_state.debug_confirmed = set()

def upload_section():
    """Handle file upload section."""
    st.header("📤 Upload Images")

    # Show current collection status
    existing_count = len(st.session_state.uploaded_images) if hasattr(st.session_state, 'uploaded_images') else 0
    if existing_count > 0:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(f"📁 You currently have {existing_count} image{'s' if existing_count != 1 else ''} in your collection")
        with col2:
            if st.button("🗑️ Clear Collection", help="Remove all images and start fresh"):
                st.session_state.uploaded_images = []
                st.session_state.selected_images = []
                # Clear temp directory using storage service
                storage_service.clear_temp_directory()
                st.success("Collection cleared!")
                st.rerun()

    uploaded_files = st.file_uploader(
        "Choose image files",
        accept_multiple_files=True,
        type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
        help="Select multiple images to upload. They will be added to your collection."
    )

    # Show newly selected files for upload (if any)
    if uploaded_files:
        st.subheader(f"📋 New Images Ready to Upload ({len(uploaded_files)})")
        cols = st.columns(min(len(uploaded_files), 3))

        valid_files = []
        for idx, uploaded_file in enumerate(uploaded_files):
            with cols[idx % 3]:
                try:
                    # Validate file size (max 10MB)
                    if uploaded_file.size > 10 * 1024 * 1024:
                        st.error(f"File {uploaded_file.name} is too large (>10MB)")
                        continue

                    # Display image preview directly from uploaded file
                    uploaded_file.seek(0)  # Reset pointer
                    image = Image.open(uploaded_file)

                    # Convert to RGB if needed (handles RGBA, P mode issues)
                    if image.mode in ('RGBA', 'P'):
                        image = image.convert('RGB')

                    st.image(image, caption=f"🆕 {uploaded_file.name}", use_container_width=True)

                    # Display image quality assessment
                    try:
                        # Save temporary file to assess quality
                        temp_assessment_path = os.path.join(get_resource_path('data/temp'), f"temp_assess_{uploaded_file.name}")
                        os.makedirs(os.path.dirname(temp_assessment_path), exist_ok=True)
                        uploaded_file.seek(0)
                        with open(temp_assessment_path, 'wb') as f:
                            f.write(uploaded_file.read())

                        # Assess image quality
                        quality_info = ocr_service.assess_image_quality(temp_assessment_path)

                        # Check orientation
                        orientation_info = ocr_service.detect_orientation(temp_assessment_path)

                        # Clean up temporary file
                        if os.path.exists(temp_assessment_path):
                            os.remove(temp_assessment_path)

                        # Display quality grade with color coding
                        grade_color = {
                            'A': '🟢',  # Excellent
                            'B': '🔵',  # Good
                            'C': '🟡',  # Fair
                            'D': '🟠',  # Poor
                            'F': '🔴',  # Very Poor
                        }.get(quality_info.grade, '⚪')

                        # Display orientation info
                        orientation_text = ""
                        if orientation_info.needs_rotation:
                            method_text = f" ({orientation_info.method or 'auto'})" if orientation_info.method else ""
                            orientation_text = f" | 🔁 Needs rotation ({orientation_info.angle}°{method_text})"

                        st.caption(f"{grade_color} Quality: {quality_info.quality_description} (Grade {quality_info.grade}){orientation_text} | " +
                                 f"Size: {uploaded_file.size / 1024:.1f} KB | Format: {image.format}")

                        # Show detailed metrics on hover/expander
                        with st.expander("📊 Quality Details", expanded=False):
                            st.write(f"**Overall Score:** {quality_info.overall_score}/100")
                            if quality_info.metrics:
                                st.write(f"**Sharpness:** {quality_info.metrics['sharpness']}")
                                st.write(f"**Contrast:** {quality_info.metrics['contrast']}")
                                st.write(f"**Brightness:** {quality_info.metrics['brightness']}")
                                st.write(f"**Noise Level:** {quality_info.metrics['noise_level']}")
                                st.write(f"**Text Regions:** {quality_info.metrics['text_regions']}")
                                if 'horizontal_lines' in quality_info.metrics:
                                    st.write(f"**Horizontal Lines:** {quality_info.metrics['horizontal_lines']}")

                            # Show orientation info
                            st.write("**Orientation:**")
                            st.write(f"Angle: {orientation_info.angle}°")
                            st.write(f"Needs Rotation: {'Yes' if orientation_info.needs_rotation else 'No'}")
                            if orientation_info.method:
                                st.write(f"Detection Method: {orientation_info.method}")

                    except Exception as quality_error:
                        st.caption(f"Size: {uploaded_file.size / 1024:.1f} KB | Format: {image.format}")
                        st.warning(f"Could not assess image quality: {str(quality_error)}")

                    valid_files.append(uploaded_file)

                except Exception as e:
                    st.error(f"Error loading {uploaded_file.name}: {str(e)}")

        # Upload button
        if valid_files:
            st.markdown("---")
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("📤 Upload Images", type="primary", help=f"Add {len(valid_files)} image(s) to collection"):
                    # Don't clear existing images, append to them instead
                    if not hasattr(st.session_state, 'uploaded_images'):
                        st.session_state.uploaded_images = []

                    new_images = []

                    with st.spinner(f"Uploading {len(valid_files)} image(s)..."):
                        for uploaded_file in valid_files:
                            try:
                                # Check if file already exists in collection (avoid true duplicates)
                                existing_names = [img['name'] for img in st.session_state.uploaded_images]
                                if uploaded_file.name in existing_names:
                                    st.warning(f"⚠️ {uploaded_file.name} already exists in collection, skipping...")
                                    continue

                                # Save to temporary directory using storage service
                                image_info_obj = storage_service.save_temp_image(uploaded_file, uploaded_file.name)

                                # Convert to dictionary for session state compatibility
                                image_info = {
                                    'name': image_info_obj.name,
                                    'original_name': image_info_obj.original_name,
                                    'path': image_info_obj.path
                                }
                                new_images.append(image_info)
                            except Exception as save_error:
                                st.error(f"Error saving {uploaded_file.name}: {str(save_error)}")

                    # Add all new images to session state
                    if new_images:
                        st.session_state.uploaded_images.extend(new_images)
                        added_count = len(new_images)

                        st.success(f"✅ Successfully uploaded {added_count} image{'s' if added_count != 1 else ''} to collection!")

                        # Auto-select new images for processing
                        for img in new_images:
                            if img['name'] not in st.session_state.selected_images:
                                st.session_state.selected_images.append(img['name'])

                        # Clear the file uploader by rerunning (this will reset it)
                        st.rerun()

            with col2:
                st.info(f"💡 Ready to upload {len(valid_files)} new image{'s' if len(valid_files) != 1 else ''}")

    # Show all uploaded images with selection checkboxes
    if st.session_state.uploaded_images:
        st.markdown("---")
        st.subheader(f"🖼️ All Uploaded Images ({len(st.session_state.uploaded_images)})")

        # Select all / Select none buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("✅ Select All"):
                st.session_state.selected_images = [img['name'] for img in st.session_state.uploaded_images]
                st.rerun()
        with col2:
            if st.button("❌ Select None"):
                st.session_state.selected_images = []
                st.rerun()
        with col3:
            selected_count = len(st.session_state.selected_images)
            st.write(f"**Selected: {selected_count} image(s)**")

        # Clear all images button
        col4, _ = st.columns([1, 3])
        with col4:
            if st.button("🗑️ Clear All", help="Remove all uploaded images"):
                # Clear session state
                st.session_state.uploaded_images = []
                st.session_state.selected_images = []
                # Delete temp files using storage service
                storage_service.clear_temp_directory()
                st.success("All images cleared!")
                st.rerun()

        # Display images with checkboxes
        cols = st.columns(min(len(st.session_state.uploaded_images), 3))
        for idx, image_info in enumerate(st.session_state.uploaded_images):
            with cols[idx % 3]:
                try:
                    # Checkbox for selection
                    is_selected = image_info['name'] in st.session_state.selected_images
                    # Use original name for display if available, otherwise use the unique name
                    display_name = image_info.get('original_name', image_info['name'])
                    if st.checkbox(f"Process this image", value=is_selected, key=f"select_{image_info['name']}"):
                        if image_info['name'] not in st.session_state.selected_images:
                            st.session_state.selected_images.append(image_info['name'])
                    else:
                        if image_info['name'] in st.session_state.selected_images:
                            st.session_state.selected_images.remove(image_info['name'])

                    # Display image with status indicator
                    image = Image.open(image_info['path'])

                    # Check if this image has been processed
                    processed_names = [r.get('image_name', '') for r in st.session_state.results]
                    is_processed = image_info['name'] in processed_names

                    # Add status emoji to caption
                    status_emoji = "✅" if is_processed else "⏳"
                    status_text = "Processed" if is_processed else "Ready"
                    # Use original name for display if available, otherwise use the unique name
                    display_name = image_info.get('original_name', image_info['name'])
                    caption = f"{status_emoji} {display_name} ({status_text})"

                    st.image(image, caption=caption, use_container_width=True)

                    # File info with processing status and quality
                    file_size = os.path.getsize(image_info['path']) / 1024

                    # Display image quality assessment for uploaded images
                    try:
                        quality_info = ocr_service.assess_image_quality(image_info['path'])

                        # Check orientation
                        orientation_info = ocr_service.detect_orientation(image_info['path'])

                        # Display quality grade with color coding
                        grade_color = {
                            'A': '🟢',  # Excellent
                            'B': '🔵',  # Good
                            'C': '🟡',  # Fair
                            'D': '🟠',  # Poor
                            'F': '🔴',  # Very Poor
                        }.get(quality_info.grade, '⚪')

                        # Display orientation info
                        orientation_text = ""
                        if orientation_info.needs_rotation:
                            method_text = f" ({orientation_info.method or 'auto'})" if orientation_info.method else ""
                            orientation_text = f" | 🔁 Needs rotation ({orientation_info.angle}°{method_text})"

                        st.caption(f"{grade_color} Quality: {quality_info.quality_description} (Grade {quality_info.grade}){orientation_text} | " +
                                 f"Size: {file_size:.1f} KB")

                        # Show detailed metrics on hover/expander
                        with st.expander("📊 Quality Details", expanded=False):
                            st.write(f"**Overall Score:** {quality_info.overall_score}/100")
                            if quality_info.metrics:
                                st.write(f"**Sharpness:** {quality_info.metrics['sharpness']}")
                                st.write(f"**Contrast:** {quality_info.metrics['contrast']}")
                                st.write(f"**Brightness:** {quality_info.metrics['brightness']}")
                                st.write(f"**Noise Level:** {quality_info.metrics['noise_level']}")
                                st.write(f"**Text Regions:** {quality_info.metrics['text_regions']}")
                                if 'horizontal_lines' in quality_info.metrics:
                                    st.write(f"**Horizontal Lines:** {quality_info.metrics['horizontal_lines']}")
                                if 'resolution_score' in quality_info.metrics:
                                    st.write(f"**Resolution Score:** {quality_info.metrics['resolution_score']}")
                                if 'edges' in quality_info.metrics:
                                    st.write(f"**Edge Count:** {quality_info.metrics['edges']}")

                            # Show orientation info
                            st.write("**Orientation:**")
                            st.write(f"Angle: {orientation_info.angle}°")
                            st.write(f"Needs Rotation: {'Yes' if orientation_info.needs_rotation else 'No'}")
                            if orientation_info.method:
                                st.write(f"Detection Method: {orientation_info.method}")

                    except Exception as quality_error:
                        st.caption(f"Size: {file_size:.1f} KB")

                    if is_processed:
                        st.success("Already processed ✓")

                    # Action buttons
                    col_a, col_b = st.columns(2)

                    with col_a:
                        # Reprocess button for already processed images
                        if is_processed:
                            if st.button("🔄", help=f"Reprocess {display_name}", key=f"reprocess_{image_info['name']}"):
                                if image_info['name'] not in st.session_state.selected_images:
                                    st.session_state.selected_images.append(image_info['name'])
                                st.rerun()

                    with col_b:
                        # Remove image button
                        if st.button("🗑️", help=f"Remove {display_name}", key=f"remove_{image_info['name']}"):
                            # Remove from uploaded images
                            st.session_state.uploaded_images = [
                                img for img in st.session_state.uploaded_images
                                if img['name'] != image_info['name']
                            ]
                            # Remove from selected images
                            if image_info['name'] in st.session_state.selected_images:
                                st.session_state.selected_images.remove(image_info['name'])
                            # Delete the temp file using storage service
                            storage_service.delete_temp_image(image_info['name'])
                            st.rerun()

                except Exception as e:
                    # Use original name for display if available, otherwise use the unique name
                    display_name = image_info.get('original_name', image_info['name'])
                    st.error(f"Error displaying {display_name}: {str(e)}")

def debug_section():
    """Display debug information for OCR results."""
    if not st.session_state.debug_mode or not st.session_state.ocr_results:
        return

    st.header("🔍 Debug Mode - OCR Results")
    st.info("Review the OCR results below. Click 'Continue to AI Processing' for each image you want to process.")

    for image_name, ocr_data in st.session_state.ocr_results.items():
        display_name = ocr_data.get('original_name', image_name)
        with st.expander(f"📄 {display_name}", expanded=True):
            col1, col2 = st.columns([1, 2])

            with col1:
                # Show image
                try:
                    image = Image.open(ocr_data['image_path'])
                    st.image(image, caption=display_name, use_container_width=True)
                except:
                    st.error("Could not display image")

            with col2:
                # Show OCR result
                st.subheader("OCR Extracted Text")
                extracted_text = ocr_data.get('extracted_text', '')
                if extracted_text:
                    st.text_area("", extracted_text, height=200, key=f"ocr_text_{image_name}", disabled=False)
                else:
                    st.warning("No text was extracted from this image.")

                # Show quality info if available
                if 'quality_info' in ocr_data:
                    quality_info = ocr_data['quality_info']
                    st.subheader("Image Quality")
                    st.write(f"Grade: {quality_info.grade} ({quality_info.quality_description})")
                    st.write(f"Overall Score: {quality_info.overall_score}/100")

                # Continue button
                confirmed = image_name in st.session_state.debug_confirmed
                if confirmed:
                    st.success("✅ Ready for AI processing")
                else:
                    if st.button("Continue to AI Processing", key=f"continue_ai_{image_name}"):
                        st.session_state.debug_confirmed.add(image_name)
                        st.rerun()

def process_images():
    """Process selected images with OCR and AI."""
    if not st.session_state.uploaded_images:
        st.warning("Please upload some images first.")
        return

    if not st.session_state.selected_images:
        st.warning("Please select at least one image to process.")
        return

    # Debug mode toggle
    st.session_state.debug_mode = st.checkbox("🔍 Enable Debug Mode (Review OCR results before AI processing)",
                                             value=st.session_state.debug_mode)

    # Show processing button with count
    selected_count = len(st.session_state.selected_images)
    button_text = f"🚀 Process {selected_count} Selected Image{'s' if selected_count > 1 else ''}"

    # Show additional info
    st.info(f"📊 Ready to process: {', '.join(st.session_state.selected_images)}")

    if st.button(button_text, type="primary", disabled=st.session_state.processing):
        st.session_state.processing = True

        # If in debug mode, extract OCR text and show in debug section
        if st.session_state.debug_mode:
            st.session_state.ocr_results = {}
            st.session_state.debug_confirmed = set()

            # Extract OCR text for all selected images using OCR service
            with st.spinner("Extracting text from images..."):
                selected_images = [img for img in st.session_state.uploaded_images
                                  if img['name'] in st.session_state.selected_images]

                for image_info in selected_images:
                    try:
                        # Extract text using OCR service
                        extracted_text = ocr_service.extract_text(image_info['path'])

                        # Assess image quality
                        quality_info = ocr_service.assess_image_quality(image_info['path'])

                        # Store OCR result for debug review
                        st.session_state.ocr_results[image_info['name']] = {
                            'image_path': image_info['path'],
                            'original_name': image_info.get('original_name', image_info['name']),
                            'extracted_text': extracted_text,
                            'quality_info': quality_info
                        }
                    except Exception as e:
                        st.error(f"Error extracting text from {image_info.get('original_name', image_info['name'])}: {str(e)}")

            st.session_state.processing = False
            st.info("OCR extraction complete. Review the results in the Debug section below.")
            st.rerun()
        else:
            # Normal processing flow (without debug)
            # Don't clear all results, only clear results for images being reprocessed
            existing_result_names = [r.get('image_name', '') for r in st.session_state.results]
            st.session_state.results = [r for r in st.session_state.results
                                       if r.get('image_name', '') not in st.session_state.selected_images]

            # Test AI connection
            st.info("Testing AI connection...")
            if not ai_service.test_connection():
                st.error("Failed to connect to AI service. Please check your configuration.")
                st.session_state.processing = False
                return

            # Process each selected image using the processing service
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Filter to only selected images
            selected_images = [img for img in st.session_state.uploaded_images
                              if img['name'] in st.session_state.selected_images]
            total_images = len(selected_images)

            for idx, image_info in enumerate(selected_images):
                # Use original name for display if available, otherwise use the unique name
                display_name = image_info.get('original_name', image_info['name'])
                progress = (idx + 1) / total_images
                progress_bar.progress(progress)
                status_text.text(f"Processing {display_name} ({idx + 1}/{total_images})")

                try:
                    # Create ImageInfo object
                    image_obj = ImageInfo(
                        name=image_info['name'],
                        original_name=display_name,
                        path=image_info['path']
                    )

                    # Process image using the processing service
                    result_obj = processing_service.process_single_image(image_obj)

                    # Convert result to dictionary for display
                    result = {
                        'image_name': image_obj.name,
                        'original_name': display_name,
                        'image_path': image_obj.path,
                        'extracted_text': result_obj.ocr_result.text if result_obj.ocr_result else '',
                        'classification': {
                            'subject': result_obj.classification_result.subject if result_obj.classification_result else 'general',
                            'content_type': result_obj.classification_result.content_type if result_obj.classification_result else 'notes',
                            'confidence': result_obj.classification_result.confidence if result_obj.classification_result else 0,
                            'key_concepts': result_obj.classification_result.key_concepts if result_obj.classification_result else [],
                            'notes': result_obj.classification_result.notes if result_obj.classification_result else '',
                            'summary': result_obj.classification_result.summary if result_obj.classification_result else '',
                        },
                        'merged': False  # TODO: Implement merge detection
                    }
                    st.session_state.results.append(result)

                except Exception as e:
                    st.error(f"❌ Error processing {display_name}: {str(e)}")
                    # Continue processing other images even if one fails
                    continue

            progress_bar.progress(1.0)
            success_count = len(st.session_state.results)
            status_text.text(f"✅ Processing complete! Successfully processed {success_count}/{total_images} images.")

            # Clear selected images after successful processing
            st.session_state.selected_images = []
            st.session_state.processing = False

            # Show success message
            if success_count == total_images:
                st.success(f"🎉 All {total_images} images processed successfully!")
            else:
                st.warning(f"⚠️ Processed {success_count} out of {total_images} images. Some images may have failed.")

            time.sleep(2)
            st.rerun()

def process_debug_confirmed():
    """Process images that have been confirmed in debug mode."""
    if not st.session_state.debug_mode or not st.session_state.debug_confirmed:
        return

    if st.button("🚀 Process Confirmed Images with AI", type="primary"):
        st.session_state.processing = True

        # Test AI connection
        st.info("Testing AI connection...")
        if not ai_service.test_connection():
            st.error("Failed to connect to AI service. Please check your configuration.")
            st.session_state.processing = False
            return

        # Process confirmed images
        confirmed_images = [name for name in st.session_state.debug_confirmed
                           if name in st.session_state.ocr_results]

        progress_bar = st.progress(0)
        status_text = st.empty()
        total_images = len(confirmed_images)

        for idx, image_name in enumerate(confirmed_images):
            ocr_data = st.session_state.ocr_results[image_name]
            display_name = ocr_data.get('original_name', image_name)

            progress = (idx + 1) / total_images
            progress_bar.progress(progress)
            status_text.text(f"Processing {display_name} with AI ({idx + 1}/{total_images})")

            try:
                extracted_text = ocr_data.get('extracted_text', '')

                if not extracted_text.strip():
                    st.warning(f"No text found in {display_name}")
                    continue

                # Generate notes using AI service
                classification_result = ai_service.process_text(
                    extracted_text,
                    display_name
                )

                # Create ImageInfo object for saving
                image_obj = ImageInfo(
                    name=image_name,
                    original_name=display_name,
                    path=ocr_data['image_path']
                )

                # TODO: Implement proper notes saving with the new architecture
                # For now, we'll create a simple result structure
                result = {
                    'image_name': image_name,
                    'original_name': display_name,
                    'image_path': ocr_data['image_path'],
                    'extracted_text': extracted_text,
                    'classification': {
                        'subject': classification_result.subject,
                        'content_type': classification_result.content_type,
                        'confidence': classification_result.confidence,
                        'key_concepts': classification_result.key_concepts,
                        'notes': classification_result.notes,
                        'summary': classification_result.summary,
                    },
                    'merged': False
                }
                st.session_state.results.append(result)

            except Exception as e:
                st.error(f"❌ Error processing {display_name}: {str(e)}")
                continue

        progress_bar.progress(1.0)
        success_count = len([r for r in st.session_state.results
                            if r.get('image_name') in confirmed_images])
        status_text.text(f"✅ AI processing complete! Successfully processed {success_count}/{total_images} images.")

        # Clear debug state
        st.session_state.debug_confirmed = set()
        st.session_state.ocr_results = {}
        st.session_state.processing = False

        st.success(f"🎉 Processed {success_count} confirmed images with AI!")
        time.sleep(2)
        st.rerun()

def results_section():
    """Display processing results."""
    if not st.session_state.results:
        return

    st.header("📊 Results")
    st.success(f"Successfully processed {len(st.session_state.results)} image(s)")

    # Summary by subject
    subjects = {}
    for result in st.session_state.results:
        subject = result['classification'].get('subject', 'Unknown').lower()
        if subject not in subjects:
            subjects[subject] = 0
        subjects[subject] += 1

    if subjects:
        st.subheader("📚 Summary by Subject")
        for subject, count in subjects.items():
            st.write(f"• **{subject.title()}**: {count} note(s)")

    # Detailed results
    st.subheader("📝 Detailed Results")

    for idx, result in enumerate(st.session_state.results):
        # Use original name for display if available in the result
        display_name = result.get('original_name', result['image_name'])
        with st.expander(f"📄 {display_name}", expanded=idx == 0):
            col1, col2 = st.columns([1, 2])

            with col1:
                # Show image
                try:
                    image = Image.open(result['image_path'])
                    st.image(image, caption=display_name, use_container_width=True)
                except:
                    st.error("Could not display image")

            with col2:
                # Show classification
                classification = result['classification']
                st.write("**Subject:**", classification.get('subject', 'N/A').title())
                st.write("**Content Type:**", classification.get('content_type', 'N/A').title())
                st.write("**Confidence:**", f"{classification.get('confidence', 0):.1f}%")

                # Show merged note indicator
                if result.get('merged', False):
                    st.info("ℹ️ This note was merged with an existing note containing similar content")

                # Show generated notes
                notes = classification.get('notes', '')
                if notes:
                    st.write("**Generated Notes:**")
                    st.text_area("", notes, height=200, key=f"notes_{idx}", disabled=True)

def main():
    """Main application function."""
    st.title("📚 SAT/ACT Notes Organizer")
    st.markdown("Upload images of your study materials to automatically extract text and generate organized notes!")

    # Initialize session state
    initialize_session_state()

    # Sidebar
    with st.sidebar:
        st.header("🛠️ Controls")

        if st.button("🔄 Clear All Data"):
            st.session_state.uploaded_images = []
            st.session_state.results = []
            # Clear temp directory using storage service
            storage_service.clear_temp_directory()
            st.success("All data cleared!")
            time.sleep(1)
            st.rerun()

        st.markdown("---")
        st.markdown("### 📋 Status")

        # Current session status
        if st.session_state.uploaded_images:
            st.write(f"📤 Session: {len(st.session_state.uploaded_images)} images uploaded")
        if st.session_state.results:
            st.write(f"✅ Session: {len(st.session_state.results)} images processed")

        # File system status
        temp_dir = get_resource_path('data/temp')
        notes_dir = get_resource_path('data/notes')

        if os.path.exists(temp_dir):
            temp_count = len([f for f in os.listdir(temp_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))])
            if temp_count > 0:
                st.write(f"🖼️ Temp: {temp_count} image(s)")

        if os.path.exists(notes_dir):
            notes_count = len([f for f in os.listdir(notes_dir) if f.endswith('.md')])
            if notes_count > 0:
                st.write(f"📝 Notes: {notes_count} file(s)")

        st.markdown("---")
        st.markdown("### 📁 Quick Access")
        if st.button("📂 Browse Files", use_container_width=True):
            st.session_state.show_file_browser = not st.session_state.show_file_browser
            st.rerun()

        st.markdown("### ⚡ Quick Actions")
        col1, col2 = st.columns(2)

        with col1:
            # Quick download all notes
            notes_dir = get_resource_path('data/notes')
            if os.path.exists(notes_dir) and os.listdir(notes_dir):
                if st.button("💾", help="Download all notes", key="quick_download"):
                    import zipfile
                    import io
                    try:
                        note_files = [f for f in os.listdir(notes_dir) if f.endswith('.md')]
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for filename in note_files:
                                file_path = os.path.join(notes_dir, filename)
                                zip_file.write(file_path, filename)
                        zip_buffer.seek(0)
                        st.download_button(
                            label="📥 notes.zip",
                            data=zip_buffer.read(),
                            file_name="sat_act_notes.zip",
                            mime="application/zip",
                            key="sidebar_zip_download"
                        )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        with col2:
            # Quick clear temp files
            if st.button("🧹", help="Clear temp files", key="quick_clear"):
                try:
                    # Clear temp directory using storage service
                    storage_service.clear_temp_directory()
                    st.success("Temp cleared!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Main content
    upload_section()

    if st.session_state.uploaded_images:
        st.markdown("---")
        process_images()

        # Debug section
        if st.session_state.debug_mode:
            debug_section()
            process_debug_confirmed()

    if st.session_state.results:
        st.markdown("---")
        results_section()

    # File browser section
    if st.session_state.get('show_file_browser', False):
        st.markdown("---")
        file_browser_section()

def file_browser_section():
    """File browser to view uploaded images and generated notes."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("📁 File Browser")
    with col2:
        if st.button("✖️ Close", key="close_browser"):
            st.session_state.show_file_browser = False
            st.rerun()

    # Show folder statistics
    temp_dir = get_resource_path('data/temp')
    notes_dir = get_resource_path('data/notes')



    col1, col2, col3 = st.columns(3)
    with col1:
        temp_size = get_folder_size(temp_dir) / 1024  # Convert bytes to KB
        st.metric("📂 Temp Folder", f"{temp_size:.1f} KB")
    with col2:
        notes_size = get_folder_size(notes_dir) / 1024  # Convert bytes to KB
        st.metric("📝 Notes Folder", f"{notes_size:.1f} KB")
    with col3:
        total_size = temp_size + notes_size
        st.metric("💾 Total Storage", f"{total_size:.1f} KB")

    # Create tabs for different folders
    tab1, tab2 = st.tabs(["🖼️ Uploaded Images", "📝 Generated Notes"])

    with tab1:
        st.subheader("Temporary Uploaded Images")

        if os.path.exists(temp_dir):
            temp_files = [f for f in os.listdir(temp_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]

            if temp_files:
                st.write(f"Found {len(temp_files)} image(s) in temp folder:")

                # Display images in a grid
                cols = st.columns(3)
                for idx, filename in enumerate(temp_files):
                    with cols[idx % 3]:
                        try:
                            image_path = os.path.join(temp_dir, filename)
                            image = Image.open(image_path)
                            st.image(image, caption=filename, use_container_width=True)

                            # File info
                            file_size = os.path.getsize(image_path) / 1024
                            st.caption(f"Size: {file_size:.1f} KB")

                            # Show file path on toggle
                            if st.checkbox("Show path", key=f"img_path_{filename}_{idx}"):
                                st.code(image_path, language=None)

                            # Download button for individual image
                            with open(image_path, 'rb') as f:
                                st.download_button(
                                    label=f"Download {filename}",
                                    data=f.read(),
                                    file_name=filename,
                                    mime="image/jpeg" if filename.lower().endswith(('.jpg', '.jpeg')) else "image/png"
                                )
                        except Exception as e:
                            st.error(f"Error loading {filename}: {str(e)}")

                # Option to clear temp folder
                if st.button("🗑️ Clear Temporary Images", type="secondary"):
                    try:
                        # Clear temp directory using storage service
                        storage_service.clear_temp_directory()
                        st.success("Temporary images cleared!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing temp files: {str(e)}")
            else:
                st.info("No images in temp folder. Upload some images first!")
        else:
            st.info("Temp folder doesn't exist yet. Upload some images first!")

    with tab2:
        st.subheader("Generated Notes")

        # Search functionality
        search_term = st.text_input("🔍 Search notes", placeholder="Search by filename or content...")

        if os.path.exists(notes_dir):
            all_note_files = [f for f in os.listdir(notes_dir) if f.endswith('.md')]

            # Filter notes based on search term
            if search_term:
                note_files = []
                for filename in all_note_files:
                    # Search in filename
                    if search_term.lower() in filename.lower():
                        note_files.append(filename)
                        continue

                    # Search in file content
                    try:
                        file_path = os.path.join(notes_dir, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                            if search_term.lower() in content:
                                note_files.append(filename)
                    except:
                        pass  # Skip files that can't be read

                if search_term and not note_files:
                    st.warning(f"No notes found containing '{search_term}'")
                elif search_term:
                    st.info(f"Found {len(note_files)} note(s) matching '{search_term}'")
            else:
                note_files = all_note_files

            if note_files:
                st.write(f"Found {len(note_files)} note file(s):")

                # Sort by modification time (newest first)
                note_files.sort(key=lambda x: os.path.getmtime(os.path.join(notes_dir, x)), reverse=True)

                for filename in note_files:
                    with st.expander(f"📄 {filename}", expanded=False):
                        try:
                            file_path = os.path.join(notes_dir, filename)

                            # File info
                            file_size = os.path.getsize(file_path) / 1024
                            mod_time = os.path.getmtime(file_path)
                            mod_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mod_time))

                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.caption(f"Modified: {mod_time_str} | Size: {file_size:.1f} KB")
                                # Show file path on toggle
                                if st.checkbox("Show path", key=f"path_{filename}"):
                                    st.code(file_path, language=None)
                            with col2:
                                # Download button
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    st.download_button(
                                        label="📥 Download",
                                        data=f.read(),
                                        file_name=filename,
                                        mime="text/markdown",
                                        key=f"download_{filename}"
                                    )

                            # Preview the note content
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()

                            # Show first 500 characters as preview
                            if len(content) > 500:
                                preview = content[:500] + "..."
                                st.markdown("**Preview:**")
                                st.text(preview)

                                # Option to show full content
                                if st.button(f"Show Full Content", key=f"full_{filename}"):
                                    st.markdown("**Full Content:**")
                                    st.markdown(content)
                            else:
                                st.markdown("**Content:**")
                                st.markdown(content)

                        except Exception as e:
                            st.error(f"Error reading {filename}: {str(e)}")

                # Option to clear all notes
                if st.button("🗑️ Clear All Notes", type="secondary"):
                    try:
                        for filename in note_files:
                            os.remove(os.path.join(notes_dir, filename))
                        st.success("All notes cleared!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing notes: {str(e)}")

                # Bulk operations
                col1, col2 = st.columns(2)
                with col1:
                    # Option to download all notes as ZIP
                    if st.button("📦 Download All Notes as ZIP"):
                        try:
                            import zipfile
                            import io

                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                for filename in note_files:
                                    file_path = os.path.join(notes_dir, filename)
                                    zip_file.write(file_path, filename)

                            zip_buffer.seek(0)
                            st.download_button(
                                label="📥 Download ZIP File",
                                data=zip_buffer.read(),
                                file_name="sat_act_notes.zip",
                                mime="application/zip"
                            )
                        except Exception as e:
                            st.error(f"Error creating ZIP file: {str(e)}")

                with col2:
                    # Show folder location
                    if st.button("📍 Open Folder Location"):
                        st.info(f"Notes folder location:")
                        st.code(notes_dir, language=None)

            else:
                st.info("No notes generated yet. Process some images first!")
        else:
            st.info("Notes folder doesn't exist yet. Process some images first!")

if __name__ == "__main__":
    main()
