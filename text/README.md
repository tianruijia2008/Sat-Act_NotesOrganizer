# SAT/ACT Notes Organizer

A streamlined web application that automatically extracts text from SAT/ACT study material images and generates organized notes using AI.

## Features

- 📤 **Easy Upload**: Drag and drop images of your study materials
- 🔍 **OCR Processing**: Extract text from images using advanced OCR
- 🤖 **AI Analysis**: Automatically classify and organize content by subject and type
- 📝 **Structured Notes**: Generate clean, organized markdown notes
- 🎯 **Subject Classification**: Automatically categorize content (Math, English, Science, etc.)
- ✨ **Simple Interface**: Clean, intuitive web interface

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AI API** (see Configuration section below)

3. **Run the Application**
   ```bash
   streamlit run ui/app.py
   ```

4. **Use the App**
   - Open your browser to the displayed URL (usually http://localhost:8501)
   - Upload images of your study materials
   - Click "Process Images" to generate organized notes
   - View and download your structured notes

## Configuration

Create a `config.json` file in the project root:

```json
{
  "providers": [
    {
      "name": "modelscope",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
      "api_key": "your-api-key-here",
      "models": ["qwen-turbo"]
    }
  ]
}
```

Or set environment variables:
- `AI_BASE_URL`: API endpoint URL
- `AI_API_KEY`: Your API key  
- `AI_MODEL`: Model name (default: qwen-turbo)

## Project Structure

```
Sat:Act_NotesOrganizer/
├── ui/
│   └── app.py              # Main Streamlit application
├── src/
│   ├── ocr_processor.py    # Text extraction from images
│   ├── ai_processor.py     # AI content analysis
│   ├── notes_saver.py      # Save organized notes as markdown
│   └── utils.py            # Utility functions
├── data/
│   ├── temp/               # Temporary uploaded files
│   └── notes/              # Generated markdown notes
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies
└── README.md
```

## How It Works

1. **Upload**: Select one or more images containing SAT/ACT study materials
2. **OCR**: Text is extracted from images using pytesseract with preprocessing
3. **AI Analysis**: Content is analyzed and classified by subject and type
4. **Organization**: AI generates structured notes with key concepts and summaries
5. **Save**: Notes are saved as markdown files with timestamps and metadata

## Dependencies

- **streamlit**: Web interface
- **pytesseract**: OCR text extraction  
- **Pillow**: Image processing
- **opencv-python-headless**: Image preprocessing
- **numpy**: Numerical operations
- **requests**: API communication

## Output Format

Generated notes include:
- **Subject classification** (Math, English, Science, etc.)
- **Content type** (Notes, Practice Problems, etc.)
- **Key concepts** extracted from the material
- **Organized notes** with clear structure
- **Summary** of main points
- **Original text** for reference
- **Metadata** (source, timestamp, confidence)

## Tips for Best Results

- Use clear, well-lit images
- Ensure text is readable and not blurry
- Crop images to focus on the study material
- Use high-contrast images (dark text on light background works best)

## Troubleshooting

**OCR not working?**
- Make sure tesseract is installed: `brew install tesseract` (macOS) or `apt-get install tesseract-ocr` (Ubuntu)
- Check image quality and lighting

**AI processing failing?**
- Verify your API key and endpoint in config.json
- Check your internet connection
- Ensure you have sufficient API credits/quota

**Import errors?**
- Run `pip install -r requirements.txt` to install all dependencies
- Make sure you're using Python 3.8 or higher

## License

MIT License - feel free to use and modify for your SAT/ACT prep needs!