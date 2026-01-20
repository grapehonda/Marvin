import serial
import time
import threading
import random
from flask import Flask, request
from flask_cors import CORS
import os
import subprocess

app = Flask(__name__)
CORS(app)

# Servo serial connection
ser = serial.Serial('/dev/serial0', 115200, timeout=1)
last_command_time = time.time()
RETURN_TO_CENTER_DELAY = 5
IDLE_TIMEOUT = 5
IDLE_INTERVAL_MIN = 3
IDLE_INTERVAL_MAX = 8  # Slightly shorter max sleep for more frequent movement
SOUND_FOLDER = 'marvin_sound'
SOUND_INTERVAL = 60
last_sound_time = 0

# Filenames that trigger the depressed head shake (fixed syntax!)
DEPRESSED_QUOTES = {
    'life.wav',
    'ohno.wav',
    'depressed.wav',
    'wretched.wav',
    'endintears.wav',
}

# Reverse direction for pan and tilt (head and arms)
REVERSE_CHANNELS = {0: True, 1: True, 2: True, 3: True, 4: True, 5: True}  # head pan/tilt, left arm pan/tilt, right arm pan/tilt reversed

# Set volume at start
subprocess.call(['amixer', 'sset', 'Playback', '70%'])

def invert_position(position):
    return 3000 - position

def move_servo(channel, position, speed=500, time=1000):
    # Apply reversal if needed
    if channel in REVERSE_CHANNELS and REVERSE_CHANNELS[channel]:
        position = invert_position(position)
    
    position = max(1000, min(2000, position))
    command = f'#{channel} P{position} S{speed} T{time}\r'.encode()
    ser.write(command)
    ser.flush()

def return_to_center():
    print("Returning to center after delay")
    move_servo(0, 1500, speed=300, time=2000)  # Head pan
    move_servo(1, 1500, speed=300, time=2000)  # Head tilt
    move_servo(2, 1500, speed=300, time=2000)  # Left arm pan
    move_servo(3, 1500, speed=300, time=2000)  # Left arm tilt
    move_servo(4, 1500, speed=300, time=2000)  # Right arm pan
    move_servo(5, 1500, speed=300, time=2000)  # Right arm tilt
    global last_command_time
    last_command_time = time.time()

def perform_depressed_shake():
    print("Marvin is feeling particularly depressed - quick head shake")
    
    # Quick tilt down (slump) - fast enough to feel heavy but not drag
    move_servo(1, 1800, speed=300, time=1500)  # faster slump
    
    # Immediate, miserable head shakes - faster and tighter sync
    shake_sequence = [1350, 1650, 1350, 1650, 1500]  # more shakes, smaller range for subtlety
    for pan_pos in shake_sequence:
        move_servo(0, pan_pos, speed=400, time=1200)
        time.sleep(1.3)  # tight timing to match voice lines
    
    # Smooth return to center (head only)
    move_servo(0, 1500, speed=300, time=1500)
    move_servo(1, 1500, speed=300, time=2000)
    
    print("Depressed head shake complete")

@app.route('/move', methods=['GET'])
def move():
    global last_command_time
    pan = int(request.args.get('pan', 1500))
    tilt = int(request.args.get('tilt', 1500))
    left_pan = int(request.args.get('left_pan', 1500))
    left_tilt = int(request.args.get('left_tilt', 1500))
    right_pan = int(request.args.get('right_pan', 1500))
    right_tilt = int(request.args.get('right_tilt', 1500))
    print("Received move command: head_pan={}, head_tilt={}, left_pan={}, left_tilt={}, right_pan={}, right_tilt={}".format(pan, tilt, left_pan, left_tilt, right_pan, right_tilt))
    move_servo(0, pan)
    move_servo(1, tilt)
    move_servo(2, left_pan)
    move_servo(3, left_tilt)
    move_servo(4, right_pan)
    move_servo(5, right_tilt)
    last_command_time = time.time()
    threading.Timer(RETURN_TO_CENTER_DELAY, return_to_center).start()
    return 'Movement executed'

def idle_thread():
    global last_sound_time
    while True:
        current_time = time.time()
        time_since_last = current_time - last_command_time
        if time_since_last > IDLE_TIMEOUT:
            print("Idle detected, performing random movement")

            # More head and arm-focused idle actions - lots of variety for constant moping
            idle_actions = [
                # Head-only idles
                {'head_pan': random.randint(1200, 1800), 'head_tilt': 1500},  # slow look side to side
                {'head_pan': 1500, 'head_tilt': random.randint(1400, 1800)},  # slow look down/up
                {'head_pan': random.randint(1300, 1700), 'head_tilt': random.randint(1600, 1800)},  # gloomy slump + glance
                {'head_pan': 1500, 'head_tilt': 1700},  # small sad nod down
                {'head_pan': random.randint(1400, 1600), 'head_tilt': 1500},  # subtle side glance
                {'head_pan': 1500, 'head_tilt': random.randint(1200, 1500)},  # slight look up then center
                {'head_pan': random.randint(1250, 1750), 'head_tilt': random.randint(1500, 1800)},  # bigger miserable sweep

                # Arm idles (independent or combined)
                {'left_pan': random.randint(1300, 1700), 'left_tilt': 1500, 'right_pan': random.randint(1300, 1700), 'right_tilt': 1500},  # arm sway
                {'left_pan': 1500, 'left_tilt': random.randint(1400, 1600), 'right_pan': 1500, 'right_tilt': random.randint(1400, 1600)},  # arm shrug
                {'left_pan': random.randint(1200, 1800), 'left_tilt': random.randint(1400, 1800), 'right_pan': random.randint(1200, 1800), 'right_tilt': random.randint(1400, 1800)},  # random arm fidget
            ]
            action = random.choice(idle_actions)
            print("Selected idle action: {}".format(action))

            # Move head if present in action
            move_servo(0, action.get('head_pan', 1500), speed=250, time=3000)  # slower, more depressed pacing
            move_servo(1, action.get('head_tilt', 1500), speed=250, time=3000)

            # Move arms if present in action
            move_servo(2, action.get('left_pan', 1500), speed=250, time=3000)
            move_servo(3, action.get('left_tilt', 1500), speed=250, time=3000)
            move_servo(4, action.get('right_pan', 1500), speed=250, time=3000)
            move_servo(5, action.get('right_tilt', 1500), speed=250, time=3000)
            print("Idle movement completed")

            if current_time - last_sound_time > SOUND_INTERVAL:
                wav_files = [f for f in os.listdir(SOUND_FOLDER) if f.endswith('.wav')]
                if wav_files:
                    random_wav = random.choice(wav_files)
                    full_path = os.path.join(SOUND_FOLDER, random_wav)
                    print(f"Playing sound: {random_wav}")

                    is_depressed_quote = random_wav in DEPRESSED_QUOTES

                    player = subprocess.Popen(['aplay', full_path])

                    if is_depressed_quote:
                        threading.Thread(target=perform_depressed_shake, daemon=True).start()

                    player.wait()

                    last_sound_time = current_time
        else:
            print("Not idle yet")
        sleep_duration = random.randint(IDLE_INTERVAL_MIN, IDLE_INTERVAL_MAX)
        print("Sleeping for {} seconds".format(sleep_duration))
        time.sleep(sleep_duration)

if __name__ == '__main__':
    print("Starting idle thread")
    threading.Thread(target=idle_thread, daemon=True).start()
    print("Idle thread started, launching Flask app")
    app.run(host='0.0.0.0', port=5003)
