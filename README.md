Requirements

- SillyTavern (latest version recommended).
- SillyTavern-Extras (ST-extras) installed and running with the flag: 
`--enable-modules=classify --classification-model j-hartmann/emotion-english-distilroberta-base` for the J-Hartmann emotion classification model.
- Node.js (for SillyTavern extensions).
- Python 3.x with dependencies: flask, flask-cors, pyserial.
- Access to SillyTavern's classification API (provided via ST-extras).

Hardware

Raspberry Pi/PCA9685 Servo breakout board (or ssc-32, both versions included).
6 servo motors connected to channels 0-5:
0: Head Pan
1: Head Tilt
2: Left Arm Pan
3: Left Arm Tilt
4: Right Arm Pan
5: Right Arm Tilt

Audio setup (e.g., speakers connected to Pi) with aplay for WAV playback.
A folder named marvin_sound containing WAV files (e.g., depressive quotes like life.wav, ohno.wav).

Note: The backend assumes the Pi's IP is 192.168.1.51. Update the JS code if different.
Usage

Enable the "Marvin" extension in SillyTavern settings.
Ensure ST-extras server is running with the required flag for classification.
Start a chat session. As the AI generates responses, the extension will analyze text, classify sentiment (biased toward sadness), and send movement commands.
When idle, the robot will perform random movements and play sounds.
For depressed quotes (specific WAV files), a special head-shake animation triggers.

Example Sentiment Mappings

Sadness: Head tilts down, arms lower.
Joy: Head pans left, arms raise.
Anger: Head pans right, right arm extends.
Default/Neutral: Falls back to sadness pose.

Troubleshooting

No Movements: Check the Pi IP in script.js and ensure the server is running.
Sentiment Errors: Verify ST-extras is running with the correct flag and the classification API is enabled.
Sounds Not Playing: Ensure aplay is installed and WAV files are valid.

Contributing
This is a personal project, but pull requests are welcome for improvements like configurable IPs, more sentiments, or better idle variety.
License
MIT License. Feel free to modify and use for your own depressed robots!
Author

grapehonda (Custom)

Version: 1.0
