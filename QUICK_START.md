# 🚀 Quick Start Guide - SciWeb Learning Platform

## Step 1: Initialize the Database

Run this command to set up the grade scanner tables:

```bash
python init_grader.py
```

You should see:
```
Creating grade scanner tables...
[OK] Grade scanner tables created successfully!

You can now use the grade scanner at /grader
```

## Step 2: Start the Application

```bash
python app.py
```

The app will run at: **http://localhost:5000**

## Step 3: Explore the New Features

### 🎨 Premium UI
- Notice the stunning purple-pink gradient background
- Smooth animations on every interaction
- Modern glassmorphism effects
- Enhanced dark mode (toggle in settings)

### 🎓 AI Grade Scanner

1. **Access the Grader**
   - Click the "Grader" button in the navigation (pink gradient button)
   - Or visit: http://localhost:5000/grader

2. **Upload an Assignment**
   - Click "Upload Assignment"
   - Drag & drop an image of handwritten work OR click to browse
   - Supported formats: JPG, PNG, PDF, HEIC
   - Fill in assignment details (title, subject)
   - Click "Submit for Grading"

3. **Watch AI Process**
   - See the animated processing screen
   - AI analyzes handwriting and evaluates answers
   - Usually takes 10-30 seconds

4. **View Results**
   - See your overall score with animated circle
   - Read detailed AI feedback
   - Review problem-by-problem breakdown
   - Each problem marked as correct ✅ or incorrect ❌
   - Get constructive suggestions for improvement

5. **Track Progress**
   - Return to /grader dashboard
   - View submission history
   - See all past grades and feedback

## 🎯 Tips for Best Grade Scanner Results

1. **Take Clear Photos**
   - Good lighting
   - Hold camera steady
   - Keep page flat
   - Fill the frame with the work

2. **Legible Handwriting**
   - Write clearly
   - Avoid smudges
   - Use dark pen/pencil

3. **Include Everything**
   - Show the complete problem
   - Include your full answer
   - Don't cut off any work

## 🎨 UI Features to Try

### Animations
- Watch the splash screen on dashboard load
- Hover over project cards
- See smooth transitions everywhere
- Animated score counter on results page

### Gradients
- Purple-to-pink primary gradient
- Cyan accent buttons
- Warm pink-yellow grader button
- Glassmorphic cards with blur effects

### Interactive Elements
- Drag-and-drop file upload
- Real-time image preview
- Progress bars with smooth animation
- Tooltip hover states

## 🔧 Troubleshooting

### "No file uploaded" error
- Make sure to select a file before submitting
- Check file size is under 10MB
- Verify file format (JPG, PNG, PDF, HEIC)

### Grading takes too long
- Normal processing: 10-30 seconds
- Complex assignments may take up to 1 minute
- If stuck after 2 minutes, check your API key

### Database error
- Run `python init_grader.py` to create tables
- Check that SQLite database exists
- Ensure write permissions in directory

### API Key Missing
- Set OPENAI_API_KEY in your environment
- Create a `.env` file with your key
- Restart the application after adding key

## 📱 Navigation Map

```
Homepage (/)
├── Dashboard - View all learning projects
├── Feed - Social learning feed
├── Messages - Chat with study groups
├── Grader - AI Grade Scanner (NEW!)
│   ├── Upload - Submit work for grading
│   ├── Process - Watch AI analyze
│   └── Results - View scores & feedback
├── Assistant - AI learning templates
└── Styles - Conversation style options
```

## 🎓 Example Workflow

1. **Student completes math homework**
2. **Takes photo with phone camera**
3. **Opens SciWeb → Grader → Upload**
4. **Drags photo into upload zone**
5. **Enters "Math Homework Ch 5" as title**
6. **Selects "Mathematics" as subject**
7. **Clicks "Submit for Grading"**
8. **Watches processing animation (15 seconds)**
9. **Sees results: 85% score**
10. **Reads feedback: "Problem 3 needs work on factoring"**
11. **Reviews specific comments on each problem**
12. **Practices problem 3 again based on feedback**
13. **Resubmits for improved score**

## 🌟 What Makes This Special

### Virtual Teacher
- 24/7 availability
- Instant feedback
- Never gets tired
- Consistent grading
- Patient explanations

### Learning Focus
- Detailed explanations, not just scores
- Helps understand mistakes
- Encourages practice
- Tracks improvement over time

### Beautiful Design
- Modern, professional appearance
- Smooth, polished interactions
- Engaging animations
- Easy to use interface

## 🔮 Coming Soon

- Visual annotations on graded images
- Progress charts and analytics
- Custom grading rubrics
- Teacher classroom dashboard
- Mobile app
- Achievement badges
- Study streak tracking

## ❓ Need Help?

Check the full documentation in `UPGRADE_SUMMARY.md`

---

**Ready to start learning? Launch the app and click the Grader button!** 🚀
