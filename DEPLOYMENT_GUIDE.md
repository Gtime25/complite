# CompLite Deployment Guide (No GitHub Required)

## Option 1: Railway (Recommended - Easiest)

### Step 1: Prepare Your Files
✅ **DONE** - Your deployment package `complite-deployment.zip` is ready!

### Step 2: Deploy to Railway
1. **Go to [railway.app](https://railway.app)**
2. **Sign up/Login** with your email
3. **Click "New Project"**
4. **Choose "Deploy from template" → "Empty Project"**
5. **Click "Upload" and select your `complite-deployment.zip` file**
6. **Wait for Railway to process your files**

### Step 3: Configure Environment Variables
1. **Go to your project dashboard**
2. **Click "Variables" tab**
3. **Add these environment variables:**
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   SLACK_WEBHOOK_URL=your_slack_webhook_url_here
   JWT_SECRET=your_jwt_secret_here
   ```

### Step 4: Deploy
1. **Railway will automatically detect your FastAPI app**
2. **Click "Deploy"**
3. **Wait for deployment to complete**
4. **Your app will be live at the provided URL!**

---

## Option 2: Render.com

### Step 1: Deploy Backend
1. **Go to [render.com](https://render.com)**
2. **Create new "Web Service"**
3. **Upload your `complite-deployment.zip`**
4. **Configure:**
   - **Name:** `complite-backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `cd soxlite-backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Add environment variables**
6. **Deploy**

### Step 2: Deploy Frontend
1. **Create new "Static Site"**
2. **Upload the same zip file**
3. **Configure:**
   - **Build Command:** `cd soxlite-frontend && npm install && npm run build`
   - **Publish Directory:** `soxlite-frontend/build`
4. **Deploy**

---

## Option 3: Heroku (CLI Required)

If you want to install Heroku CLI:

```bash
# Install Heroku CLI
brew install heroku/brew/heroku

# Login to Heroku
heroku login

# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set OPENAI_API_KEY=your_key
heroku config:set SLACK_WEBHOOK_URL=your_webhook
heroku config:set JWT_SECRET=your_secret

# Deploy
git init
git add .
git commit -m "Initial commit"
heroku git:remote -a your-app-name
git push heroku main
```

---

## Environment Variables You Need

### Required:
- `OPENAI_API_KEY` - Your OpenAI API key from [platform.openai.com](https://platform.openai.com)

### Optional:
- `SLACK_WEBHOOK_URL` - Slack webhook for alerts
- `JWT_SECRET` - Secret for JWT tokens (auto-generated if not provided)

---

## After Deployment

1. **Test your app** at the provided URL
2. **Check the logs** if there are any issues
3. **Your app is now live on the web!**

## Troubleshooting

### Common Issues:
1. **Import errors** - Check that all dependencies are in `requirements.txt`
2. **API key errors** - Verify your OpenAI API key is correct
3. **Port issues** - Make sure you're using `$PORT` environment variable
4. **Build failures** - Check the deployment logs for specific errors

### Need Help?
- Check the deployment platform's documentation
- Look at the build logs for error messages
- Ensure all environment variables are set correctly 