# MorphoSense AI — Streamlit edition

A multilingual (Azerbaijani / English / Russian) research demo for palm crease mask extraction and synthetic image-perturbation consistency tests. The algorithmic settings are preserved from `MorphoSense_AI_Colab_ROI_v3.ipynb`.

## Run locally

```bash
python -m venv .venv
# Activate your virtual environment, then:
pip install -r requirements.txt
streamlit run app.py
```

Or upload this folder to GitHub and deploy with Streamlit Community Cloud, selecting `app.py` as the entry point. The server needs internet access on first run to download the official MediaPipe HandLandmarker task model into `models/`. The `models/` folder is created automatically.

## What the demo does

1. Detects one palm using MediaPipe HandLandmarker and derives an approximate inner-palm ROI.
2. Runs Black-hat and Frangi crease-candidate extraction on the original image.
3. Applies low light, high light, low contrast, Gaussian noise, and Gaussian blur to the **same image**, while holding the ROI fixed.
4. Compares original and changed binary masks using IoU and Dice, including mask pixel counts.
5. Shows baseline measurements, visual comparisons, and exports an analysis ZIP.

### Scientific limits

IoU and Dice represent **mask self-consistency**, not ground-truth detection accuracy. An empty perturbed mask can produce IoU 0 and requires diagnosis. This tool is not a medical device and does not classify anatomical crease types or diagnose any disease. P2 and P3 historical data were obtained under different protocols.

### Privacy

The uploaded image is processed in the active Streamlit session; no persistent upload database is implemented. A downloaded ZIP **includes the original uploaded image**, so treat it as personal data. Hosting services may have their own processing and retention practices; obtain appropriate consent before uploading real participants' images.

### Reproducibility

Noise uses RNG seed 42, sigma 18. Gaussian blur uses kernel 7x7 and sigma 1.5. Low light multiplier 0.65; high light multiplier 1.25 plus 10; contrast multiplier 0.65 around 127.5. The original v3 preprocessing, ROI and morphological thresholds are retained.


## Gaussian noise diagnostics update
This release preserves the original five-test pipeline and adds a diagnostic expander.
`gaussian_noise_diagnostics.csv` records score-positive pixels, thresholded pixels, cleaned pixels, and a **separate experimental** median-filter (3x3) trial. The original reported IoU/Dice remain unchanged. The report ZIP includes trial comparison images.
`packages.txt` includes Linux libraries needed for OpenCV/MediaPipe on Streamlit Community Cloud.
