import socket
import json
import msvcrt
import requests
from collections import deque
from statistics import mean

# ==================================================
# CONFIG
# ==================================================

HOST = "0.0.0.0"
PORT = 5003

BACKEND_URL = "http://localhost:5005"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print("\nFOREST FIRE BRAIN STARTED...\n")

# ==================================================
# MEMORY
# ==================================================

smoke_history = deque(maxlen=20)

confidence = 0.0

current_state = "SAFE"

verification_mode = False
verification_result = None

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

                smoke_history.clear()

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
            f"{BACKEND_URL}/api/pending/forest_fire",
            timeout=0.3
        )

        action = r.json().get("action")

        if action == "CONFIRM" and verification_mode:
            verification_result = "CONFIRMED"

        elif action == "FALSE_POSITIVE" and verification_mode:
            verification_result = "FALSE_POSITIVE"

        elif action == "RESET":
            confidence = 0
            smoke_history.clear()
            verification_result = None
            verification_mode = False
            current_state = "SAFE"

    except:
        pass


# ==================================================
# SMOKE LEVEL
# ==================================================

def smoke_level(avg_smoke):

    if avg_smoke < 650:
        return 0

    elif avg_smoke < 1200:
        return 1

    elif avg_smoke < 2000:
        return 2

    else:
        return 3


# ==================================================
# MAIN LOOP
# ==================================================

while True:

    data, addr = sock.recvfrom(4096)

    packet = json.loads(data.decode())

    smoke = int(packet["smoke"])

    # ------------------------------------------
    # HISTORY
    # ------------------------------------------

    smoke_history.append(smoke)

    avg_smoke = mean(smoke_history)

    # ------------------------------------------
    # LEVEL
    # ------------------------------------------

    level = smoke_level(avg_smoke)

    # ------------------------------------------
    # PERSISTENCE CONFIDENCE ENGINE
    # ------------------------------------------

    if current_state not in ["CONFIRMED", "FALSE_POSITIVE"]:

        if level == 0:

            confidence = max(
                0,
                confidence - 3
            )

        elif level == 1:

            confidence = min(
                100,
                confidence + 0.3
            )

        elif level == 2:

            confidence = min(
                100,
                confidence + 1
            )

        elif level == 3:

            confidence = min(
                100,
                confidence + 3
            )

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

    # ------------------------------------------
    # KEYBOARD + BACKEND
    # ------------------------------------------

    check_backend()

    if verification_mode:
        check_keyboard()

    if current_state == "CONFIRMED":
        check_keyboard()

    if current_state == "FALSE_POSITIVE":
        check_keyboard()

    # ------------------------------------------
    # RESULTS
    # ------------------------------------------

    if verification_result == "CONFIRMED":

        current_state = "CONFIRMED"
        verification_mode = False

    elif verification_result == "FALSE_POSITIVE":

        current_state = "FALSE_POSITIVE"
        verification_mode = False

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
    print("      FOREST FIRE MONITORING")
    print("====================================\n")

    print("LIVE SENSOR DATA\n")

    print(f"Smoke Value       : {smoke}")

    print("\n------------------------------------\n")

    print("FILTERED DATA\n")

    print(f"Average Smoke     : {avg_smoke:.1f}")

    print("\n------------------------------------\n")

    print("ANALYSIS\n")

    if level == 0:
        level_text = "SAFE"

    elif level == 1:
        level_text = "LIGHT SMOKE"

    elif level == 2:
        level_text = "MEDIUM SMOKE"

    else:
        level_text = "HEAVY SMOKE"

    print(f"Smoke Level       : {level_text}")

    print(f"\nConfidence        : {confidence:.1f}%")

    print(f"State             : {current_state}")

    print("\n------------------------------------")

    if current_state == "SAFE":

        print("\nSTATUS : AIR QUALITY NORMAL")

    elif current_state == "SUSPICIOUS":

        print("\nSTATUS : LIGHT SMOKE DETECTED")

    elif current_state == "WARNING":

        print("\nSTATUS : POSSIBLE FIRE CONDITIONS")

    elif current_state == "VERIFYING":

        print("\nSTATUS : VERIFICATION IN PROGRESS")

        print("\nPress C = Confirm")
        print("Press F = False Positive")
        print("Press R = Reset")

    elif current_state == "CONFIRMED":

        print("\nFOREST FIRE CONFIRMED")
        print("RED ALERT")
        print("EMERGENCY ACTION REQUIRED")

        print("\nPress R = Reset")

    elif current_state == "FALSE_POSITIVE":

        print("\nFALSE POSITIVE")
        print("NO FIRE DETECTED")

        print("\nPress R = Reset")

    print("\n====================================")

    # ------------------------------------------
    # BACKEND SYNC
    # Sends brain-calculated values to backend.
    # Backend stores and serves — never recalculates.
    # ------------------------------------------

    try:

        requests.post(
            f"{BACKEND_URL}/api/update/forest_fire",
            json={
                "state": current_state,
                "confidence": round(confidence, 2),
                "raw_value": smoke,
                "raw": {
                    "smoke": smoke,
                    "avg_smoke": round(avg_smoke, 1),
                    "smoke_level": level_text,
                }
            },
            timeout=0.3
        )

    except:
        pass