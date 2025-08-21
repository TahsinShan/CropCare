import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename

# AI imports
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change in real project
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Upload folder setup
UPLOAD_FOLDER = os.path.join('static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed image extensions
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

# User loader
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

# Load pretrained AI model
MODEL_PATH = "plant_disease_model.h5"
model = None
try:
    model = load_model(MODEL_PATH)
    print("AI Model loaded successfully!")
except Exception as e:
    print(f"Warning: AI Model could not be loaded! {e}")

# Labels (adjust based on your model)
labels = [
    "Apple Scab",
    "Apple Black Rot",
    "Apple Healthy",
    "Corn Gray Leaf Spot",
    "Corn Common Rust",
    "Tomato Early Blight",
    "Tomato Late Blight",
    "Tomato Healthy"
]

# Remedies for diseases
remedies = {
    "Apple Scab": "Remove infected leaves. Use fungicides like Captan. Improve air circulation.",
    "Apple Black Rot": "Prune affected branches. Apply copper-based fungicide.",
    "Apple Healthy": "No issues detected. Maintain regular watering and sunlight.",
    "Corn Gray Leaf Spot": "Rotate crops. Apply fungicide if severe.",
    "Corn Common Rust": "Plant resistant varieties. Use fungicide if needed.",
    "Tomato Early Blight": "Remove infected leaves. Apply chlorothalonil-based fungicide.",
    "Tomato Late Blight": "Destroy infected plants. Apply fungicides containing mancozeb.",
    "Tomato Healthy": "No disease detected. Keep soil moist and ensure good airflow."
}

# Prediction function
def predict_plant_health(img_path):
    if not model:
        return "Unknown", "Model not loaded", 0.0
    img = Image.open(img_path).convert('RGB')
    img = img.resize((224, 224))  # adjust to your model input size
    x = np.array(img) / 255.0
    x = np.expand_dims(x, axis=0)
    preds = model.predict(x)
    idx = np.argmax(preds)
    disease = labels[idx]
    confidence = preds[0][idx]
    severity = "Mild" if confidence < 0.7 else "Severe"
    return disease, severity, confidence

# Routes
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
        except:
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
            return redirect(url_for("dashboard"))
        else:
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

    # Prepare data for chart
    dates = [r["date"] for r in records]
    results = [r["disease"] for r in records]  # using disease column

    # Convert results into numeric form for chart (Healthy=1, Diseased=0)
    results_numeric = [1 if "healthy" in r.lower() else 0 for r in results]
    colors = ["#4caf50" if "healthy" in r.lower() else "#f44336" for r in results]

    return render_template(
        "dashboard.html",
        history=records,
        dates=dates,
        results_numeric=results_numeric,
        colors=colors
    )


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    if 'plant_image' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for("dashboard"))

    file = request.files['plant_image']

    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for("dashboard"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        # Predict using AI model
        disease, severity, confidence = predict_plant_health(save_path)
        remedy = remedies.get(disease, "No remedy available.")
        humidity = ""  # placeholder for sensor data

        # Save to database
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
    else:
        flash("Invalid file type! Only images allowed.", "danger")
        return redirect(url_for("dashboard"))

@app.route("/report/<int:record_id>")
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
    return render_template("report.html", report=record)

@app.route("/history")
@login_required
def history():
    conn = sqlite3.connect("plantguardian.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM history WHERE user_id=? ORDER BY date DESC", (current_user.id,))
    records = c.fetchall()
    conn.close()

    # Count Healthy vs Diseased
    healthy = sum(1 for r in records if "healthy" in r["disease"].lower())
    diseased = sum(1 for r in records if "healthy" not in r["disease"].lower())
    result_counts = [healthy, diseased]

    return render_template(
        "history.html",
        history=records,
        result_counts=result_counts
    )



@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
