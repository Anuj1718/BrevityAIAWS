# Brevity AI - Deployment Guide

## Issues Fixed

### 1. ✅ "Not Found" Error on Page Refresh
**Problem**: When refreshing the browser on any route other than `/`, the site shows "Not found".

**Root Cause**: This is a common issue with Single Page Applications (SPAs). When you refresh on `/upload` or `/pricing`, the server looks for those actual files instead of serving `index.html` and letting React Router handle the routing.

**Solution**: Added redirect configuration files:
- `public/_redirects` - For Netlify/Render static sites
- `vercel.json` - For Vercel deployments
- `netlify.toml` - Alternative Netlify config
- `render.yaml` - Render static site config

All these files tell the server to redirect all routes to `index.html`, allowing React Router to handle navigation.

### 2. ✅ Slow Upload with No Progress Feedback
**Problem**: Large PDF uploads appear frozen with no progress indication.

**Solution**: Implemented real-time upload progress tracking in [Upload.jsx](./src/components/Upload/Upload.jsx):
- Replaced `fetch` API with `XMLHttpRequest` for upload progress events
- Added progress percentage display: "Uploading file... 45%"
- Progress bar updates smoothly from 0% to 30% during upload
- Better user experience with visual feedback

## Deployment Instructions

### Deploy to Render (Recommended)

#### Frontend (Static Site)
1. Connect your GitHub repository to Render
2. Create a new **Static Site**
3. Configure:
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
4. Add Environment Variable:
   - `VITE_API_URL` = `https://brevity.duckdns.org`
5. Deploy!

The `render.yaml` file will handle the routing automatically.

#### Backend (Web Service)
1. Create a new **Web Service** on Render
2. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd Backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.11+
3. Important: **Add persistent storage or cloud storage** (see Storage Solutions below)

### Deploy to Vercel

#### Frontend Only
```bash
cd Frontend
vercel
```

The `vercel.json` config will handle routing automatically.

### Deploy to Netlify

#### Frontend
```bash
cd Frontend
npm run build
netlify deploy --prod --dir=dist
```

Both `_redirects` and `netlify.toml` will handle routing.

## Storage Solutions (CRITICAL for Backend)

### Current Issue
Your backend stores files in `uploads/` and `outputs/` directories, which are **ephemeral on Render**. Files will be lost on:
- Service restart
- New deployment
- Idle timeout

### Recommended Solutions

#### Option 1: AWS S3 (Best for Production)
Add to `requirements.txt`:
```
boto3
```

Modify `app/services/file_handler.py` to use S3 instead of local storage.

#### Option 2: Render Disks (Easiest but Paid)
Add to your Render Web Service:
- Go to Settings → Disks
- Create a disk mounted at `/data`
- Update paths in code to use `/data/uploads` and `/data/outputs`

#### Option 3: Cloudinary (Good for PDFs)
Add to `requirements.txt`:
```
cloudinary
```

## Testing the Fixes

### Test SPA Routing
1. Navigate to any page (e.g., `/upload`)
2. Refresh the browser (F5)
3. Page should load correctly without "Not Found"

### Test Upload Progress
1. Select a large PDF (10MB+)
2. Click "Upload & Process"
3. You should see: "Uploading file... X%" with percentage increasing
4. Progress bar should update smoothly

## Environment Variables

### Frontend (.env)
```env
VITE_API_URL=https://brevity.duckdns.org
```

### Backend (.env)
```env
ALLOWED_ORIGINS=https://main.degqsw0mhmm75.amplifyapp.com,http://localhost:5173
PUBLIC_DOMAIN=brevity.duckdns.org
BACKEND_HOST=127.0.0.1
```

### Backend (.env)
```env
# Add when implementing cloud storage
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET=your-bucket-name
```

## Files Modified/Created

### New Files
- ✅ `Frontend/public/_redirects` - Netlify/Render redirect rules
- ✅ `Frontend/vercel.json` - Vercel routing config
- ✅ `Frontend/netlify.toml` - Netlify config
- ✅ `Frontend/render.yaml` - Render static site config

### Modified Files
- ✅ `Frontend/src/components/Upload/Upload.jsx` - Added upload progress tracking

## Next Steps

1. **Deploy Frontend** with new routing configs
2. **Test refresh** on all routes
3. **Implement Cloud Storage** for backend (S3 recommended)
4. **Add Environment Variables** for API URL
5. **Test upload progress** with large PDFs

## Support

If you encounter issues:
- Check browser console for errors
- Verify environment variables are set correctly
- Ensure backend URL is accessible from frontend
- Check Render logs for backend errors
