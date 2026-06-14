import socket
import sys
import os
import urllib.request

# ==================================================
# DEPENDENCY CHECK
# ==================================================
try:
    import qrcode
except ImportError:
    print("\n" + "=" * 54)
    print("  MISSING DEPENDENCIES")
    print("=" * 54)
    print("This launcher requires 'qrcode' and 'pillow' to run.")
    print("Please install them using pip:")
    print("    pip install qrcode pillow")
    print("=" * 54 + "\n")
    sys.exit(1)

# ==================================================
# BACKEND STATUS CHECK
# ==================================================
print("Checking backend status...")
backend_running = False
try:
    with urllib.request.urlopen("http://localhost:5005/user", timeout=1.0) as response:
        if response.status == 200:
            backend_running = True
except Exception:
    pass

if not backend_running:
    print("\n" + "!" * 54)
    print("  BACKEND NOT RUNNING")
    print("!" * 54)
    print("Please start app.py first.")
    print("Run:")
    print("    python backend/app.py")
    print("!" * 54 + "\n")
    sys.exit(0)

# ==================================================
# IP DETECTION
# ==================================================
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a public DNS IP (doesn't send actual packet)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

local_ip = get_local_ip()
dashboard_url = f"http://{local_ip}:5005/user"

# ==================================================
# QR CODE GENERATION
# ==================================================
print("\nGenerating QR code for mobile access...")

# Generate and save PNG image
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data(dashboard_url)
qr.make(fit=True)

img_file = "dashboard_qr.png"
try:
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(img_file)
    saved_path = os.path.abspath(img_file)
except Exception as e:
    saved_path = f"Could not save image: {e}"

# ==================================================
# TERMINAL DISPLAY
# ==================================================
print("\n" + "=" * 54)
print("              USER DASHBOARD QR CODE")
print("=" * 54 + "\n")

# Print QR code directly in the terminal
try:
    # invert=True is typically cleaner on dark-themed developer terminals
    qr.print_ascii(invert=True)
except Exception:
    print("[Error printing ASCII QR code to terminal]")

print("\n" + "=" * 54)
print(f"User Dashboard URL:")
print(f"  {dashboard_url}")
print("-" * 54)
print("Instructions:")
print("  1. Connect your phone to the SAME WiFi network.")
print("  2. Scan the QR code above or type the URL in your browser.")
print("  3. Open the dashboard.")
print(f"\nQR Code Image saved to:")
print(f"  {saved_path}")
print("=" * 54 + "\n")
