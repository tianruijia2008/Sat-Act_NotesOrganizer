# SAT/ACT Notes Organizer - Quick Start

A simple app that converts images of study materials into organized markdown notes using OCR and AI.

## Prerequisites

- Python 3.8+
- Tesseract OCR
- AI API key (ModelScope or similar)

## 1. Check Setup

First, verify everything is configured correctly:

```bash
python3 setup_check.py
```

This will check dependencies, Tesseract installation, and configuration.

## 2. Install Dependencies

If setup check fails, install missing packages:

```bash
pip3 install streamlit pytesseract Pillow opencv-python numpy requests
```

### Install Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

## 3. Configure API Key

### Option A: Environment Variables (Recommended)
```bash
export AI_API_KEY="your_api_key_here"
export AI_BASE_URL="https://api-inference.modelscope.cn/v1/chat/completions"
export AI_MODEL="Qwen/Qwen3-235B-A22B-Thinking-2507"
```

### Option B: Edit config.json
Edit the `config.json` file and replace `"your_openai_api_key_here"` with your actual API key.

## 4. Run the App

### Desktop Usage
```bash
python3 app_launcher.py
```

The app will open in your browser at `http://localhost:8501`

### Mobile Usage
For mobile access (iPhone/Android):

```bash
# Terminal 1: Start mobile proxy
python3 mobile_proxy.py

# Terminal 2: Start ngrok
ngrok http 8502
```

Use the ngrok HTTPS URL on your mobile device.

## 5. How to Use

1. **Upload Images**: Drag and drop images of study materials
2. **Process**: Click "Process Selected Images" 
3. **Review**: Check OCR quality and AI-generated notes
4. **Download**: Save organized notes as markdown files

## Troubleshooting

### Common Issues

**"ModuleNotFoundError"**
- Run `pip3 install -r text/requirements.txt`

**"Tesseract not found"**
- Install Tesseract OCR (see step 2)
- On macOS, may need to set path: `export PATH="/usr/local/bin:$PATH"`

**"AI API Error"**
- Check your API key is set correctly
- Verify API URL is accessible
- Run `python3 setup_check.py` to diagnose

**Mobile ERR_NGROK-3200**
- Wait 10-15 seconds after starting all services
- Make sure you're using the HTTPS ngrok URL
- Try refreshing the page

### Test Mobile Setup
```bash
python3 test_mobile_setup.py
```

This will verify the complete chain: Streamlit → Proxy → Ngrok

## File Structure

```
Sat:Act_NotesOrganizer/
├── ui/app.py              # Main Streamlit app
├── services/              # Core processing services
├── src/                   # OCR and AI processors  
├── data/notes/            # Generated notes
├── data/temp/             # Temporary uploaded images
└── config.json            # Configuration file
```

## Tips

- **Better OCR**: Use clear, well-lit images with good contrast
- **AI Quality**: More detailed text input = better AI analysis
- **Mobile Access**: Always use HTTPS ngrok URL for mobile devices
- **Batch Processing**: Select multiple images to process together

Need help? Run `python3 setup_check.py` to diagnose issues.