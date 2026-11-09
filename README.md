# π RuView Mobile 📡

WiFi Spatial Intelligence & Biometric Monitoring Android App.  
Inspired by the open-source **[π RuView](https://github.com/ruvnet/RuView)** project.

---

## 🌟 Features
- 🔄 **Real-Time 2D Spatial Radar:** Concentric distance rings, rotating radar beam, and target blips showing detected human presence through walls.
- 🫀 **Vital Signs & Biometrics:**
  - Real-time Heart Rate (BPM) + animated ECG waveform.
  - Respiration Rate (RPM) + sinusoidal breathing wave.
- 🟢 **Integrated Simulation Mode:** Test all radar and biometric graphics instantly on your phone without requiring an active ESP32 sensor.
- ⚙️ **Network / ESP32 Configuration:** Connect directly to your local RuView node or Home Assistant bridge via IP/WebSocket.

---

## 🛠️ Build APK via GitHub Actions
1. Push this repository to GitHub.
2. Go to the **Actions** tab.
3. The build will run using the official Kivy Buildozer environment.
4. Download the compiled `.apk` directly from **Artifacts** (`ruview-android-apk`).
