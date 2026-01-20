# Marvin: SillyTavern Extension for Sentiment Analysis and Servo Control

## Description

Marvin is a custom extension for SillyTavern, a text-based AI chat interface. It adds real-time sentiment analysis to AI-generated messages and controls a physical robot (inspired by Marvin, the paranoid android from *The Hitchhiker's Guide to the Galaxy*) using servo motors. The extension biases sentiment detection toward "sadness" to match the character's depressed personality, translating emotions into head and arm movements. It also includes idle behaviors like random fidgeting and playback of depressive sound quotes when the robot is inactive.

This project bridges software AI with hardware robotics, creating an immersive experience where the robot physically reacts to chat content.

## Features

- **Sentiment Analysis**: Classifies text emotions (anger, disgust, fear, joy, neutral, sadness, surprise) using SillyTavern's API, with a strong bias toward sadness for low-confidence or neutral results.
- **Real-Time Movement**: During message generation, analyzes text in chunks (250 characters) and sends servo commands to express sentiments (e.g., head tilt down for sadness, arms raised for joy).
- **Idle Behaviors**: When inactive for 5 seconds, performs random "moping" movements (e.g., head glances, arm shrugs) every 3-8 seconds. Plays random WAV sounds from a folder every 60 seconds, with special head-shake animations for particularly depressed quotes.
- **Hardware Control**: Uses a Python Flask server to handle HTTP requests and send commands to servos via serial (e.g., on a Raspberry Pi).
- **Cooldowns and Safety**: Minimum 2-second cooldown between movements; auto-return to neutral pose after 5 seconds.

## Requirements

### Software
- [SillyTavern](https://github.com/SillyTavern/SillyTavern) (latest version recommended).
- Node.js (for SillyTavern extensions).
- Python 3.x with dependencies: `flask`, `flask-cors`, `pyserial` (install via `pip install flask flask-cors pyserial`).
- Access to SillyTavern's classification API for sentiment analysis.

### Hardware
- Raspberry Pi (or similar) with serial-enabled GPIO (e.g., `/dev/serial0` at 115200 baud).
- 6 servo motors connected to channels 0-5:
  - 0: Head Pan
  - 1: Head Tilt
  - 2: Left Arm Pan
  - 3: Left Arm Tilt
  - 4: Right Arm Pan
  - 5: Right Arm Tilt
- Audio setup (e.g., speakers connected to Pi) with `aplay` for WAV playback.
- A folder named `marvin_sound` containing WAV files (e.g., depressive quotes like `life.wav`, `ohno.wav`).

Note: The backend assumes the Pi's IP is `192.168.1.51`. Update the JS code if different.
