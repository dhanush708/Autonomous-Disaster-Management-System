# Autonomous Disaster Management System

Welcome to the Autonomous Disaster Management System. This real-time platform monitors and fuses sensor data to detect regional disasters (Landslides, Earthquakes, Cloudbursts, and Forest Fires) and coordinates a verification workflow between physical brains and dashboard clients.

## Prerequisites

* **Operating System**: Windows (recommended for the multi-terminal brain launcher)
* **Python**: Version 3.8 or higher
* **Browser**: Any modern web browser (Chrome, Edge, Firefox, or Safari)
* **Network**: A Wi-Fi router or local area network (required for mobile dashboard access)

## Install Dependencies

1. Open your terminal or Command Prompt.
2. Navigate to the project root directory.
3. Install the primary dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. (Optional) Install the mobile dashboard publisher dependencies:
   ```bash
   pip install qrcode pillow
   ```

## Project Structure

The project layout contains the following files:

```text
dm/
├── backend/
│   ├── app.py                # Flask Backend server (runs on Port 5005)
│   └── requirements.txt      # Python backend packages (flask, flask-cors, requests)
├── brains/
│   ├── landslide_brain.py    # Landslide sensor processor (UDP Port 5000)
│   ├── earthquake_brain.py   # Earthquake sensor processor (UDP Port 5001)
│   ├── cloudburst_brain.py   # Cloudburst sensor processor (UDP Port 5002)
│   └── forest_fire_brain.py  # Forest Fire sensor processor (UDP Port 5003)
├── dashboard/
│   ├── templates/
│   │   ├── admin.html        # Command Center template
│   │   └── user.html         # User warning receiver template
│   └── static/
│       ├── style.css         # Styling system
│       └── app.js            # Admin interface polling/charts controller
├── run_all_brains.py         # Simultaneous Windows terminal launcher for brains
├── publish_dashboard.py      # Local IP detector and QR Code publisher
└── HOW_TO_RUN.md             # This instruction manual
```

## Starting The Backend

The Flask server hosts the core API routes, user registration data, and current sensor status arrays.

1. Open a Command Prompt window.
2. Navigate to the project root directory.
3. Run the following command:
   ```bash
   python backend/app.py
   ```
4. The server will start on `http://localhost:5005`. Keep this terminal window open.

## Starting All Disaster Brains

Each brain daemon listens for incoming UDP packets sent from sensor nodes, calculates threat confidence, and handles states.

1. Open a separate Command Prompt window.
2. Navigate to the project root directory.
3. Run the launcher script:
   ```bash
   python run_all_brains.py
   ```
4. This command will spawn four separate Command Prompt windows running:
   * Landslide Monitor
   * Earthquake Monitor
   * Cloudburst Monitor
   * Forest Fire Monitor

Keep these terminal windows running in the background.

## Opening The Admin Dashboard

1. Open your web browser.
2. Enter the following URL:
   `http://localhost:5005/admin` (or simply `http://localhost:5005`)

This dashboard gives you a view of live sensor health, raw values, confidence trends, active maps, and the manual action panels.

## Opening The User Dashboard

1. Open your web browser.
2. Enter the following URL:
   `http://localhost:5005/user`

This dashboard prompts the user to select their zone (Zone 1: Landslide, Zone 2: Forest Fire, Zone 3: Cloudburst, Zone 4: Earthquake) and displays safety alerts, threat details, and evacuation procedures.

## Mobile Access

To view the User Dashboard on a mobile phone:

1. Connect both the hosting laptop and the phone to the **same Wi-Fi network**.
2. Find the laptop's local IP address:
   * **On Windows**: Open Command Prompt, run `ipconfig`, and look for the "IPv4 Address" under your active Wi-Fi adapter (e.g., `192.168.1.100`).
   * **On macOS/Linux**: Open Terminal, run `ifconfig` or `ip a`, and locate your network interface IP address.
3. On your mobile phone, open the web browser and navigate to:
   `http://<YOUR_IP>:5005/user` (e.g., `http://192.168.1.100:5005/user`)

### Automated Mobile Access (Recommended)

Alternatively, you can run the publisher tool:
```bash
python publish_dashboard.py
```
This script automatically scans your laptop's interface, builds the correct URL, saves a `dashboard_qr.png` file, and displays a scannable QR Code directly in your terminal window. Scan this QR Code with your phone's camera to open the dashboard.

## Verification Workflow

When a sensor starts registering threat data (e.g., smoke levels rising):
1. The brain evaluates the threat and increments confidence (`SAFE` $\rightarrow$ `SUSPICIOUS` $\rightarrow$ `WARNING`).
2. Once confidence reaches 70%, the system enters the `VERIFYING` state.
3. On the Admin Dashboard, the affected disaster card shows **Confirm**, **False Positive**, and **Reset** buttons.
4. On the User Dashboard, the user's screen changes to yellow, showing "Possible Disaster Detected - Verification in progress".
5. The admin has three options:
   * **Confirm**: Marks the alert as confirmed. The system shifts to `CONFIRMED` (RED ALERT) state, and the user dashboard displays evacuation instructions.
   * **False Positive**: Dismisses the alarm. The user dashboard shows "False Alarm".
   * **Reset**: Clears the threat buffers, sets confidence to 0%, and resets both dashboards to `SAFE`.

## Troubleshooting

* **Issue**: Phone cannot connect to the dashboard URL.
  * *Solution 1*: Check that the phone and laptop are on the same Wi-Fi router.
  * *Solution 2*: Windows Defender Firewall may block port 5005. Allow `python.exe` through the firewall or create an inbound port rule in Windows Firewall Settings for TCP port 5005.
* **Issue**: `ImportError: No module named 'qrcode'`.
  * *Solution*: Run `pip install qrcode pillow` in your terminal to install the necessary image generator dependencies.
* **Issue**: The terminal prints "Backend not running".
  * *Solution*: You must start `python backend/app.py` before launching the brains or the mobile publisher.
* **Issue**: Brain files exit with a socket error.
  * *Solution*: Another application is using the UDP ports (5000-5003). Ensure no duplicate instances of the brain scripts are running.

## Shutdown Procedure

1. Close the four Command Prompt windows running the individual brains.
2. In the Flask backend window, press `Ctrl + C` to stop the server.
3. Close the terminal windows.
