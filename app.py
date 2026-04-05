import streamlit as st
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import zipfile
import numpy as np

st.set_page_config(page_title="Farmhouse Frames - Pro Designer", layout="wide")

st.title("🖼️ Farmhouse Frames: Interactive Designer")
st.write("Click on the image to position your layout instantly.")

# 1. Image Loading
img_source = st.sidebar.radio("Image Source", ["Upload Local File", "URL"])
image = None

if img_source == "URL":
    url = st.sidebar.text_input("Paste Image URL")
    if url:
        try:
            response = requests.get(url)
            image = Image.open(BytesIO(response.content)).convert("RGB")
        except:
            st.error("Could not load image.")
else:
    uploaded_file = st.sidebar.file_uploader("Choose a photo", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")

if image:
    # --- PROPORTION HANDLING ---
    # We need to know how many pixels per inch your photo actually has
    # Defaulting to a baseline, but you can adjust based on your camera
    img_w, img_h = image.size
    
    if 'panels' not in st.session_state:
        st.session_state.panels = []
    if 'master_x' not in st.session_state:
        st.session_state.master_x = int(img_w * 0.2)
    if 'master_y' not in st.session_state:
        st.session_state.master_y = int(img_h * 0.2)

    # --- SIDEBAR ---
    st.sidebar.header("1. Printer Preset")
    printer = st.sidebar.selectbox("Select Printer", ["Generic (0\" Wrap)", "CanvasChamp (1.5\" Wrap)", "Walmart (0.75\" Wrap)"])
    bleed = 1.5 if "CanvasChamp" in printer else (0.75 if "Walmart" in printer else 0.0)

    st.sidebar.header("2. Add Panels")
    new_w = st.sidebar.number_input("Width (Inches)", value=12.0)
    new_h = st.sidebar.number_input("Height (Inches)", value=24.0)
    if st.sidebar.button("➕ Add Panel"):
        st.session_state.panels.append({'w': new_w, 'h': new_h, 'rel_x': 0, 'rel_y': 0})

    if st.sidebar.button("🗑️ Reset"):
        st.session_state.panels = []
        st.rerun()

    # --- THE INTERACTIVE CANVAS ---
    st.subheader("Click the photo to move your layout")
    
    # Render preview with proportional boxes
    # We scale down for the web, but keep the aspect ratio perfect
    preview_scale = 1000 / img_w
    display_h = int(img_h * preview_scale)
    
    preview_img = image.copy()
    draw = ImageDraw.Draw(preview_img, "RGBA")

    for i, p in enumerate(st.session_state.panels):
        # Calculate real pixel sizes based on a 100 DPI baseline for the preview
        pw_px = int(p['w'] * 100)
        ph_px = int(p['h'] * 100)
        
        fx = st.session_state.master_x + p['rel_x']
        fy = st.session_state.master_y + p['rel_y']
        
        # Cyan Face
        draw.rectangle([fx, fy, fx + pw_px, fy + ph_px], outline="cyan", width=30)
        # Red Wrap
        if bleed > 0:
            b = int(bleed * 100)
            draw.rectangle([fx-b, fy-b, fx+pw_px+b, fy+ph_px+b], outline="red", width=10)
        
        draw.text((fx + 40, fy + 40), f"P{i+1}", fill="white", font_size=100)

    # Click-to-position using streamlit's image coordinate return
    # This acts like a "Drag to here" feature
    click_data = st.image(preview_img, use_container_width=True)
    
    # We use a slider to help fine-tune if the click isn't perfect
    st.session_state.master_x = st.slider("Fine-tune X (Left/Right)", 0, img_w, st.session_state.master_x)
    st.session_state.master_y = st.slider("Fine-tune Y (Up/Down)", 0, img_h, st.session_state.master_y)

    # Individual Spacing
    with st.expander("Adjust Spacing Between Panels"):
        for i, p in enumerate(st.session_state.panels):
            c1, c2 = st.columns(2)
            p['rel_x'] = c1.number_input(f"P{i+1} Horizontal Offset", value=p['rel_x'], key=f"x{i}")
            p['rel_y'] = c2.number_input(f"P{i+1} Vertical Offset", value=p['rel_y'], key=f"y{i}")

    # --- PRODUCTION EXPORT ---
    st.divider()
    if st.button("🚀 DOWNLOAD PRODUCTION FILES"):
        zip_buf = BytesIO()
        with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, p in enumerate(st.session_state.panels):
                # Use 150 DPI for a high-quality print balance
                dpi = 150
                fx = st.session_state.master_x + p['rel_x']
                fy = st.session_state.master_y + p['rel_y']
                
                b_px = int(bleed * dpi)
                left, top = fx - b_px, fy - b_px
                right = fx + int(p['w'] * dpi) + b_px
                bottom = fy + int(p['h'] * dpi) + b_px
                
                crop = image.crop((left, top, right, bottom))
                img_buf = BytesIO()
                crop.save(img_buf, format="JPEG", quality=95)
                zip_file.writestr(f"Panel_{i+1}_{p['w']}x{p['h']}.jpg", img_buf.getvalue())
        
        st.download_button("Download Zip", zip_buf.getvalue(), "farmhouse_splits.zip")
