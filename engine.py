"""MorphoSense AI v3 pipeline, ported from the supplied Colab v3 notebook.
No diagnosis or anatomical ground-truth validation is provided.
"""
import io, os, zipfile, urllib.request
import cv2
import numpy as np
import pandas as pd
from PIL import Image
from scipy.ndimage import label
from skimage.filters import frangi
from skimage.morphology import remove_small_objects

MODEL_URL='https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'
CONDITIONS=['Low light','High light','Low contrast','Gaussian noise','Gaussian blur']
METHODS=['Black-hat','Frangi']
P2=pd.DataFrame([['Low light',.5478,.4998],['High light',.679,.7345],['Low contrast',.5765,.5248],['Gaussian noise',.011,.0097],['Gaussian blur',.4023,.3462]],columns=['Perturbation','Black-hat IoU','Frangi IoU'])
P3=pd.DataFrame([['Black-hat',17,3.512096,1264.882353,71.684028],['Frangi',17,4.728384,2689.705882,48.811831]],columns=['Method','Images','Coverage (%)','Components','Mean component area (pixels)'])

def get_landmarker(model_path):
    import mediapipe as mp
    os.makedirs(os.path.dirname(model_path),exist_ok=True)
    if not os.path.isfile(model_path):
        urllib.request.urlretrieve(MODEL_URL,model_path)
    opts=mp.tasks.vision.HandLandmarkerOptions(base_options=mp.tasks.BaseOptions(model_asset_path=model_path),running_mode=mp.tasks.vision.RunningMode.IMAGE,num_hands=1)
    return mp.tasks.vision.HandLandmarker.create_from_options(opts)

def palm_roi(rgb,landmarker):
    import mediapipe as mp
    h,w=rgb.shape[:2]
    result=landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB,data=np.ascontiguousarray(rgb)))
    if not result.hand_landmarks: raise ValueError('No hand detected. Use a clear, front-facing palm with visible fingers.')
    pts=np.array([[int(round(p.x*(w-1))),int(round(p.y*(h-1)))] for p in result.hand_landmarks[0]],dtype=np.int32)
    hull=cv2.convexHull(pts[[0,1,2,5,9,13,17]])
    region=np.zeros((h,w),np.uint8)
    cv2.fillConvexPoly(region,hull,255)
    radius=max(3,round(min(h,w)*.018))
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*radius+1,2*radius+1))
    region=cv2.erode(region,kernel)
    if np.count_nonzero(region)<400: raise ValueError('Detected palm ROI is too small. Try a larger image.')
    return region.astype(bool)

def mask_image(rgb,method,roi):
    gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    clahe=cv2.createCLAHE(clipLimit=2.,tileGridSize=(8,8)).apply(gray)
    if method=='Black-hat':
        kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15))
        score=cv2.morphologyEx(clahe,cv2.MORPH_BLACKHAT,kernel).astype(np.float32)
        pct,minsz=94,18
    else:
        score=frangi(clahe.astype(np.float32)/255.,sigmas=np.arange(1,4.6,.5),black_ridges=True).astype(np.float32)
        pct,minsz=88,15
    threshold=np.percentile(score[roi],pct)
    raw=(score>threshold)&(score>0)&roi
    return remove_small_objects(raw,min_size=minsz).astype(bool)

def overlay(rgb,mask):
    out=rgb.copy().astype(np.float32)
    out[mask]=.48*out[mask]+.52*np.array([255,50,50])
    return Image.fromarray(np.uint8(np.clip(out,0,255)))

def metrics(mask,roi):
    labels,n=label(mask)
    areas=np.bincount(labels.ravel())[1:]
    return 100*mask.sum()/roi.sum(),int(n),float(areas.mean()) if len(areas) else 0

def disturb(rgb,kind):
    rng=np.random.default_rng(42)
    if kind=='Gaussian noise':return np.uint8(np.clip(rgb.astype(np.float32)+rng.normal(0,18,rgb.shape),0,255))
    if kind=='Gaussian blur':return cv2.GaussianBlur(rgb,(7,7),1.5)
    if kind=='Low light':return np.uint8(np.clip(rgb.astype(float)*.65,0,255))
    if kind=='High light':return np.uint8(np.clip(rgb.astype(float)*1.25+10,0,255))
    if kind=='Low contrast':return np.uint8(np.clip((rgb.astype(float)-127.5)*.65+127.5,0,255))
    raise ValueError(kind)

def roi_preview(rgb,roi):
    preview=rgb.copy()
    contours,_=cv2.findContours(roi.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(preview,contours,-1,(30,230,80),2)
    preview[~roi]=(preview[~roi]*.35).astype(np.uint8)
    return Image.fromarray(preview)

def comparison_canvas(rgb,changed,base_mask,changed_mask,roi):
    def crop(arr):return np.where(roi[...,None],arr,arr//4).astype(np.uint8)
    top=np.concatenate([crop(rgb),crop(changed)],axis=1)
    bottom=np.concatenate([crop(np.asarray(overlay(rgb,base_mask))),crop(np.asarray(overlay(changed,changed_mask)))],axis=1)
    return Image.fromarray(np.concatenate([top,bottom],axis=0))

def png_bytes(im):
    buf=io.BytesIO();im.save(buf,format='PNG');return buf.getvalue()


def noise_diagnostics(rgb,roi,base):
    """Observe intermediate mask stages; do not alter published robustness metrics."""
    changed=disturb(rgb,'Gaussian noise')
    rows=[]; comparison={}
    for method in METHODS:
        gray=cv2.cvtColor(changed,cv2.COLOR_RGB2GRAY)
        clahe=cv2.createCLAHE(clipLimit=2.,tileGridSize=(8,8)).apply(gray)
        if method=='Black-hat':
            kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15))
            score=cv2.morphologyEx(clahe,cv2.MORPH_BLACKHAT,kernel).astype(np.float32)
            pct,minsz=94,18
        else:
            score=frangi(clahe.astype(np.float32)/255.,sigmas=np.arange(1,4.6,.5),black_ridges=True).astype(np.float32)
            pct,minsz=88,15
        threshold=float(np.percentile(score[roi],pct))
        positive=int(np.count_nonzero((score>0)&roi))
        raw=(score>threshold)&(score>0)&roi
        cleaned=remove_small_objects(raw,min_size=minsz).astype(bool)
        # Experimental preprocessing: median filter only on the noisy input.
        # The original baseline, ROI and published pipeline remain unchanged.
        denoised=cv2.medianBlur(changed,3)
        trial=mask_image(denoised,method,roi)
        baseline=base[method]
        inter=int(np.logical_and(baseline,trial).sum())
        union=int(np.logical_or(baseline,trial).sum())
        trial_iou=inter/union if union else 1.
        rows.append([method,round(threshold,6),positive,int(raw.sum()),int(cleaned.sum()),int(trial.sum()),round(trial_iou,4)])
        comparison[method]=comparison_canvas(rgb,denoised,baseline,trial,roi)
    columns=['Method','Threshold','Positive score pixels','Before cleanup pixels','After cleanup pixels','Median-filter trial pixels','Median-filter trial IoU']
    return pd.DataFrame(rows,columns=columns),comparison

def noise_optimization_trials(rgb,roi,base):
    """Exploratory grid; never modifies the standard robustness pipeline."""
    noisy=disturb(rgb,'Gaussian noise')
    filters={
        'None':noisy,
        'Median 3x3':cv2.medianBlur(noisy,3),
        'Gaussian 3x3':cv2.GaussianBlur(noisy,(3,3),0.8),
    }
    rows=[]
    for method in METHODS:
        baseline=base[method]
        for filter_name,filtered in filters.items():
            gray=cv2.cvtColor(filtered,cv2.COLOR_RGB2GRAY)
            clahe=cv2.createCLAHE(clipLimit=2.,tileGridSize=(8,8)).apply(gray)
            if method=='Black-hat':
                kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15))
                score=cv2.morphologyEx(clahe,cv2.MORPH_BLACKHAT,kernel).astype(np.float32)
                pct=94
            else:
                score=frangi(clahe.astype(np.float32)/255.,sigmas=np.arange(1,4.6,.5),black_ridges=True).astype(np.float32)
                pct=88
            threshold=np.percentile(score[roi],pct)
            raw=(score>threshold)&(score>0)&roi
            for min_size in (8,12,18):
                trial=remove_small_objects(raw,min_size=min_size).astype(bool)
                inter=int(np.logical_and(baseline,trial).sum())
                union=int(np.logical_or(baseline,trial).sum())
                iou=inter/union if union else 1.
                dice=2*inter/(int(baseline.sum())+int(trial.sum())) if (baseline.sum()+trial.sum()) else 1.
                rows.append([method,filter_name,min_size,int(raw.sum()),int(trial.sum()),round(iou,4),round(dice,4)])
    return pd.DataFrame(rows,columns=['Method','Filter','Min size','Before cleanup pixels','Trial pixels','IoU','Dice'])

def run_analysis(img,landmarker):
    rgb=np.array(img.convert('RGB'))
    h,w=rgb.shape[:2]
    if max(h,w)>900:
        scale=900/max(h,w)
        rgb=cv2.resize(rgb,(max(1,round(w*scale)),max(1,round(h*scale))),interpolation=cv2.INTER_AREA)
    roi=palm_roi(rgb,landmarker)
    base={m:mask_image(rgb,m,roi) for m in METHODS}
    baseline=[]
    for m in METHODS:
        cov,n,area=metrics(base[m],roi)
        baseline.append([m,round(cov,3),n,round(area,2),int(base[m].sum())])
    baseline_df=pd.DataFrame(baseline,columns=['Method','Coverage (%)','Components','Mean area (px)','Baseline pixels'])
    records=[];panels={};images={'original.png':png_bytes(Image.fromarray(rgb)),'palm_roi.png':png_bytes(roi_preview(rgb,roi))}
    for condition in CONDITIONS:
        changed=disturb(rgb,condition)
        for m in METHODS:
            cm=mask_image(changed,m,roi)
            inter=int(np.logical_and(base[m],cm).sum());union=int(np.logical_or(base[m],cm).sum())
            iou=inter/union if union else 1.
            den=int(base[m].sum()+cm.sum());dice=2*inter/den if den else 1.
            records.append([condition,m,round(iou,4),round(dice,4),int(base[m].sum()),int(cm.sum()),inter,union])
            panel=comparison_canvas(rgb,changed,base[m],cm,roi)
            panels[(condition,m)]=panel
            images[f'comparison_{condition.lower().replace(" ","_")}_{m.lower().replace("-","_")}.png']=png_bytes(panel)
    df=pd.DataFrame(records,columns=['Perturbation','Method','IoU','Dice','Baseline pixels','Changed pixels','Intersection pixels','Union pixels'])
    diagnostic_df,diagnostic_panels=noise_diagnostics(rgb,roi,base)
    optimization_df=noise_optimization_trials(rgb,roi,base)
    images['gaussian_noise_optimization_trials.csv']=optimization_df.to_csv(index=False).encode()
    images['gaussian_noise_diagnostics.csv']=diagnostic_df.to_csv(index=False).encode()
    for m,im in diagnostic_panels.items():
        images[f'noise_median_trial_{m.lower().replace("-","_")}.png']=png_bytes(im)
    images['baseline_metrics.csv']=baseline_df.to_csv(index=False).encode()
    images['robustness_metrics.csv']=df.to_csv(index=False).encode()
    images['readme.txt']=(
        'MorphoSense AI | one-image synthetic robustness study\n'
        'The same baseline palm ROI is held fixed for all changes.\n'
        'Top: original / perturbed. Bottom: baseline / perturbed overlays.\n'
        'IoU and Dice quantify self-consistency, NOT ground-truth accuracy.\n'
        'Noise: sigma=18 seed=42; blur: kernel 7 sigma=1.5; low light x0.65;\n'
        'high light x1.25+10; low contrast x0.65 about 127.5.\n'
        'The ROI is approximate; no clinical or diagnostic validation.\n'
        'Historical P2 and P3 results use different protocols.\n'
        'Noise diagnostic CSV: score-positive, thresholded, and cleaned pixel counts.\n'
        'Median-filter trial is exploratory; main IoU/Dice are unchanged.\n').encode()
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in images.items():z.writestr(name,data)
    return dict(optimization_df=optimization_df,diagnostic_df=diagnostic_df,diagnostic_panels=diagnostic_panels,rgb=Image.fromarray(rgb),roi=roi_preview(rgb,roi),base={m:overlay(rgb,base[m]) for m in METHODS},baseline=baseline_df,df=df,panels=panels,zip=buf.getvalue(),roi_pixels=int(roi.sum()))
