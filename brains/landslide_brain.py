import socket
import json
import time
import msvcrt
import requests
from collections import deque
from statistics import mean

# ==================================================
# CONFIG
# ==================================================

HOST = "0.0.0.0"
PORT = 5000

BACKEND_URL = "http://localhost:5005"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print("\nLANDSLIDE BRAIN V3 STARTED...\n")

# ==================================================
# MEMORY
# ==================================================

tilt_history = deque(maxlen=20)
vibration_history = deque(maxlen=20)

confidence = 0.0
current_state = "SAFE"

verification_mode = False
verification_result = None

# ==================================================
# SCORING
# ==================================================

def tilt_score(tilt):

    if tilt < 2:
        return 0
    elif tilt < 5:
        return 20
    elif tilt < 10:
        return 40
    elif tilt < 15:
        return 75
    elif tilt < 20:
        return 90
    else:
        return 100


def vibration_score(vib):

    if vib < 0.1:
        return 0
    elif vib < 0.3:
        return 10
    elif vib < 0.6:
        return 20
    elif vib < 1.0:
        return 40
    else:
        return 60


# ==================================================
# KEYBOARD CHECK
# ==================================================

def check_keyboard():

    global verification_result

    if msvcrt.kbhit():

        try:

            key = msvcrt.getch().decode("utf-8").upper()

            if key == "C":
                verification_result = "CONFIRMED"

            elif key == "F":
                verification_result = "FALSE_POSITIVE"

        except:
            pass


# ==================================================
# BACKEND CHECK
# Brain polls backend for admin actions.
# Admin dashboard click → backend stores intent →
# Brain reads here → Brain changes its own state.
# Flask never changes state/confidence/verification_result.
# ==================================================

def check_backend():

    global verification_result
    global verification_mode
    global confidence
    global current_state
    global avg_tilt
    global avg_vibration

    try:

        r = requests.get(
            f"{BACKEND_URL}/api/pending/landslide",
            timeout=0.3
        )

        action = r.json().get("action")

        if action == "CONFIRM" and verification_mode:
            verification_result = "CONFIRMED"

        elif action == "FALSE_POSITIVE" and verification_mode:
            verification_result = "FALSE_POSITIVE"

        elif action == "RESET":
            confidence = 0
            tilt_history.clear()
            vibration_history.clear()
            verification_mode = False
            verification_result = None
            avg_tilt = 0
            avg_vibration = 0
            current_state = "SAFE"

    except:
        pass


# ==================================================
# MAIN LOOP
# ==================================================

while True:

    data, addr = sock.recvfrom(4096)

    packet = json.loads(data.decode())

    pitch = float(packet["pitch"])
    roll = float(packet["roll"])
    tilt = float(packet["tilt"])
    vibration = float(packet["vibration"])

    # ------------------------------------------
    # HISTORY
    # ------------------------------------------

    tilt_history.append(tilt)
    vibration_history.append(vibration)

    avg_tilt = mean(tilt_history)
    avg_vibration = mean(vibration_history)

    # ------------------------------------------
    # CONFIDENCE
    # ------------------------------------------

    t_score = tilt_score(avg_tilt)
    v_score = vibration_score(avg_vibration)

    raw_confidence = (
        0.8 * t_score +
        0.6 * v_score
    )

    if raw_confidence > 100:
        raw_confidence = 100

    if raw_confidence > confidence:

        confidence = (
            0.5 * confidence +
            0.5 * raw_confidence
        )

    else:

        confidence = max(
            0,
            confidence - 1
        )

    if confidence > 100:
        confidence = 100

    # ------------------------------------------
    # ENTER VERIFYING
    # ------------------------------------------

    if confidence >= 70 and not verification_mode:

        verification_mode = True
        current_state = "VERIFYING"

    # ------------------------------------------
    # KEYBOARD + BACKEND CHECK
    # ------------------------------------------

    check_backend()

    if verification_mode:
        check_keyboard()

    # ------------------------------------------
    # VERIFICATION RESULTS
    # ------------------------------------------

    if verification_result == "CONFIRMED":

        current_state = "CONFIRMED"

    elif verification_result == "FALSE_POSITIVE":

        current_state = "FALSE_POSITIVE"

    else:

        if not verification_mode:

            if confidence < 30:
                current_state = "SAFE"

            elif confidence < 50:
                current_state = "SUSPICIOUS"

            elif confidence < 70:
                current_state = "WARNING"

    # ------------------------------------------
    # TERMINAL
    # ------------------------------------------

    print("\033c", end="")

    print("====================================")
    print("      LANDSLIDE MONITORING")
    print("====================================\n")

    print("LIVE SENSOR DATA\n")

    print(f"Pitch             : {pitch:.2f}")
    print(f"Roll              : {roll:.2f}")
    print(f"Tilt              : {tilt:.2f}")
    print(f"Vibration         : {vibration:.3f}")

    print("\n------------------------------------\n")

    print("FILTERED DATA\n")

    print(f"Average Tilt      : {avg_tilt:.2f}")
    print(f"Average Vibration : {avg_vibration:.3f}")

    print("\n------------------------------------\n")

    print("ANALYSIS\n")

    print(f"Tilt Score        : {t_score}")
    print(f"Vibration Score   : {v_score}")

    print(f"\nConfidence        : {confidence:.1f}%")
    print(f"State             : {current_state}")

    print("\n------------------------------------")

    if current_state == "SAFE":

        print("\nSTATUS : SYSTEM STABLE")

    elif current_state == "SUSPICIOUS":

        print("\nSTATUS : SUSPICIOUS MOVEMENT DETECTED")

    elif current_state == "WARNING":

        print("\nSTATUS : POSSIBLE LANDSLIDE CONDITIONS")

    elif current_state == "VERIFYING":

        print("\nSTATUS : VERIFICATION IN PROGRESS")
        print("\nPress C = Confirm")
        print("Press F = False Positive")

    elif current_state == "CONFIRMED":

        print("\nLANDSLIDE CONFIRMED")
        print("RED ALERT")
        print("EMERGENCY ACTION REQUIRED")

    elif current_state == "FALSE_POSITIVE":

        print("\nFALSE POSITIVE")
        print("NO LANDSLIDE DETECTED")
        print("RETURNING TO SAFE IN 5 SECONDS")

        time.sleep(5)

        confidence = 0
        tilt_history.clear()
        vibration_history.clear()
        verification_mode = False
        verification_result = None
        raw_confidence = 0
        avg_tilt = 0
        avg_vibration = 0
        
        current_state = "SAFE"

    print("\n====================================")

    # ------------------------------------------
    # BACKEND SYNC
    # Sends brain-calculated values to backend.
    # Backend stores and serves — never recalculates.
    # ------------------------------------------

    try:

        requests.post(
            f"{BACKEND_URL}/api/update/landslide",
            json={
                "state": current_state,
                "confidence": round(confidence, 2),
                "raw_value": round(tilt, 3),
                "raw": {
                    "pitch": round(pitch, 2),
                    "roll": round(roll, 2),
                    "tilt": round(tilt, 2),
                    "avg_tilt": round(avg_tilt, 2),
                    "vibration": round(vibration, 3),
                    "avg_vibration": round(avg_vibration, 3),
                }
            },
            timeout=0.3
        )

    except:
        pass