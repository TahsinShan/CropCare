# 🌿 CropCare — Smart Plant Disease Detection & IoT Watering System

**CropCare** is a Flask-powered web application that uses AI-based image classification and IoT integration to monitor plant health, detect diseases, and automatically manage watering via an ESP32 microcontroller.  

The system combines **machine learning**, **computer vision**, and **IoT** to help farmers and plant enthusiasts maintain healthy crops efficiently.

---

## 🚀 Features

### 🌾 AI Plant Disease Detection
- Upload a plant leaf image to identify diseases using a deep learning model (`plant_disease_model.h5`).
- Confidence score and severity level shown for each prediction.
- Displays the correct **remedy** and **ideal soil moisture** for the diagnosed condition.

### 💧 IoT Soil Monitoring & Auto-Watering
- Real-time soil moisture reading from ESP32 sensor via REST API (`/moisture`).
- Calculates moisture percentage based on calibrated ADC values.
- Allows users to trigger watering directly from the web dashboard via ESP32 endpoint (`/start_pump`).

### 👩‍🌾 User Features
- Secure **user registration and login** (passwords hashed with Flask-Bcrypt).
- Upload and analyze multiple plant images.
- View **diagnosis history**, including date, disease, severity, and remedy.
- Visual analytics for healthy vs. diseased crops.
- Access detailed plant care guides for each condition.

### 🧠 AI Model Integration
- TensorFlow-based CNN model trained on PlantVillage dataset.
- Labels and mappings loaded dynamically from `labels.json`.
- Automatic preprocessing and resizing before prediction.

---

## 🗂️ Project Structure

```
CropCare/
│
├── app.py                        # Main Flask application
├── plant_disease_model.h5        # Trained AI model
├── labels.json                   # Label mappings for model predictions
├── plantguardian.db              # SQLite database (auto-created)
│
├── static/
│   ├── uploads/                  # Uploaded plant images
│   └── css/, js/, img/           # Static assets
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── upload.html
│   ├── dashboard.html
│   ├── history.html
│   ├── report.html
│   ├── about.html
│   ├── plantcare.html
│   └── plantinfo/                # Info pages for each plant condition
│
└── README.md
```

---

## ⚙️ Setup Instructions

### 1️⃣ Prerequisites
- Python 3.8+
- pip (Python package manager)
- ESP32 device with soil moisture sensor and pump relay module

---

### 2️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/CropCare.git
cd CropCare
```

---

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

If you don’t have a `requirements.txt`, you can use:
```bash
pip install flask flask-bcrypt flask-login tensorflow pillow requests
```

---

### 4️⃣ Configure ESP32
Ensure your ESP32 is running a firmware that serves:
- `GET /moisture` → returns JSON like `{"raw": 2500}`
- `POST /start_pump` → activates the water pump

Then, edit your ESP32 IP in `app.py`:
```python
ESP32_BASE_URL = "http://192.168.x.xxx"
```

---

### 5️⃣ Run the App
```bash
python app.py
```
Then open your browser and visit:
```
http://localhost:5000
```

---

## 📸 How It Works

1. **Login / Register** to your CropCare account.  
2. **Upload a leaf photo** in the “Upload” page.  
3. The AI model predicts the disease and shows:
   - Disease name  
   - Severity level  
   - Suggested remedy  
4. CropCare fetches **current soil moisture** and compares it to the **ideal moisture** for the detected condition.  
5. You can **start watering** directly through the “Report” page.  
6. All analyses are stored in your personal **history**.

---

## 🧩 Database Schema

**Table: users**
| id | username | password |
|----|-----------|----------|

**Table: history**
| id | user_id | date | disease | severity | remedy | humidity | photo |

---

## 🌿 Supported Plants & Diseases

CropCare supports detection of diseases for:
- **Tomato**
- **Potato**
- **Bell Pepper**

Each has multiple conditions including:
- Early Blight  
- Late Blight  
- Bacterial Spot  
- Leaf Mold  
- Septoria Leaf Spot  
- Target Spot  
- Spider Mites  
- Yellow Leaf Curl Virus  
- Mosaic Virus  
- Healthy States  

---

## 🧠 AI Model Details

- Framework: **TensorFlow / Keras**
- Input size: 224×224 RGB
- Output: 15+ plant disease classes
- Dataset: **PlantVillage** (augmented and cleaned)
- Activation: Softmax
- Output: Disease label with confidence %

---

## 🔐 Security Features
- Hashed passwords (Bcrypt)
- Session-based authentication (Flask-Login)
- Route protection via `@login_required`
- Sanitized uploads via `secure_filename`

---

## 🌐 Future Enhancements
- Live camera capture via ESP32-CAM  
- Email/SMS notifications for low soil moisture  
- Admin dashboard for analytics  
- Cloud database integration (Firebase / PostgreSQL)

---

## 👨‍💻 Author

**Developed by:** [Tahsin Hasan Shan](https://github.com/tahsinshan)  
🎓 Founder & General Secretary, SCPSC IT Club  
💡 Passionate about AI, IoT, and Sustainable Tech

---

## 🪴 License
This project is released under the **MIT License** — feel free to use, modify, and expand.

---

## 🖼️ Preview
**Dashboard View**
> AI Predictions, Graphs, and Moisture Insights — all in one place!

**Upload Page**
> Upload your plant photo and instantly get diagnosis results with remedies.

---

✨ *CropCare — where AI meets nature for smarter farming.*
