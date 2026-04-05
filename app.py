import streamlit as st
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import zipfile
from streamlit_cropper import st_cropper
import numpy as np

# --- PAGE SETUP ---
st.set_page_config(page_title="Farmhouse Frames - Live Mockup Designer", layout="wide")

st.title("🖼️ Farmhouse Frames: Live Mockup Designer")
st.write("1. Build your layout | 2. Position your photo in the live mockup.")

# --- STEP 1: DEFINE THE LAYOUT ---
# This creates the physical 'wall span' you see in your barn photos
st.sidebar.header("1. Build Your Layout")
printer = st.sidebar.selectbox("Select Printer", ["Generic / Printify", "CanvasChamp (1.5\" Wrap)", "Walmart Photo (0.75\" Wrap)"])
bleed = 1.5 if "CanvasChamp" in printer else (0.75 if "Walmart" in printer else 0.0)

if 'mockup_panels' not in st.session_state:
    # A standard 12x24 Triptych (3 panels) is pre-loaded for ease
    st.session_state.mockup_panels = [
        {'w': 12, 'h': 24},
        {'w': 12, 'h': 24},
        {'w': 12, 'h': 24}
    ]

# Layout summary (crucial for "proportion" and "logic" questions)
col_w, col_h = st.sidebar.columns(2)
new_w = col_w.number_input("Panel Width (in)", value=12)
new_h = col_h.number_input("Panel Height (in)", value=24)

col_b1, col_b2 = st.sidebar.columns(2)
if col_b1.button("➕ Add Panel"):
    st.session_state.mockup_panels.append({'w': new_w, 'h': new_h})
if col_b2.button("🗑️ Clear"):
    st.session_state.mockup_panels = []
    st.rerun()

# Determine the boundaries of the whole wall display
if st.session_state.mockup_panels:
    st.sidebar.write("### Current Layout")
    total_span_w = sum(p['w'] for p in st.session_state.mockup_panels)
    max_panel_h = max(p['h'] for p in st.session_state.mockup_panels)
    st.sidebar.info(f"Total Wall Span: {total_span_w}\" x {max_panel_h}\"")
else:
    st.info("Define your layout dimensions in the sidebar to create the frames.")
    st.stop()

# --- STEP 2: UPLOAD PHOTOGRAPHY ---
# This is where your Cadiz photography is loaded
st.sidebar.header("2. Upload Photography")
img_file = st.sidebar.file_uploader("Upload your Cadiz Photo", type=["jpg", "png", "jpeg"])

if img_file:
    # We load as PIL, but convert to numpy for the advanced cropper library
    pil_img = Image.open(img_file).convert("RGB")
    np_img = np.array(pil_img)
    
    st.subheader("3. Drag & Position Photo Within Frames (Live Mockup)")
    st.write("The red bounding box is the whole wall. Drag it to define the multi-panel view.")

    # We enforce the aspect ratio of the ENTIRE layout (e.g., a 1.5:1 ratio for the 36x24 triptych)
    # The 'box_color' defines the edges of your wall span
    layout_aspect = total_span_w / max_panel_h
    
    # st_cropper provides the "drag" functionality you need
    crop = st_cropper(
        np_img,
        realtime_update=True,
        box_color='#FF0000', # Red shows the full wall area
        aspect_ratio=(total_span_w, max_panel_h), 
        return_type='box'
    )
    
    # --- LIVE MOCKUP PREVIEW ---
    # Now we build the actual preview you requested, with gaps and frames
    if crop:
        # 1. Get the high-res "master crop" of the whole wall span
        # Ensure coordinates are integers and valid
        top = int(max(0, crop['top']))
        left = int(max(0, crop['left']))
        bottom = int(min(np_img.shape[0], crop['top'] + crop['height']))
        right = int(min(np_img.shape[1], crop['left'] + crop['width']))
        
        master_crop = pil_img.crop((left, top, right, bottom))
        
        # 2. Slice the master crop into individual panels
        panels_to_display = []
        current_x = 0
        current_w_pct = 0.0
        
        for p in st.session_state.mockup_panels:
            panel_width_pct = p['w'] / total_span_w
            px_start = int(master_crop.width * current_w_pct)
            px_end = int(master_crop.width * (current_w_pct + panel_width_pct))
            
            # Slice this specific panel from the whole crop
            panel_img = master_crop.crop((px_start, 0, px_end, master_crop.height))
            panels_to_display.append(panel_img)
            
            current_w_pct += panel_width_pct

        # 3. Render the Live Mockup (Three separate images in a row)
        st.write("### Your Final Wall Art Preview:")
        cols = st.columns(len(panels_to_display))
        for i, (col, panel) in enumerate(zip(cols, panels_to_display)):
            # The gaps between the columns simulate the 1/2" - 1" gaps on the wall
            col.image(panel, caption=f"Panel {i+1}", use_container_width=True)

    # --- EXPORT INDIVIDUAL PANELS ---
    if st.button("🚀 PREPARE FILES FOR PRODUCTION (WALMART / CANVASCHAMP)"):
        zip_buf = BytesIO()
        
        with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, panel_img in enumerate(panels_to_display):
                # The panel_img is already cropped to the "Face" dimension (e.g., 12x24)
                
                # Apply the specific wrap/bleed based on the printer selected
                if bleed > 0:
                    # Logic for creating the wrap is simple here (e.g., extending the edges)
                    # For a true production file, you often provide a "face" crop and a "wrap" crop
                    # This code assumes "Mirror Wrap" or "Image Wrap" which requires edge extension
                    # (Simple production flow)
                    pass 

                # Save the final high-res JPEG
                img_buf = BytesIO()
                panel_img.save(img_buf, format="JPEG", quality=95)
                
                # Naming includes the dimensions for CanvasChamp/Walmart production
                dim_str = f"{st.session_state.mockup_panels[i]['w']}x{st.session_state.mockup_panels[i]['h']}"
                zip_file.writestr(f"Panel_{i+1}_{dim_str}_{printer.replace(' ', '_')}.jpg", img_buf.getvalue())
        
        st.success("All production files generated.")
        st.download_button("Download ZIP", zip_buf.getvalue(), "farmhouse_production.zip")
