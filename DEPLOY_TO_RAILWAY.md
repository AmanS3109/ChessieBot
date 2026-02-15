# 🚀 Deploying ChessieBot to Railway

This guide will help you deploy your **ChessieBot** FastAPI application to [Railway.app](https://railway.app/).

## Prerequisites

1.  **GitHub Repository**: Your code must be pushed to a GitHub repository.
2.  **Railway Account**: Sign up at [railway.app](https://railway.app/).
3.  **API Keys**: You need your `GROQ_API_KEY` and `GOOGLE_API_KEY`.

## Steps

### 1. Push Code to GitHub

Ensure all your latest changes, including the new `Procfile` and `nixpacks.toml`, are committed and pushed.

```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 2. Create New Project on Railway

1.  Go to your [Railway Dashboard](https://railway.app/dashboard).
2.  Click **"New Project"**.
3.  Select **"Deploy from GitHub repo"**.
4.  Select your **ChessieBot** repository.
5.  Click **"Deploy Now"**.

### 3. Configure Environment Variables

1.  Click on your project card in the dashboard.
2.  Go to the **"Variables"** tab.
3.  Add the following variables:
    *   `GROQ_API_KEY`: Your Groq API key.
    *   `GOOGLE_API_KEY`: Your Google Gemini API key.
    *   `ENV`: `production` (optional, but good practice).

## Troubleshooting

-   **Build Failed?** Check the "Build Logs". Issue usually related to `requirements.txt`.
-   **App Crashing?** Check "Deploy Logs". Usually missing environment variables or port issues.
-   **Audio/Video Issues?** Ensure `ffmpeg` is installed (handled by `nixpacks.toml`).

## Note on 'nixpacks.toml'

We added a `nixpacks.toml` file to ensure `ffmpeg` is installed in the environment, which is required for:
-   Audio processing (Whisper STT).
-   Video processing (yt-dlp).
