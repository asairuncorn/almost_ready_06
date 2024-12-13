import eventlet
eventlet.monkey_patch()

from presure_emulator import CountdownTimer
import copy
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time
import RPi.GPIO as GPIO
from switch import Switch
# from led import LED
from pump import Pump
from timer import Timer
from sensor import PressureSensor
import threading
import os


#

# GPIO setup
GPIO.setmode(GPIO.BCM)
SWITCH_PIN = 17  # GPIO pin for the start switch
LED_PIN = 27     # GPIO pin for the LED
RELAY_PIN = 22   # GPIO pin for the pump relay

# Application setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_default_secret_key')  # Use environment variable or default key
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize peripherals
switch = Switch(SWITCH_PIN)
# led = LED(LED_PIN)

# Shared state
progress_state = {
    1: {'status': 'Ready', 'progress': 0, 'pressure': 0, 'switch_status': 'off'},
    2: {'status': 'nie', 'progress': 0, 'pressure': 0, 'switch_status': 'off'},
    3: {'status': 'Ready', 'progress': 0, 'pressure': 0, 'switch_status': 'off'},
    4: {'status': 'Ready', 'progress': 0, 'pressure': 0, 'switch_status': 'off'},
}


def monitor_progress_state():
    previous_state = copy.deepcopy(progress_state)
    while True:
        # Check for changes in progress_state
        for bay_id, current_state in progress_state.items():
            if current_state != previous_state[bay_id]:
                with app.app_context():
                    # Emit updated state to the client
                    socketio.emit('update_state', progress_state, broadcast=True)
                    previous_state[bay_id] = copy.deepcopy(current_state)  # Update the previous state

        time.sleep(0.1)  # Adjust the interval as needed


# Start the monitoring thread
# threading.Thread(target=monitor_progress_state, daemon=True).start()







# Monitor switch status
def monitor_switch():
    previous_switch_state = False  # Assume the switch starts as not pressed
    while True:
        current_switch_state = switch.is_pressed()

        # Emit only if the switch state has changed
        if current_switch_state != previous_switch_state:
            with app.app_context():
                if current_switch_state:
                    progress_state[1]['status'] = 'Ready'
                    progress_state[1]['switch_status'] = 'on'
                    socketio.emit('update_state', progress_state[1])
                    socketio.emit('update_state', progress_state[1]['status'])
                    print(progress_state[1]['status'])
                else:
                    progress_state[1]['switch_status'] = 'off'
                    socketio.emit('update_state', progress_state[1])

            previous_switch_state = current_switch_state

        # Always emit "off" status if the switch is not pressed
        if not current_switch_state:
            with app.app_context():
                progress_state[1]['switch_status'] = 'off'
                socketio.emit('update_state', progress_state[1])

        time.sleep(0.1)


# Start the monitor thread
threading.Thread(target=monitor_switch, daemon=True).start()

# Progress update helper
def update_progress_dial(progress):
    #
    # with app.app_context():
    #     progress_state[1]['progress'] = progress
    #     emit('update_state', {'bay_id': 1, 'status': 'Running', 'progress': progress}, broadcast=True)
    #     # progress_state[1]['progress'] = progress
    #     socketio.emit('update_state', progress_state[1], broadcast=True)
    #     print("wysylam do progres state")
    #     print(progress_state[1]['progress'])
    #     if progress == 100:
    #         progress_state[1]['status'] = 'Finished+'
    #         time.sleep(2)
    #         # emit('update_state', {'bay_id': 1, 'status': 'Finished', 'progress': 0}, broadcast=True)
    #         progress_state[1]['progress'] = 0
    #         emit('update_state', progress_state[1]['progress'], broadcast=True)
    emit('update_state', {'bay_id': 1, 'status': 'Running', 'progress': progress}, broadcast=True)

    if progress == 100:
        progress_state[1]['status'] = 'Finished'
        time.sleep(2)
        emit('update_state', {'bay_id': 1, 'status': 'Finished', 'progress': 0}, broadcast=True)
        progress_state[1]['switch_status'] = 'off'
        print(progress_state)


# Flask routes
@app.route('/')
def index():
    return render_template('index_n.html')

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print("emiting data")
    emit('initialize_state', progress_state)



@socketio.on('start_progress')
def handle_start_progress(data):
    bay_id = data['bay_id']
    progress_state[bay_id]['status'] = 'Running'
    progress_state[bay_id]['progress'] = 0
    emit('update_state', {'bay_id': bay_id, 'status': 'Running', 'progress': 0}, broadcast=True)

    pump = Pump(RELAY_PIN)

    emit('update_state', {'bay_id': bay_id, 'status': 'Running', 'pressure': 22}, broadcast=True)


    pressure_sensor = PressureSensor()
    timer = Timer(5, pressure_sensor)
    timer.start(update_progress_dial)

@socketio.on('stop_progress')
def handle_stop_progress(data):
    bay_id = data['bay_id']
    progress_state[bay_id]['status'] = 'Stopped'
    emit('update_state', {'bay_id': bay_id, 'status': 'Stopped', 'progress': progress_state[bay_id]['progress']}, broadcast=True)

# @socketio.on('update_pressure')
# def handle_update_pressure(data):
#     bay_id = data['bay_id']
#     pressure = data['pressure']
#     progress_state[bay_id]['pressure'] = pressure
#     emit('update_pressure', {'bay_id': bay_id, 'pressure': pressure}, broadcast=True)
#
# @socketio.on('set_time')
# def handle_set_time(data):
#     bay_id = data['bay_id']
#     time = data['time']
#     emit('update_time', {'bay_id': bay_id, 'time': time}, broadcast=True)

# Run server
if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5001, debug=True)




