# SAT/ACT Notes Organizer

A tool to automatically organize SAT/ACT study materials by extracting text from images, classifying content, and generating structured markdown files.

## Features

- **OCR Processing**: Extract text from images of study materials
- **AI Classification**: Automatically classify content as notes or wrong questions
- **Markdown Generation**: Create organized markdown files for easy review
- **Web Interface**: User-friendly UI for uploading images and viewing results
- **Vector Database**: Store and retrieve content using semantic search

## Prerequisites

- Python 3.8 or higher
- Tesseract OCR installed on your system
- API access to ModelScope (for AI processing)

## 📚 Complete Setup & Usage Guide

**For detailed setup instructions, usage examples, and troubleshooting, see:**

**➡️ [USER_GUIDE.md](USER_GUIDE.md) ⬅️**

The user guide includes:
- 🛠 **Complete setup instructions** (dependencies, API keys, mobile camera)
- 🚀 **Multiple usage methods** (desktop, mobile, command line, Zed tasks)
- 📱 **Mobile camera setup** (ngrok tunnel for iPhone/iPad camera access)
- 🎮 **Web interface walkthrough** (all tabs and features explained)
- ⚠️ **Troubleshooting section** (common issues and solutions)
- 💡 **Tips for best results** (image quality, processing workflow)

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   brew install tesseract ngrok/ngrok/ngrok
   ```

2. **Setup ngrok (for mobile camera):**
   ```bash
   # Sign up at https://dashboard.ngrok.com/signup
   ngrok config add-authtoken YOUR_TOKEN
   ```

3. **Configure API key in `config.json`**

4. **Start the app:**
   ```bash
   python3 -m streamlit run ui/app.py --server.port 8501
   ```

5. **For mobile camera, create HTTPS tunnel:**
   ```bash
   ngrok http 8501
   ```

## How It Works

1. **Image Processing**: Images are processed using Tesseract OCR to extract text
2. **AI Analysis**: The extracted text is analyzed by an AI model to classify content
3. **Content Organization**: Related content is grouped and organized into structured formats
4. **Markdown Generation**: Organized content is saved as markdown files for easy review
5. **Vector Storage**: Content is stored in a vector database for semantic search and retrieval

## Project Structure

- `src/`: Core modules for OCR processing, AI analysis, and file management
- `script/`: Main orchestrator scripts
- `data/`: Storage for raw images, processed notes, and vector database
- `ui/`: Web interface using Streamlit
- `config.json`: Configuration file for API keys and settings

## More Information

For comprehensive documentation, see **[USER_GUIDE.md](USER_GUIDE.md)**

## License

This project is licensed under the MIT License.