# Farmhouse Frames Splitter

A Streamlit web app that lets you upload a photo, lay out custom-sized canvas panels on top of it, and export each panel as a print-ready JPEG — all in one ZIP file ready to upload to Printify or CanvasChamp.

## Features

- Load an image from your computer or a URL
- Define panels by width and height (in inches) at a chosen DPI
- Position each panel on the image with sliders
- Preview the layout with a live mockup
- Export all panels as a ZIP of high-quality JPEGs

## Deploy on Streamlit Community Cloud

1. Fork or push this repo to your GitHub account.
2. Go to [streamlit.io](https://streamlit.io) and sign in with GitHub.
3. Click **New app**, select this repository, and click **Deploy**.
4. Streamlit will give you a shareable URL (e.g. `https://your-app.streamlit.app`).

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
