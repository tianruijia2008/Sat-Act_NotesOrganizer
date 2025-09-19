import cv2
import numpy as np
from PIL import Image
import io
import streamlit as st

def enhance_image_for_text(image):
    """
    Enhance captured image for better text readability using OpenCV.
    This addresses blurry text issues by applying sharpening and contrast enhancement.
    """
    try:
        # Convert PIL image to OpenCV format
        if isinstance(image, Image.Image):
            # Convert to numpy array
            img_array = np.array(image)
            # Convert RGB to BGR for OpenCV
            if len(img_array.shape) == 3:
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            else:
                img_cv = img_array
        else:
            img_cv = image

        # Convert to grayscale for processing
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # Apply adaptive histogram equalization for better contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)

        # Apply unsharp mask for better text sharpness
        gaussian = cv2.GaussianBlur(enhanced, (0, 0), 2.0)
        unsharp_mask = cv2.addWeighted(enhanced, 1.5, gaussian, -0.5, 0)

        # Apply morphological operations to clean up text
        kernel = np.ones((1,1), np.uint8)
        cleaned = cv2.morphologyEx(unsharp_mask, cv2.MORPH_CLOSE, kernel)

        # Convert back to RGB and PIL Image
        if len(img_array.shape) == 3:
            enhanced_bgr = cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)
            enhanced_rgb = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2RGB)
        else:
            enhanced_rgb = cleaned

        enhanced_pil = Image.fromarray(enhanced_rgb)

        return enhanced_pil

    except Exception as e:
        st.warning(f"Image enhancement failed: {e}. Using original image.")
        return image

def detect_text_focus_quality(image):
    """
    Detect if the image has good focus for text using edge detection.
    Returns a focus score (higher is better focused).
    """
    try:
        # Convert to OpenCV format
        if isinstance(image, Image.Image):
            img_array = np.array(image)
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Calculate Laplacian variance (focus measure)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # Normalize score (typical range for text images is 50-2000+)
        if laplacian_var < 100:
            quality = "Poor (Very Blurry)"
            score = 1
        elif laplacian_var < 300:
            quality = "Fair (Slightly Blurry)"
            score = 2
        elif laplacian_var < 500:
            quality = "Good"
            score = 3
        else:
            quality = "Excellent (Sharp)"
            score = 4

        return {
            'score': score,
            'quality': quality,
            'variance': laplacian_var
        }

    except Exception as e:
        return {
            'score': 2,
            'quality': "Unknown",
            'variance': 0,
            'error': str(e)
        }

def get_camera_tips():
    """
    Return practical tips for better mobile camera focus on text.
    """
    return {
        'distance': "Hold your phone 6-12 inches from the document",
        'lighting': "Use bright, even lighting. Avoid shadows and glare",
        'stability': "Keep your phone steady. Use both hands or lean against something",
        'focus': "Tap on the document in your camera app before taking the photo",
        'angle': "Keep your phone parallel to the document (not tilted)",
        'background': "Use a dark background behind light paper for better contrast",
        'multiple': "Take 2-3 photos and choose the sharpest one"
    }

def show_camera_help():
    """
    Display helpful camera tips in Streamlit.
    """
    with st.expander("📱 Tips for Sharp Text Photos"):
        tips = get_camera_tips()

        st.markdown("### 🎯 For Best Focus:")
        st.markdown(f"• **Distance:** {tips['distance']}")
        st.markdown(f"• **Tap to Focus:** {tips['focus']}")
        st.markdown(f"• **Stability:** {tips['stability']}")

        st.markdown("### 💡 For Best Lighting:")
        st.markdown(f"• **Lighting:** {tips['lighting']}")
        st.markdown(f"• **Background:** {tips['background']}")

        st.markdown("### 📐 For Best Angle:")
        st.markdown(f"• **Position:** {tips['angle']}")
        st.markdown(f"• **Multiple shots:** {tips['multiple']}")

def process_camera_image(image_file):
    """
    Process camera image with focus detection and enhancement.
    """
    try:
        # Load image
        if hasattr(image_file, 'read'):
            image_bytes = image_file.read()
            image = Image.open(io.BytesIO(image_bytes))
        else:
            image = image_file

        # Analyze focus quality
        focus_info = detect_text_focus_quality(image)

        # Show focus quality feedback
        if focus_info['score'] >= 3:
            st.success(f"✅ Image Quality: {focus_info['quality']}")
        elif focus_info['score'] == 2:
            st.warning(f"⚠️ Image Quality: {focus_info['quality']} - Consider retaking")
        else:
            st.error(f"❌ Image Quality: {focus_info['quality']} - Please retake with better focus")

        # Show variance score for debugging
        st.caption(f"Focus score: {focus_info['variance']:.1f}")

        # Enhance image for better text processing
        enhanced_image = enhance_image_for_text(image)

        return enhanced_image, focus_info

    except Exception as e:
        st.error(f"Error processing camera image: {e}")
        return image_file, {'score': 0, 'quality': 'Error', 'variance': 0}

def compare_before_after(original_image, enhanced_image):
    """
    Show before/after comparison of image enhancement.
    """
    st.subheader("Image Enhancement Results")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Original**")
        st.image(original_image, use_column_width=True)

    with col2:
        st.markdown("**Enhanced for OCR**")
        st.image(enhanced_image, use_column_width=True)

def auto_orient_image(image):
    """
    Auto-orient image based on text detection (rotate if text is sideways).
    """
    try:
        # Convert to OpenCV
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Detect text orientation using morphological operations
        # This is a simple heuristic - for production, you might want to use
        # more sophisticated text orientation detection

        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Find lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)

        if lines is not None:
            angles = []
            for rho, theta in lines[:10]:  # Use first 10 lines
                angle = np.degrees(theta) - 90
                angles.append(angle)

            # Calculate median angle
            if angles:
                median_angle = np.median(angles)

                # If significantly rotated, suggest rotation
                if abs(median_angle) > 15:
                    st.info(f"📐 Text appears rotated by ~{median_angle:.1f}°. Consider rotating your phone or document.")

                    # Auto-rotate if angle is close to 90° increments
                    if 80 <= abs(median_angle) <= 100:
                        rotated = image.rotate(90 if median_angle > 0 else -90, expand=True)
                        st.info("🔄 Auto-rotated image for better text alignment")
                        return rotated

        return image

    except Exception as e:
        st.warning(f"Auto-orientation failed: {e}")
        return image

def get_mobile_camera_settings():
    """
    Return JavaScript code for better mobile camera settings.
    This can be injected into Streamlit apps for better camera behavior.
    """
    return """
    <script>
    // Mobile camera optimization
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // Override default constraints for better document scanning
        const originalGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);

        navigator.mediaDevices.getUserMedia = function(constraints) {
            if (constraints && constraints.video) {
                // Add document scanning optimizations
                const videoConstraints = {
                    ...constraints.video,
                    focusMode: { ideal: "continuous" },
                    exposureMode: { ideal: "continuous" },
                    whiteBalanceMode: { ideal: "continuous" },
                    // Higher resolution for text clarity
                    width: { ideal: 1920, min: 1280 },
                    height: { ideal: 1080, min: 720 },
                    // Prefer back camera for documents
                    facingMode: { ideal: "environment" }
                };

                constraints.video = videoConstraints;
            }
            return originalGetUserMedia(constraints);
        };
    }
    </script>
    """
