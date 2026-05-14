# 🎨 Cartoonizing Images Using Genetic Algorithms

Bachelor's thesis project — a web app that transforms portrait photos into anime-style cartoons using deep learning, genetic algorithm optimization, and facial landmark detection.

**GUC Media Engineering & Technology Faculty — Supervised by Dr. Islam ElMaddah — May 2025**

---

## 🧠 How It Works

1. **Pre-processing** — Image is resized to 512×512, bilateral filtered, and contrast-enhanced via CLAHE
2. **Cartoonization** — AnimeGANv2 (face_paint_512_v2) applies anime-style stylization
3. **Post-processing** — Bilateral filter, unsharp mask, saturation and contrast adjustment
4. **GA Optimization** — Genetic algorithm (PyGAD) evolves saturation, contrast, and sharpness parameters over ~40 generations, maximizing SSIM score
5. **Facial Exaggeration** — MediaPipe Face Mesh detects 468 landmarks to locally warp eyes, jaw, nose, and ears for expressive cartoon effects

---

## 📈 Results

- Average SSIM score of **0.78** across test images
- GA optimization improved SSIM by **~0.15** over baseline AnimeGANv2 alone
- Processing time: **1.3s** (GPU) / **4.2s** (CPU) per image
- Facial exaggeration used in **72%** of user sessions

---

## 🛠 Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat&logo=pytorch&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat&logo=opencv&logoColor=white)

---

## 🏗 Project Structure

    backend/
    ├── app.py              # Flask REST API
    ├── cartoonize.py       # Core pipeline: GAN + GA + post-processing
    └── requirements.txt
    frontend/
    ├── src/
    │   ├── App.js          # Main React component with sliders
    │   └── components/
    └── public/

---

## ▶️ How to Run

**Backend**
```
cd backend
pip install -r requirements.txt
python app.py
```

**Frontend**
```
cd frontend
npm install
npm start
```

---

## 🔬 Key Technologies

| Component | Technology |
|-----------|-----------|
| Stylization model | AnimeGANv2 (face_paint_512_v2) |
| Optimization | PyGAD — Genetic Algorithm |
| Facial landmarks | MediaPipe Face Mesh (468 points) |
| Quality metric | SSIM (Structural Similarity Index) |
| Backend | Flask + PyTorch |
| Frontend | React + Axios |
