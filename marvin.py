import board
import busio
import adafruit_pca9685
import time
import threading
import random
from flask import Flask, request
from flask_cors import CORS
import os
import subprocess

app = Flask(__name__)
CORS(app)

# PCA9685 setup
i2c = busio.I2C(board.SCL, board.SDA)
pca = adafruit_pca9685.PCA9685(i2c)
pca.frequency = 50

# Set initial positions to center
for channel in range(6):
    off = int((1500 / 20000.0) * 65535)
    pca.channels[channel].duty_cycle = off

# Track current positions
current_positions = [1500 for _ in range(6)]

last_command_time = time.time()
RETURN_TO_CENTER_DELAY = 5
IDLE_TIMEOUT = 5
IDLE_INTERVAL_MIN = 3
IDLE_INTERVAL_MAX = 8
SOUND_FOLDER = 'marvin_sound'
SOUND_INTERVAL = 60
last_sound_time = 0

DEPRESSED_QUOTES = {
    'life.wav',
    'ohno.wav',
    'depressed.wav',
    'wretched.wav',
    'endintears.wav',
}

REVERSE_CHANNELS = {0: True, 1: True, 2: True, 3: True, 4: True, 5: True}

subprocess.call(['amixer', 'sset', 'Playback', '70%'])

def set_servo_pulse(channel, pulse):
    pulse = max(1000, min(2000, pulse))
    off = int((pulse / 20000.0) * 65535)
    pca.channels[channel].duty_cycle = off

def ramp_servo(channel, target, duration_ms, steps=500):
    current = current_positions[channel]
    delta = target - current
    if delta == 0:
        return
    step_us = delta / steps
    step_delay = (duration_ms / 1000.0) / steps
    for _ in range(steps):
        current += step_us
        set_servo_pulse(channel, int(current))
        time.sleep(step_delay)
    set_servo_pulse(channel, target)
    current_positions[channel] = target

def move_servo(channel, position, time=2000):
    if channel in REVERSE_CHANNELS and REVERSE_CHANNELS[channel]:
        position = 3000 - position
    target = max(1000, min(2000, position))
    ramp_servo(channel, target, time)

def return_to_center():
    print("Returning to center after delay")
    move_servo(0, 1500)
    move_servo(1, 1500)
    move_servo(2, 1500)
    move_servo(3, 1500)
    move_servo(4, 1500)
    move_servo(5, 1500)
    global last_command_time
    last_command_time = time.time()

def perform_depressed_shake():
    print("Marvin is feeling particularly depressed - quick head shake")
    
    move_servo(1, 1800, time=2000)  # slow slump
    
    shake_sequence = [1350, 1650, 1350, 1650, 1500]
    for pan_pos in shake_sequence:
        move_servo(0, pan_pos, time=2000)  # slower shakes for heavy feel
    
    # No redundant pan return - last shake ends at center
    move_servo(1, 1500, time=2500)  # slow lift
    
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

            idle_actions = [
                {'head_pan': random.randint(1200, 1800), 'head_tilt': 1500},
                {'head_pan': 1500, 'head_tilt': random.randint(1400, 1800)},
                {'head_pan': random.randint(1300, 1700), 'head_tilt': random.randint(1600, 1800)},
                {'head_pan': 1500, 'head_tilt': 1700},
                {'head_pan': random.randint(1400, 1600), 'head_tilt': 1500},
                {'head_pan': 1500, 'head_tilt': random.randint(1200, 1500)},
                {'head_pan': random.randint(1250, 1750), 'head_tilt': random.randint(1500, 1800)},
                {'left_pan': random.randint(1300, 1700), 'left_tilt': 1500, 'right_pan': random.randint(1300, 1700), 'right_tilt': 1500},
                {'left_pan': 1500, 'left_tilt': random.randint(1400, 1600), 'right_pan': 1500, 'right_tilt': random.randint(1400, 1600)},
                {'left_pan': random.randint(1200, 1800), 'left_tilt': random.randint(1400, 1800), 'right_pan': random.randint(1200, 1800), 'right_tilt': random.randint(1400, 1800)},
            ]
            action = random.choice(idle_actions)
            print("Selected idle action: {}".format(action))

            move_servo(0, action.get('head_pan', 1500))
            move_servo(1, action.get('head_tilt', 1500))
            move_servo(2, action.get('left_pan', 1500))
            move_servo(3, action.get('left_tilt', 1500))
            move_servo(4, action.get('right_pan', 1500))
            move_servo(5, action.get('right_tilt', 1500))
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
                        perform_depressed_shake()  # Call directly, no thread - blocks idle until shake done

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
