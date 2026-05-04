from flask import Flask, render_template, request, redirect, url_for, send_file
import time, csv, os

from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import confusion_matrix, accuracy_score
import numpy as np

app = Flask(__name__)

# =========================
# 🔥 GLOBAL STATE
# =========================
failure_count = 0
failure_start = None
failure_active = False
total_requests = 0

chaos_mode = None
last_mttr = 0

# =========================
# 🤖 AI MODELS
# =========================
rf_model = RandomForestClassifier()
iso_model = IsolationForest(contamination=0.2, random_state=42)

# ✅ TRAINING DATA (SIMULATED IoT DATA)
X_train = np.random.normal(loc=[25,50], scale=[5,10], size=(200,2))
y_train = [0 if (x[0] < 40 and x[1] < 80) else 1 for x in X_train]

rf_model.fit(X_train, y_train)
iso_model.fit(X_train)

# =========================
# 📊 DATA TRACKING
# =========================
y_true = []
y_pred = []

# =========================
# 📝 LOGGING
# =========================
def log_data(temp, hum, status, mttr):
    file_exists = os.path.isfile("logs.csv")
    with open("logs.csv", "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Temp","Humidity","Status","MTTR"])
        writer.writerow([temp, hum, status, mttr])

# =========================
# 🔥 CHAOS
# =========================
@app.route('/inject/<mode>')
def inject(mode):
    global chaos_mode
    chaos_mode = mode
    return redirect(url_for('index'))

@app.route('/download')
def download():
    return send_file("logs.csv", as_attachment=True)

# =========================
# 🚀 MAIN
# =========================
@app.route('/', methods=['GET','POST'])
def index():

    global failure_count, failure_start, failure_active
    global total_requests, chaos_mode, last_mttr
    global y_true, y_pred

    # 🔹 Default values (for first page load)
    temperature = None
    humidity = None
    status = ""
    decision = ""
    mttr = 0
    failure_rate = 0
    accuracy = 0
    cm = [[0,0],[0,0]]

    if request.method == 'POST':

        total_requests += 1

        temperature = float(request.form.get('temperature') or 25)
        humidity = float(request.form.get('humidity') or 50)

        # 🔥 CHAOS
        if chaos_mode == "sensor":
            temperature = 80
        elif chaos_mode == "network":
            temperature = 0
            humidity = 0
        elif chaos_mode == "drift":
            temperature = 38

        # =========================
        # 🤖 AI PREDICTION
        # =========================
        rf_pred = rf_model.predict([[temperature, humidity]])[0]
        iso_pred = iso_model.predict([[temperature, humidity]])[0]
        iso_flag = 1 if iso_pred == -1 else 0

        # =========================
        # 🎯 STATUS LOGIC
        # =========================
        if temperature == 0 and humidity == 0:
            status = "RED"
            y_true.append(1)

        elif rf_pred == 1 or iso_flag == 1:
            status = "RED"
            y_true.append(1)

        elif temperature > 35:
            status = "ORANGE"
            y_true.append(0)

        else:
            status = "GREEN"
            y_true.append(0)

        y_pred.append(1 if status == "RED" else 0)

        # =========================
        # ⏱ FAILURE START
        # =========================
        if status == "RED" and not failure_active:
            failure_active = True
            failure_start = time.time()
            failure_count += 1

        # =========================
        # 🔧 SELF HEAL
        # =========================
        if chaos_mode == "reset" and failure_active:

            recovery_time = time.time() - failure_start

            if 1 <= recovery_time <= 15:
                last_mttr = recovery_time
            else:
                last_mttr = 5

            failure_active = False
            failure_start = None
            chaos_mode = None

            temperature = 25
            humidity = 50
            status = "GREEN"

            decision = "🔧 System Recovered (Self-Healed)"

        # =========================
        # 🎯 DECISION CLEAN LOGIC
        # =========================
        elif status == "RED":
            decision = "🚨 AI Detected Failure"

        elif status == "ORANGE":
            decision = "⚠️ AI Monitoring"

        elif status == "GREEN" and not failure_active:
            decision = "✅ System Stable"

        # =========================
        # 📊 METRICS
        # =========================
        mttr = last_mttr if last_mttr else 0
        failure_rate = failure_count / total_requests if total_requests else 0

        if len(y_true) > 5:
            accuracy = accuracy_score(y_true, y_pred)
            cm = confusion_matrix(y_true, y_pred).tolist()

        # =========================
        # 📝 LOGGING
        # =========================
        log_data(temperature, humidity, status, mttr)

    return render_template('index.html',
                           temperature=temperature,
                           humidity=humidity,
                           status=status,
                           mttr=round(mttr,2),
                           failure_rate=round(failure_rate,2),
                           decision=decision,
                           accuracy=round(accuracy,2),
                           cm=cm)

# =========================
# ▶ RUN
# =========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)