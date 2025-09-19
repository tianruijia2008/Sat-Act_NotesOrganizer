# SAT/ACT Notes Organizer - Complete User Guide

A tool to automatically organize SAT/ACT study materials by extracting text from images, classifying content, and generating structured markdown files with AI-powered analysis.

## 🎯 What This Program Does

- **📸 Extract text** from images of study materials using OCR
- **🤖 AI Classification** - Automatically identifies notes vs. wrong questions
- **📝 Generate organized** markdown files for easy review
- **🌐 Web Interface** - User-friendly UI for uploading images and viewing results
- **📱 Mobile Camera Support** - Take photos directly with your phone (via HTTPS)
- **🔍 Vector Database** - Store and retrieve content using semantic search

---

## 🛠 Initial Setup

### Prerequisites
- **macOS** (this guide is for Mac)
- **Python 3.8+** 
- **Internet connection** (for AI processing and mobile camera)

### 1. Install Dependencies

```bash
# Navigate to project directory
cd /path/to/Sat:Act_NotesOrganizer

# Install Python packages
pip install -r requirements.txt

# Install Tesseract OCR (for text extraction from images)
brew install tesseract

# Install ngrok (for mobile camera access)
brew install ngrok/ngrok/ngrok
```

### 2. Setup ngrok for Mobile Camera (One-time)

```bash
# 1. Sign up for free ngrok account: https://dashboard.ngrok.com/signup
# 2. Get your auth token from the dashboard
# 3. Configure ngrok with your token:
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

### 3. Configure API Keys

Edit `config.json` and add your OpenAI API key:

```json
{
  "openai_api_key": "your_openai_api_key_here",
  ...
}
```

---

## 🚀 How to Use

### Option 1: Desktop Only (Mac Camera)

**Step 1: Start the Application**
```bash
# Method A: Using Zed (if available)
# Open project in Zed → Command Palette (Cmd+Shift+P) → "task spawn" → "🚀 Launch Web UI (Local)"

# Method B: Command Line
cd /path/to/Sat:Act_NotesOrganizer
python3 -m streamlit run ui/app.py --server.port 8501
```

**Step 2: Access the Web Interface**
- Open browser and go to: `http://localhost:8501`
- Camera will work on Mac for taking photos

**Step 3: Use the Application**
- **Upload Images**: Drag/drop or select image files
- **Camera Capture**: Take photos directly with Mac webcam
- **Process Images**: Click "Process Images" to analyze with AI
- **View Results**: See organized notes and classifications

### Option 2: Mobile Camera Access (iPhone/iPad)

**Step 1: Start the Application (Background)**
```bash
cd /path/to/Sat:Act_NotesOrganizer
python3 -m streamlit run ui/app.py --server.port 8501 &
```

**Step 2: Create HTTPS Tunnel**
```bash
# In same terminal or new terminal tab:
ngrok http 8501
```

**Step 3: Get the HTTPS URL**
Look for output like:
```
Forwarding    https://abc123def.ngrok.io -> http://localhost:8501
```

**Step 4: Access on Mobile**
- **Connect phone to same WiFi** as your Mac
- **Open browser on phone** (Safari/Chrome)
- **Go to the ngrok HTTPS URL**: `https://abc123def.ngrok.io`
- **Camera will work** because it's secure HTTPS!

---

## 📱 Using Zed Tasks (Recommended)

If using Zed editor, you can use clickable tasks:

1. **Open Command Palette**: `Cmd+Shift+P`
2. **Type**: "task spawn"
3. **Select a task**:
   - **🚀 Launch Web UI (Local)** - Start app for Mac use
   - **🌐 Create HTTPS Tunnel (Mobile Camera)** - Create ngrok tunnel
   - **📝 Process All Images** - Batch process images in data/raw/
   - **👀 Watch & Process Images** - Auto-process new images
   - **🧹 Clear Processed Data** - Reset processed data
   - **📦 Install Dependencies** - Install Python packages
   - **🔧 Install Tesseract OCR** - Install OCR software

---

## 📂 Project Structure

```
Sat:Act_NotesOrganizer/
├── ui/app.py                 # Main web interface
├── src/                      # Core processing modules
│   ├── ocr_processor.py     # Text extraction from images
│   ├── ai_processor.py      # AI classification
│   ├── notes_saver.py       # Save organized notes
│   └── vector_db.py         # Vector database for search
├── data/                     # Data storage
│   ├── raw/                 # Place images here for batch processing
│   ├── notes/               # Generated markdown notes
│   └── vector_db/           # Search database
├── script/                   # Automation scripts
│   └── run_all.py           # Batch processing script
├── config.json              # Configuration (API keys, settings)
├── requirements.txt         # Python dependencies
└── USER_GUIDE.md           # This guide
```

---

## 🎮 Web Interface Guide

### Main Tabs

1. **Upload Images**
   - Drag & drop image files or click to select
   - Supports: JPG, PNG, JPEG, BMP, TIFF
   - Can upload multiple images at once
   - Toggle "Preprocess Images" for better OCR accuracy

2. **Processing Status**  
   - Shows real-time processing progress
   - Displays current step (OCR → AI Analysis → Saving)
   - Progress bar and status updates

3. **View Results**
   - See all processed images and their classifications
   - View extracted text and AI analysis
   - Download generated markdown files
   - Toggle "Show Debug Info" for detailed information

4. **Camera Capture** 📸
   - Take photos directly in the app
   - **Enhanced with autofocus detection** - app tells you if photo is sharp enough
   - **Automatic image enhancement** - optimizes contrast and sharpness for text
   - Works on Mac (localhost) and mobile (via HTTPS tunnel)
   - Save to raw folder or process immediately

   **📱 For Sharp Text Photos:**
   - **Tap to focus** on the document before capturing
   - Hold phone **6-12 inches** from document
   - Use **bright, even lighting** (avoid shadows)
   - Keep phone **steady** and **parallel** to document
   - App shows focus quality: ✅ Excellent | ⚠️ Fair | ❌ Poor (retake)

### Sidebar Options
- **Clear Processed Data** - Removes all notes and database (keeps raw images)
- **Processing Options** - Configure preprocessing and analysis settings

---

## 🔧 Command Line Usage

### Batch Processing
```bash
# Process all images in data/raw/ directory
python3 script/run_all.py

# Watch for new images and auto-process
python3 script/run_all.py --watch
```

### Manual Processing
```bash
# Start web interface
python3 -m streamlit run ui/app.py --server.port 8501

# Create HTTPS tunnel for mobile
ngrok http 8501
```

### Data Management
```bash
# Clear processed data (keeps raw images)
./clear_data.sh

# Or manually:
rm -rf data/notes/* data/vector_db/*
```

---

## ⚠️ Troubleshooting

### Common Issues

**1. "about:blank" in browser**
- Make sure Streamlit is running: `ps aux | grep streamlit`
- Try restarting: Stop with Ctrl+C, then restart
- Check for port conflicts: `lsof -i :8501`

**2. Camera doesn't work on mobile**
- Ensure you're using HTTPS tunnel (ngrok URL)
- Check that ngrok is running and showing "online" status
- Try refreshing the page or restarting ngrok

**3. OCR not working**
- Install Tesseract: `brew install tesseract`
- Check installation: `tesseract --version`
- Verify images are clear and readable

**4. AI classification fails**
- Check API key in `config.json`
- Verify internet connection
- Check API quota/billing

**5. Import errors**
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python3 --version` (need 3.8+)

### Getting Help
- Check terminal output for error messages
- Verify all dependencies are installed
- Ensure config.json has valid API keys
- Try processing with smaller/clearer images first

---

## 🔐 Security & Privacy

- **Local Processing**: OCR and file handling happen on your Mac
- **AI Processing**: Text is sent to OpenAI/ModelScope for classification
- **ngrok Tunnel**: Creates temporary public URL (secure but accessible from internet)
- **Data Storage**: All data stays on your Mac in the `data/` folder

### Privacy Tips
- Stop ngrok when not needed: `Ctrl+C` in ngrok terminal
- Clear sensitive data: Use "Clear Processed Data" button
- Keep API keys secure: Don't share `config.json`

---

## 📊 Tips for Best Results

### Image Quality
- **Good lighting** - Ensure text is clearly visible
- **Straight angles** - Avoid skewed or rotated text
- **High resolution** - Use good quality camera/scanner
- **Clear text** - Handwritten notes should be legible

### Processing Tips
- **Enable preprocessing** for better OCR accuracy
- **Process in batches** for efficiency
- **Review classifications** and provide feedback
- **Organize raw images** in folders by subject/date

### Mobile Usage
- **Same WiFi network** required for best performance
- **HTTPS tunnel** necessary for camera access
- **Close ngrok** when done to stop public access
- **Good phone camera** improves OCR results

---

## 🎯 Workflow Examples

### Daily Study Session
1. Take photos of practice problems with phone camera (via HTTPS tunnel)
2. Images automatically processed and classified
3. Review organized notes on any device
4. Search previous content using vector database

### Batch Processing Old Materials
1. Place scanned images in `data/raw/` folder
2. Run `python3 script/run_all.py` for batch processing
3. All images processed automatically
4. Find organized notes in `data/notes/` folder

### Real-time Processing
1. Start app with watch mode: `python3 script/run_all.py --watch`
2. Drop new images into `data/raw/` folder
3. Processing happens automatically
4. Get notifications when processing completes

---

## 🔄 Updates & Maintenance

### Regular Maintenance
- **Clear processed data** periodically to save space
- **Update dependencies** occasionally: `pip install -r requirements.txt --upgrade`
- **Check disk space** in `data/` folder
- **Backup important notes** to external storage

### Configuration Updates
- **API keys** - Update in `config.json` when needed
- **Paths** - Adjust folder locations if needed
- **AI settings** - Modify model parameters for different behavior

---

*For additional support or feature requests, check the project documentation or contact the development team.*