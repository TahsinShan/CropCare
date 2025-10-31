# CropCare

CropCare is an intelligent plant health monitoring and irrigation management system built with Flask, TensorFlow, and ESP32 IoT integration.  
It enables users to detect crop diseases from images using AI, monitor real-time soil moisture, and control irrigation systems automatically or manually through a web interface.

---

## Overview

CropCare combines deep learning for plant disease detection with Internet of Things (IoT) capabilities to help farmers and agricultural researchers maintain healthy crops efficiently.  
Users can upload images of plant leaves for diagnosis, receive treatment recommendations, and manage watering operations through the platform.

---

## Key Features

### AI-Based Disease Detection
- Upload a plant leaf image to detect diseases using a trained TensorFlow CNN model.
- Identifies multiple conditions in tomato, potato, and bell pepper plants.
- Displays predicted disease, confidence score, and severity level.

### IoT-Enabled Smart Irrigation
- Communicates with an ESP32 microcontroller to retrieve real-time soil moisture data.
- Compares actual and ideal soil moisture based on plant condition.
- Allows manual or automatic activation of a water pump directly from the web interface.

### User Account Management
- Secure registration and login using Flask-Login and bcrypt.
- Each user maintains a private history of tests and reports.

### Analytical Dashboard
- Interactive charts display health trends over time.
- Tracks ratios of healthy to diseased plants.
- Visual representation of user history for better decision-making.

### Plant Care Knowledge Base
- Comprehensive library of diseases and recommended remedies.
- Individual plant condition pages with prevention and treatment guidance.

---

## Technology Stack

| Component        | Technology Used               |
|------------------|-------------------------------|
| Backend Framework | Flask (Python)                |
| Frontend          | HTML, CSS, Bootstrap, JavaScript |
| Database          | SQLite                        |
| Authentication    | Flask-Login, bcrypt            |
| AI Model          | TensorFlow / Keras (.h5 model) |
| IoT Integration   | ESP32 microcontroller via REST API |
| Image Processing  | Pillow (PIL), NumPy            |

---

## Project Structure

CropCare/
│
├── app.py                      # Main Flask application
├── cropcare.db                 # SQLite database (auto-created)
├── plant_disease_model.h5      # Trained TensorFlow model
├── labels.json                 # Class label definitions
│
├── static/
│   ├── uploads/                # Uploaded images
│   ├── css/                    # Stylesheets
│   ├── js/                     # JavaScript files
│   └── images/                 # Static assets
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── upload.html
│   ├── dashboard.html
│   ├── report.html
│   ├── history.html
│   ├── about.html
│   ├── plantcare.html
│   └── plantinfo/              # Disease-specific information pages
│
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
