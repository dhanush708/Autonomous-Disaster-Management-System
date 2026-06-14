# 🏗️ System Architecture

## High-Level Architecture

```text
┌─────────────────────────────────────┐
│          SENSOR LAYER               │
├─────────────────────────────────────┤
│ ESP32 + Smoke Sensor                │
│ ESP32 + MPU6050 (Landslide)         │
│ ESP32 + MPU6050 (Earthquake)        │
│ ESP32 + DHT22 (Cloudburst)          │
└─────────────────────────────────────┘
                    │
                    │ UDP Communication
                    ▼

┌─────────────────────────────────────┐
│       DISASTER INTELLIGENCE         │
├─────────────────────────────────────┤
│ Forest Fire Brain                   │
│ Landslide Brain                     │
│ Earthquake Brain                    │
│ Cloudburst Brain                    │
└─────────────────────────────────────┘
                    │
                    │ State + Confidence
                    ▼

┌─────────────────────────────────────┐
│         FLASK BACKEND               │
├─────────────────────────────────────┤
│ State Management                    │
│ API Endpoints                       │
│ Event Logging                       │
│ Verification Routing                │
│ Dashboard Communication             │
└─────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼

┌──────────────────┐   ┌──────────────────┐
│ ADMIN DASHBOARD  │   │ USER DASHBOARD   │
├──────────────────┤   ├──────────────────┤
│ Live Monitoring  │   │ Mobile Friendly  │
│ Graphs           │   │ Public Alerts    │
│ Verification     │   │ Disaster Status  │
│ Event Timeline   │   │ Live Updates     │
└──────────────────┘   └──────────────────┘
        │
        │ Verification Actions
        ▼

┌─────────────────────────────────────┐
│      VERIFICATION WORKFLOW          │
├─────────────────────────────────────┤
│ Confirm                             │
│ False Positive                      │
│ Reset                               │
└─────────────────────────────────────┘
                    │
                    ▼

┌─────────────────────────────────────┐
│      FUTURE ROVER INTEGRATION       │
├─────────────────────────────────────┤
│ Autonomous Deployment               │
│ Camera Verification                 │
│ AI Assisted Decision Making         │
│ Automatic Confirmation              │
└─────────────────────────────────────┘
```

---

# Disaster Processing Pipeline

```text
Sensor Reading
      │
      ▼
Disaster Brain
      │
      ▼
Noise Filtering
      │
      ▼
Historical Analysis
      │
      ▼
Confidence Calculation
      │
      ▼
State Machine
      │
      ▼
SAFE
SUSPICIOUS
WARNING
VERIFYING
      │
      ▼
Admin Verification
      │
      ├─────────────► FALSE_POSITIVE
      │
      ▼
CONFIRMED
```

---

# Communication Flow

```text
ESP32
  │
  ▼
UDP Packet
  │
  ▼
Python Disaster Brain
  │
  ▼
Flask Backend API
  │
  ▼
Admin Dashboard
  │
  ▼
User Dashboard
```

---

# Software Architecture Contribution

The embedded hardware layer is responsible for collecting environmental data.

The software platform is responsible for:

* Disaster Intelligence Engines
* Confidence Score Framework
* State Machine Design
* Verification Workflow
* Flask Backend Architecture
* Dashboard Communication Layer
* Admin Dashboard Logic
* User Dashboard Logic
* Real-Time Visualization
* Mobile Monitoring Platform
* Future Rover Integration Architecture

This project combines embedded systems engineering with a custom-designed software platform for disaster analysis and decision support.

---

# Key Design Principles

✅ Modular Architecture

✅ Independent Disaster Brains

✅ Confidence-Based Detection

✅ False Positive Reduction

✅ Real-Time Monitoring

✅ Verification Before Confirmation

✅ Mobile Accessibility

✅ Future Autonomous Expansion

✅ Separation of Hardware and Software Responsibilities

```
```
