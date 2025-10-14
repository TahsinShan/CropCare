import os
import sys
import json
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename


ESP32_BASE_URL = "http://192.168.1.158"  # Or use your ESP32's IP



import requests

def get_soil_moisture():
    try:
        response = requests.get(f"{ESP32_BASE_URL}/moisture", timeout=5)
        data = response.json()
        raw = int(data["raw"])  # get raw ADC value
        
        # Convert raw ADC to percentage here
        dry_value = 4095
        wet_value = 2000
        
        # Clamp raw value
        raw = max(min(raw, dry_value), wet_value)
        
        moisture_percent = 100.0 * (dry_value - raw) / (dry_value - wet_value)
        moisture_percent = max(0, min(moisture_percent, 100))  # safety clamp
        
        return moisture_percent

    except Exception as e:
        print(f"Error getting soil moisture: {e}")
        return None


def start_watering():
    try:
        response = requests.post(f"{ESP32_BASE_URL}/start_pump", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Error starting watering: {e}")
        return False

# Moisture levels per condition
ideal_moisture_levels = {
    "Tomato_healthy": 75,
    "Tomato_Early_blight": 50,
    "Tomato_Late_blight": 55,
    "Tomato_Leaf_Mold": 60,
    "Tomato_Septoria_leaf_spot": 55,
    "Tomato_Spider_mites_Two_spotted_spider_mite": 50,
    "Tomato__Target_Spot": 55,
    "Tomato__Tomato_YellowLeaf__Curl_Virus": 45,
    "Tomato__Tomato_mosaic_virus": 50,
    "Tomato_Bacterial_spot": 50,
    "Potato___healthy": 70,
    "Potato___Early_blight": 55,
    "Potato___Late_blight": 60,
    "Pepper__bell___healthy": 70,
    "Pepper__bell___Bacterial_spot": 55,
    "PlantVillage": 65  
}


remedies = {
    "Tomato_healthy": "Your plant is healthy. Maintain regular watering and monitor for early signs of disease.",
    "Tomato_Early_blight": "Remove affected leaves. Use fungicides containing chlorothalonil or copper. Rotate crops yearly.",
    "Tomato_Late_blight": "Remove and destroy infected plants. Apply copper-based fungicides. Avoid overhead watering.",
    "Tomato_Leaf_Mold": "Improve air circulation. Use fungicides like mancozeb. Remove infected leaves.",
    "Tomato_Septoria_leaf_spot": "Remove lower leaves. Use fungicides like chlorothalonil. Avoid wetting leaves.",
    "Tomato_Spider_mites_Two_spotted_spider_mite": "Spray with insecticidal soap or neem oil. Increase humidity around plants.",
    "Tomato__Target_Spot": "Use preventive fungicides. Remove infected leaves. Practice crop rotation.",
    "Tomato__Tomato_YellowLeaf__Curl_Virus": "Control whiteflies. Remove infected plants. Use resistant varieties.",
    "Tomato__Tomato_mosaic_virus": "Remove infected plants. Disinfect tools. Avoid smoking near plants.",
    "Tomato_Bacterial_spot": "Apply copper-based bactericides. Remove infected plants. Avoid overhead irrigation.",
    "Potato___healthy": "Plant is healthy. Maintain consistent care and regular checks for disease.",
    "Potato___Early_blight": "Use fungicides like chlorothalonil. Rotate crops. Remove infected debris.",
    "Potato___Late_blight": "Apply copper-based fungicides. Destroy infected plants. Ensure good drainage.",
    "Pepper__bell___healthy": "Keep soil well-drained. Monitor for signs of pest or disease. Water consistently.",
    "Pepper__bell___Bacterial_spot": "Use copper-based bactericides. Remove infected leaves. Avoid wet foliage.",
    "PlantVillage": "General advice: Maintain good hygiene, proper spacing, and monitor moisture regularly."
}





# AI imports
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np

# Force UTF-8 encoding for Windows console
#sys.stdout.reconfigure(encoding='utf-8')
#sys.stderr.reconfigure(encoding='utf-8')

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change in production
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Upload folder
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database setup
def init_db():
    conn = sqlite3.connect("plantguardian.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date TEXT,
                    disease TEXT,
                    severity TEXT,
                    remedy TEXT,
                    humidity TEXT,
                    photo TEXT)""")
    conn.commit()
    conn.close()

init_db()

# User class
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect("plantguardian.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return User(row[0], row[1], row[2])
    return None

# Load model and labels
MODEL_PATH = "plant_disease_model.h5"
LABELS_PATH = "labels.json"

model = None
labels = []

try:
    model = load_model(MODEL_PATH)
    print("AI Model loaded successfully!")
except Exception as e:
    print(f"Warning: Could not load AI model! {e}")

try:
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        labels = json.load(f)
    print(f"Loaded {len(labels)} labels from {LABELS_PATH}")
except Exception as e:
    print(f"Warning: Could not load labels.json! {e}")



# Prediction function
def predict_plant_health(img_path):
    if not model or not labels:
        print("Model or labels not loaded.")
        return "Unknown", "Model not loaded", 0.0

    img = Image.open(img_path).convert('RGB')
    img = img.resize((224, 224))
    x = np.array(img) / 255.0
    x = np.expand_dims(x, axis=0)

    preds = model.predict(x)
    idx = np.argmax(preds)
    disease = labels[idx]
    confidence = float(preds[0][idx])
    severity = "Mild" if confidence < 0.7 else "Severe"

    # 🔍 ADD THIS:
    print(f"[Prediction] Disease: {disease}, Confidence: {confidence:.4f}, Severity: {severity}")

    return disease, severity, confidence




# ------------------- ROUTES -------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        try:
            conn = sqlite3.connect("plantguardian.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists!", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("plantguardian.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()
        if row and bcrypt.check_password_hash(row[2], password):
            user = User(row[0], row[1], row[2])
            login_user(user)
            return redirect(url_for("upload"))
        flash("Invalid credentials!", "danger")
    return render_template("login.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/dashboard")
@login_required
def dashboard():
    conn = sqlite3.connect("plantguardian.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM history WHERE user_id=? ORDER BY date DESC", (current_user.id,))
    records = c.fetchall()
    conn.close()

    dates = [r["date"] for r in records]
    results_numeric = [1 if "healthy" in r["disease"].lower() else 0 for r in records]
    colors = ["#4caf50" if val==1 else "#f44336" for val in results_numeric]

    # 🧠 Add this block:
    healthy = sum(1 for r in records if "healthy" in r["disease"].lower())
    diseased = sum(1 for r in records if "healthy" not in r["disease"].lower())
    result_counts = [healthy, diseased]

    return render_template(
        "dashboard.html",
        history=records,
        dates=dates,
        results_numeric=results_numeric,
        colors=colors,
        result_counts=result_counts  # ✅ Now it's passed to the template
    )

@app.route("/techniques")
@login_required
def techniques():
    return render_template("techniques.html")



@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "GET":
        return render_template("upload.html")

    # POST logic stays the same
    if 'plant_image' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for("upload"))

    file = request.files['plant_image']
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for("upload"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        disease, severity, confidence = predict_plant_health(save_path)
        remedy = remedies.get(disease, "No specific remedy available.")
        humidity = ""

        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect("plantguardian.db")
        c = conn.cursor()
        c.execute("""INSERT INTO history (user_id, date, disease, severity, remedy, humidity, photo)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (current_user.id, date, disease, severity, remedy, humidity, filename))
        record_id = c.lastrowid
        conn.commit()
        conn.close()

        return redirect(url_for("report", record_id=record_id))

    flash("Invalid file type! Only images allowed.", "danger")
    return redirect(url_for("upload"))


@app.route("/report/<int:record_id>", methods=["GET", "POST"])
@login_required
def report(record_id):
    conn = sqlite3.connect("plantguardian.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM history WHERE id=? AND user_id=?", (record_id, current_user.id))
    record = c.fetchone()
    conn.close()
    
    if not record:
        flash("Report not found!", "danger")
        return redirect(url_for("dashboard"))

    # Fetch current moisture
    current_moisture = get_soil_moisture()

    # Get ideal required moisture based on disease
    disease_label = record["disease"]
    required_moisture = ideal_moisture_levels.get(disease_label, 65)

    # Handle watering request
    if request.method == "POST" and "water_now" in request.form:
        success = start_watering()
        if success:
            flash("Pump started successfully!", "success")
        else:
            flash("Failed to start watering!", "danger")
        return redirect(url_for("report", record_id=record_id))

    return render_template("report.html", 
                           report=record, 
                           current_moisture=current_moisture,
                           required_moisture=required_moisture)






from flask import abort

@app.route("/plantcare")
@login_required
def plantcare():
    condition_pages = [
  "Pepper__bell___Bacterial_spot",
  "Pepper__bell___healthy",
  "PlantVillage",
  "Potato___Early_blight",
  "Potato___Late_blight",
  "Potato___healthy",
  "Tomato_Bacterial_spot",
  "Tomato_Early_blight",
  "Tomato_Late_blight",
  "Tomato_Leaf_Mold",
  "Tomato_Septoria_leaf_spot",
  "Tomato_Spider_mites_Two_spotted_spider_mite",
  "Tomato__Target_Spot",
  "Tomato__Tomato_YellowLeaf__Curl_Virus",
  "Tomato__Tomato_mosaic_virus",
  "Tomato_healthy"
]
    return render_template("plantcare.html", conditions=condition_pages)

@app.route("/plantinfo/<condition_name>")
@login_required
def plant_info(condition_name):
    try:
        return render_template(f"plantinfo/{condition_name}.html")
    except:
        flash("Plant condition page not found!", "danger")
        return redirect(url_for("plantcare"))




        





 
@app.route("/history")
@login_required
def history():
    conn = sqlite3.connect("plantguardian.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM history WHERE user_id=? ORDER BY date DESC", (current_user.id,))
    records = c.fetchall()
    conn.close()

    healthy = sum(1 for r in records if "healthy" in r["disease"].lower())
    diseased = sum(1 for r in records if "healthy" not in r["disease"].lower())
    result_counts = [healthy, diseased]

    return render_template("history.html", history=records, result_counts=result_counts)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    # Render sets the PORT environment variable automatically
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 for local
    app.run(
        debug=os.environ.get("FLASK_ENV") != "production",  # Debug if not in production
        host="0.0.0.0",
        port=port
    )

