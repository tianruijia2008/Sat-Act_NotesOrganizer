# SAT/ACT Notes Organizer - User Guide

A streamlined web application that converts your SAT/ACT study material images into organized, searchable notes using AI.

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project
cd Sat:Act_NotesOrganizer

# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR
# macOS:
brew install tesseract
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

### 2. Configuration

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

**Alternative: Environment Variables**
```bash
export AI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
export AI_API_KEY="your-api-key-here"
export AI_MODEL="qwen-turbo"
```

### 3. Run the Application

```bash
streamlit run ui/app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📱 Using the Application

### Step 1: Upload Images
- Click "Browse files" or drag and drop images
- Supported formats: PNG, JPG, JPEG, BMP, TIFF
- Upload multiple images at once
- Preview images before processing

### Step 2: Process Images
- Click "🚀 Process Images" button
- Watch the progress bar as each image is processed
- OCR extracts text from images
- AI analyzes and organizes the content

### Step 3: View Results
- See summary by subject (Math, English, Science, etc.)
- Expand each result to view detailed notes
- Generated notes include:
  - Subject classification
  - Content type (notes, practice problems, etc.)
  - Key concepts
  - Organized summary
  - Original extracted text

### Step 4: Save Notes
- All notes are automatically saved as markdown files
- Located in `data/notes/` directory
- Files named with timestamp and source image
- Can be opened in any markdown editor

---

## 🎯 Features Explained

### Automatic Classification
The AI automatically identifies:
- **Subject**: Math, English, Science, Social Studies
- **Content Type**: Notes, Practice Problems, Wrong Answer Explanations
- **Key Concepts**: Important topics and themes
- **Confidence Level**: How certain the AI is about the classification

### Generated Notes Structure
Each note includes:
- **Header**: Subject and content type
- **Metadata**: Source image, timestamp, confidence
- **Key Concepts**: Bullet-pointed main topics
- **Summary**: Brief overview of content
- **Organized Notes**: Structured, readable content
- **Original Text**: Raw OCR output for reference

### File Management
- **Automatic Saving**: Notes saved immediately after processing
- **Clear Data**: Button to reset all uploaded images and results
- **Timestamp Naming**: Files named with date/time to avoid conflicts
- **Markdown Format**: Compatible with Obsidian, Notion, and other note apps

---

## 💡 Tips for Best Results

### Image Quality
- Use clear, well-lit photos
- Ensure text is readable and not blurry
- Avoid shadows and glare
- Crop images to focus on the study material
- High contrast works best (dark text on light background)

### Content Types That Work Well
- ✅ Handwritten notes
- ✅ Textbook pages
- ✅ Practice problems
- ✅ Formula sheets
- ✅ Study guides
- ✅ Test questions

### Processing Tips
- Process related materials together
- Use descriptive filenames when possible
- Review generated notes for accuracy
- Keep original images as backup

---

## 🔧 Troubleshooting

### OCR Issues
**Problem**: No text extracted from images
**Solutions**:
- Check image quality and lighting
- Ensure tesseract is installed correctly
- Try preprocessing images (crop, adjust contrast)
- Verify image contains readable text

### AI Processing Errors
**Problem**: AI analysis fails
**Solutions**:
- Verify API key in config.json
- Check internet connection
- Ensure API quota/credits available
- Try with simpler content first

### Import Errors
**Problem**: Module import failures
**Solutions**:
- Run `pip install -r requirements.txt`
- Verify Python 3.8+ is installed
- Check for conflicting package versions
- Try creating a fresh virtual environment

### File Access Issues
**Problem**: Cannot save notes or access files
**Solutions**:
- Check file permissions in project directory
- Ensure sufficient disk space
- Try running with administrator privileges
- Verify data directory exists

---

## 📂 Project Structure

```
Sat:Act_NotesOrganizer/
├── ui/
│   └── app.py                 # Main web application
├── src/
│   ├── ocr_processor.py      # Text extraction
│   ├── ai_processor.py       # AI analysis
│   ├── notes_saver.py        # Note generation
│   └── utils.py              # Helper functions
├── data/
│   ├── temp/                 # Temporary uploads
│   └── notes/                # Generated notes
├── config.json               # Configuration
├── requirements.txt          # Dependencies
└── README.md
```

---

## 🔑 API Configuration

### ModelScope (Recommended)
1. Sign up at https://www.modelscope.cn/
2. Get API key from dashboard
3. Add to config.json as shown above

### Other Compatible APIs
The app works with any OpenAI-compatible API:
- OpenAI GPT
- Anthropic Claude (via proxy)
- Local LLMs (ollama, etc.)
- Other cloud providers

Just update the `base_url` and `api_key` in config.json.

---

## 📝 Output Examples

### Math Notes Example
```markdown
# Math - Practice Problem

**Source:** algebra_practice.jpg
**Generated:** 2024-01-15 14:30:25
**Confidence:** 92%

## Key Concepts
- Quadratic equations
- Factoring
- Solving methods

## Summary
Practice problem involving quadratic equation solving using multiple methods.

## Notes
This problem demonstrates solving x² + 5x + 6 = 0 using:
1. Factoring: (x + 2)(x + 3) = 0
2. Solutions: x = -2 or x = -3
...
```

### English Notes Example
```markdown
# English - Notes

**Source:** essay_tips.jpg
**Generated:** 2024-01-15 14:32:10
**Confidence:** 88%

## Key Concepts
- Essay structure
- Thesis statements
- Supporting evidence

## Summary
Guidelines for writing effective SAT essays with clear structure and strong arguments.

## Notes
Key components of a strong essay:
- Introduction with clear thesis
- Body paragraphs with evidence
- Conclusion that reinforces main points
...
```

---

## 🆘 Support

### Common Questions

**Q: Can I process handwritten notes?**
A: Yes! The OCR works well with clear handwriting.

**Q: What file size limits are there?**
A: No hard limits, but larger images take longer to process.

**Q: Can I edit the generated notes?**
A: Yes, all notes are saved as standard markdown files.

**Q: Does this work offline?**
A: OCR works offline, but AI analysis requires internet connection.

### Getting Help

If you encounter issues:
1. Check this troubleshooting section first
2. Verify your configuration and dependencies
3. Try with simple test images
4. Check the console/terminal for error messages

---

## 🔄 Updates and Maintenance

### Keeping Up to Date
- Pull latest changes from repository
- Update dependencies: `pip install -r requirements.txt --upgrade`
- Check for configuration changes

### Data Management
- Notes accumulate in `data/notes/`
- Use "Clear All Data" button to reset
- Back up important notes before clearing
- Consider organizing notes by date or subject

---

This completes the user guide for the SAT/ACT Notes Organizer. The app is designed to be simple and efficient - upload images, get organized notes, and focus on studying!