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
PORT = 5002

BACKEND_URL = "http://localhost:5005"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print("\nCLOUDBURST BRAIN STARTED...\n")

# ==================================================
# MEMORY
# ==================================================

humidity_history = deque(maxlen=20)

confidence = 0.0

current_state = "SAFE"

verification_mode = False
verification_result = None

baseline_humidity = None
baseline_ready = False

baseline_samples = []

# ==================================================
# SCORING
# ==================================================

def humidity_score(humidity):

    if humidity < 65:
        return 0

    elif humidity < 70:
        return 20

    elif humidity < 75:
        return 40

    elif humidity < 80:
        return 60

    else:
        return 80


def change_score(change):

    if change < 2:
        return 0

    elif change < 4:
        return 30

    elif change < 6:
        return 50

    elif change < 8:
        return 70

    else:
        return 90


# ==================================================
# KEYBOARD
# ==================================================

def check_keyboard():

    global verification_result
    global confidence
    global current_state
    global verification_mode

    if msvcrt.kbhit():

        try:

            key = msvcrt.getch().decode("utf-8").upper()

            if key == "C":
                verification_result = "CONFIRMED"

            elif key == "F":
                verification_result = "FALSE_POSITIVE"

            elif key == "R":

                confidence = 0

                humidity_history.clear()

                verification_result = None
                verification_mode = False

                current_state = "SAFE"

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

    try:

        r = requests.get(
            f"{BACKEND_URL}/api/pending/cloudburst",
            timeout=0.3
        )

        action = r.json().get("action")

        if action == "CONFIRM" and verification_mode:
            verification_result = "CONFIRMED"

        elif action == "FALSE_POSITIVE" and verification_mode:
            verification_result = "FALSE_POSITIVE"

        elif action == "RESET":
            confidence = 0
            humidity_history.clear()
            verification_result = None
            verification_mode = False
            current_state = "SAFE"

    except:
        pass


# ==================================================
# MAIN LOOP
# ==================================================

while True:

    data, addr = sock.recvfrom(4096)

    packet = json.loads(data.decode())

    humidity = float(packet["humidity"])
    temperature = float(packet["temperature"])

    # ------------------------------------------
    # BASELINE LEARNING
    # ------------------------------------------

    if not baseline_ready:

        baseline_samples.append(humidity)

        if len(baseline_samples) >= 20:

            baseline_humidity = mean(baseline_samples)

            baseline_ready = True

    # ------------------------------------------
    # HISTORY
    # ------------------------------------------

    humidity_history.append(humidity)

    avg_humidity = mean(humidity_history)

    # ------------------------------------------
    # ANALYSIS
    # ------------------------------------------

    if baseline_ready:

        humidity_change = avg_humidity - baseline_humidity

        h_score = humidity_score(avg_humidity)
        c_score = change_score(humidity_change)

        raw_confidence = h_score + c_score

        if raw_confidence > 100:
            raw_confidence = 100

        # --------------------------------------
        # FAST RISE / SLOW FALL
        # --------------------------------------

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

    else:

        humidity_change = 0
        h_score = 0
        c_score = 0

    # ------------------------------------------
    # STATE MACHINE
    # ------------------------------------------

    if (
        confidence >= 70
        and not verification_mode
        and current_state != "CONFIRMED"
    ):

        verification_mode = True
        current_state = "VERIFYING"

    check_backend()

    if verification_mode:
        check_keyboard()

    if verification_result == "CONFIRMED":

        current_state = "CONFIRMED"
        verification_mode = False

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
    # DISPLAY
    # ------------------------------------------

    print("\033c", end="")

    print("====================================")
    print("      CLOUDBURST MONITORING")
    print("====================================\n")

    print("LIVE SENSOR DATA\n")

    print(f"Humidity          : {humidity:.1f}%")
    print(f"Temperature       : {temperature:.1f}C")

    print("\n------------------------------------\n")

    if baseline_ready:

        print("BASELINE ANALYSIS\n")

        print(f"Baseline Humidity : {baseline_humidity:.1f}%")
        print(f"Average Humidity  : {avg_humidity:.1f}%")
        print(f"Humidity Change   : {humidity_change:.1f}%")

        print("\n------------------------------------\n")

        print("SCORING\n")

        print(f"Humidity Score    : {h_score}")
        print(f"Change Score      : {c_score}")

        print(f"\nConfidence        : {confidence:.1f}%")
        print(f"State             : {current_state}")

    else:

        print("LEARNING BASELINE...")
        print(f"Samples Collected : {len(baseline_samples)}/20")

    print("\n------------------------------------")

    if current_state == "SAFE":

        print("\nSTATUS : WEATHER STABLE")

    elif current_state == "SUSPICIOUS":

        print("\nSTATUS : HUMIDITY RISING")

    elif current_state == "WARNING":

        print("\nSTATUS : POSSIBLE CLOUDBURST CONDITIONS")

    elif current_state == "VERIFYING":

        print("\nSTATUS : VERIFICATION IN PROGRESS")

        print("\nPress C = Confirm")
        print("Press F = False Positive")
        print("Press R = Reset")

    elif current_state == "CONFIRMED":

        print("\nCLOUDBURST CONFIRMED")
        print("RED ALERT")
        print("EMERGENCY ACTION REQUIRED")
        print("\nPress R = Reset")

    elif current_state == "FALSE_POSITIVE":

        print("\nFALSE POSITIVE")
        print("NO CLOUDBURST DETECTED")
        print("\nPress R = Reset")

    print("\n====================================")

    # ------------------------------------------
    # BACKEND SYNC
    # Sends brain-calculated values to backend.
    # Backend stores and serves — never recalculates.
    # ------------------------------------------

    try:

        requests.post(
            f"{BACKEND_URL}/api/update/cloudburst",
            json={
                "state": current_state,
                "confidence": round(confidence, 2),
                "raw_value": round(humidity, 1),
                "raw": {
                    "humidity": round(humidity, 1),
                    "temperature": round(temperature, 1),
                    "baseline_humidity": round(baseline_humidity, 1) if baseline_ready else None,
                    "avg_humidity": round(avg_humidity, 1),
                    "humidity_change": round(humidity_change, 1),
                    "baseline_ready": baseline_ready,
                }
            },
            timeout=0.3
        )

    except:
        pass