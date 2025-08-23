# Deploy Medical Analyzer to Render

## Quick Deployment Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Deploy medical analyzer to Render"
   git push origin main
   ```

2. **Create Render Service**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file

3. **Configuration**
   - Service Name: `medical-report-analyzer`
   - Environment: `Python`
   - Build Command: (auto-detected from render.yaml)
   - Start Command: (auto-detected from render.yaml)

## What's Configured

✅ **Tesseract OCR** - Installed via apt-get in build command
✅ **Python Dependencies** - All packages in requirements.txt
✅ **Port Configuration** - Uses Render's $PORT environment variable
✅ **Gunicorn Server** - Production WSGI server
✅ **File Upload Support** - Handles PDF, JPG, PNG files up to 15MB

## Features Included

🔬 **Advanced Medical Analysis**
- 150+ medical parameters
- Blood tests, ultrasound reports, lab results
- Multi-method OCR for scanned documents
- Normal/abnormal value detection

🎯 **File Support**
- PDF documents (text + scanned)
- Image files (JPG, JPEG, PNG)
- Direct text input

## Environment Variables (Optional)

You can add these in Render dashboard if needed:
- `PYTHON_VERSION=3.11.4` (already set in render.yaml)

## Testing Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python medical_analyzer.py
```

Visit: http://localhost:8000

## Troubleshooting

If deployment fails:
1. Check build logs in Render dashboard
2. Ensure all files are committed to git
3. Verify render.yaml syntax
4. Check that requirements.txt has all dependencies

## Post-Deployment

Once deployed, your app will be available at:
`https://medical-report-analyzer.onrender.com`

The app will automatically:
- Install Tesseract OCR
- Set up all Python dependencies
- Configure proper port binding
- Start with Gunicorn for production