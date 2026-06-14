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
PORT = 5001

BACKEND_URL = "http://localhost:5005"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print("\nEARTHQUAKE BRAIN STARTED...\n")

# ==================================================
# MEMORY
# ==================================================

vibration_history = deque(maxlen=20)

confidence = 0.0
current_state = "SAFE"

verification_mode = False
verification_result = None

# ==================================================
# EARTHQUAKE SCORING
# ==================================================

def vibration_score(vib):

    if vib < 0.04:
        return 0

    elif vib < 0.10:
        return 25

    elif vib < 0.25:
        return 50

    elif vib < 0.50:
        return 80

    else:
        return 100


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

    try:

        r = requests.get(
            f"{BACKEND_URL}/api/pending/earthquake",
            timeout=0.3
        )

        action = r.json().get("action")

        if action == "CONFIRM" and verification_mode:
            verification_result = "CONFIRMED"

        elif action == "FALSE_POSITIVE" and verification_mode:
            verification_result = "FALSE_POSITIVE"

        elif action == "RESET":
            confidence = 0
            vibration_history.clear()
            verification_mode = False
            verification_result = None
            current_state = "SAFE"

    except:
        pass


# ==================================================
# MAIN LOOP
# ==================================================

while True:

    data, addr = sock.recvfrom(4096)

    packet = json.loads(data.decode())

    vibration = float(packet["vibration"])

    # ------------------------------------------
    # HISTORY
    # ------------------------------------------

    vibration_history.append(vibration)

    avg_vibration = mean(vibration_history)

    # ------------------------------------------
    # SCORING
    # ------------------------------------------

    v_score = vibration_score(avg_vibration)

    raw_confidence = v_score

    # ------------------------------------------
    # FAST RISE / SLOW FALL
    # ------------------------------------------

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

    if (
    confidence >= 70
    and not verification_mode
    and current_state != "CONFIRMED"
):

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
    # TERMINAL
    # ------------------------------------------

    print("\033c", end="")

    print("====================================")
    print("      EARTHQUAKE MONITORING")
    print("====================================\n")

    print("LIVE SENSOR DATA\n")

    print(f"Vibration         : {vibration:.5f}")

    print("\n------------------------------------\n")

    print("FILTERED DATA\n")

    print(f"Average Vibration : {avg_vibration:.5f}")

    print("\n------------------------------------\n")

    print("ANALYSIS\n")

    print(f"Vibration Score   : {v_score}")

    print(f"\nConfidence        : {confidence:.1f}%")

    print(f"State             : {current_state}")

    print("\n------------------------------------")

    if current_state == "SAFE":

        print("\nSTATUS : SYSTEM STABLE")

    elif current_state == "SUSPICIOUS":

        print("\nSTATUS : MINOR TREMORS DETECTED")

    elif current_state == "WARNING":

        print("\nSTATUS : POSSIBLE EARTHQUAKE ACTIVITY")

    elif current_state == "VERIFYING":

        print("\nSTATUS : VERIFICATION IN PROGRESS")

        print("\nPress C = Confirm")
        print("Press F = False Positive")

    elif current_state == "CONFIRMED":

        print("\nEARTHQUAKE CONFIRMED")
        print("RED ALERT")
        print("EMERGENCY ACTION REQUIRED")

    elif current_state == "FALSE_POSITIVE":

        print("\nFALSE POSITIVE")
        print("NO EARTHQUAKE DETECTED")
        print("RETURNING TO SAFE IN 5 SECONDS")

        time.sleep(5)

        confidence = 0

        vibration_history.clear()

        verification_mode = False
        verification_result = None

        current_state = "SAFE"

    print("\n====================================")

    # ------------------------------------------
    # BACKEND SYNC
    # Sends brain-calculated values to backend.
    # Backend stores and serves — never recalculates.
    # ------------------------------------------

    try:

        requests.post(
            f"{BACKEND_URL}/api/update/earthquake",
            json={
                "state": current_state,
                "confidence": round(confidence, 2),
                "raw_value": round(vibration, 5),
                "raw": {
                    "vibration": round(vibration, 5),
                    "avg_vibration": round(avg_vibration, 5),
                }
            },
            timeout=0.3
        )

    except:
        pass