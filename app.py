import datetime
import sys
from typing import List, Tuple

from flask import Flask, render_template, request, redirect, url_for
import schedule
import time
import threading
import socket
import signal

# Used for communicating with the serial program
IP_HDR = "IP_ADDR"          # Sending IP
OFF_HDR = "LIGHT_OFF"       # Sending light off
ON_HDR = "LIGHT_ON"         # Sending light on
PRANK_ON_HDR = "PRANK_ON"   # Sending prank mode on

app = Flask(__name__)

# All the currently scheduled jobs
# [(time, str rep, job object), ...]
jobs: List[Tuple[datetime.time, str, schedule.Job]] = []

# Send the given IP string
def send_ip(ip: str):
    print(f"{IP_HDR}:{ip}", flush=True)
    print("[SERVER] Sent ip", file=sys.stderr, flush=True)

# Send the light off message
def light_off():
    print(f"{OFF_HDR}", flush=True)
    print("[SERVER] Sent off", file=sys.stderr, flush=True)

# Send the light on message
def light_on():
    print(f"{ON_HDR}", flush=True)
    print("[SERVER] Sent on", file=sys.stderr, flush=True)

# Send the prank mode on message
def prank_on():
    print(f"{PRANK_ON_HDR}", flush=True)
    print("[SERVER] Sent prank on", file=sys.stderr, flush=True)

# Function used to sort the job list. Retrieves the time of the job
def jobs_sort(job: Tuple[datetime.time, str, schedule.Job]):
    return job[0]

# Creates a list of the string representations of the scheduled jobs
def pretty_jobs(ugly_jobs: List[Tuple[datetime.time, str, schedule.Job]]):
    return [j[1] for j in ugly_jobs]

# Creates a background thread to run scheduled jobs
# Returns an Event which can be used to stop the thread
def run_continuously(interval=1):
    end = threading.Event()

    class RunThread(threading.Thread):

        @classmethod
        def run(cls):
            while not end.is_set():
                schedule.run_pending()
                time.sleep(interval)

    thread = RunThread()
    thread.start()
    return end

# Start the background thread
end_scheduler = run_continuously()

# Handles when the program is terminated with SIGINT
def quit_handler(signum, frame):
    print("Shutting down scheduler...", file=sys.stderr, flush=True)
    end_scheduler.set()
    exit(0)

# Register the quit handler for SIGINT
signal.signal(signal.SIGINT, quit_handler)

# Default route
@app.route("/")
def default():
    return redirect(url_for('control'))

# Explicit control route
@app.route("/control")
def control():
    return render_template("control.html", set_events=pretty_jobs(jobs))

# Where the control form is POSTed to for processing. Redirects to /control
@app.route("/control_form", methods=['POST'])
def control_form():
    # Retrieve which of the base four options was chosen
    option = request.form.get("options")
    if option == "set_event": # Check if we're managing events
        print("Managing events", file=sys.stderr, flush=True)

        # Get which type of modification is being done
        manage_e_option = request.form.get("e_mod_type")
        if manage_e_option == "add_event": # Adding an event
            print("Adding event", file=sys.stderr, flush=True)
            e_option = request.form.get("e_options")
            if e_option == "e_light_on": # Light on
                print(f"Scheduling on at {request.form.get('e_time')}", flush=True, file=sys.stderr)
                job = schedule.every().day.at(request.form.get("e_time")).do(light_on)
                jobs.append((job.at_time, f"Light ON at {job.at_time}", job))
                jobs.sort(key=jobs_sort)
            elif e_option == "e_light_off": # Light off
                print(f"Scheduling off at {request.form.get('e_time')}", flush=True, file=sys.stderr)
                job = schedule.every().day.at(request.form.get("e_time")).do(light_off)
                jobs.append((job.at_time, f"Light OFF at {job.at_time}", job))
                jobs.sort(key=jobs_sort)
            elif e_option == "e_prank_on": # Prank mode on
                print(f"Scheduling prank mode on at {request.form.get('e_time')}", flush=True, file=sys.stderr)
                job = schedule.every().day.at(request.form.get("e_time")).do(prank_on)
                jobs.append((job.at_time, f"Prank mode ON at {job.at_time}", job))
                jobs.sort(key=jobs_sort)
        elif manage_e_option == "remove_event": # Removing an event
            print("Deleting event", file=sys.stderr, flush=True)
            to_delete_str = request.form.get("events")
            print(to_delete_str, file=sys.stderr, flush=True)

            # Find the job we are attempting to remove
            to_delete = None
            for j in jobs:
                if j[1] == to_delete_str:
                    to_delete = j
                    break

            # If found, delete the job
            if to_delete:
                jobs.remove(to_delete)
                schedule.cancel_job(to_delete[2])

    else: # Doing immediate action
        print("Making change", file=sys.stderr, flush=True)
        if option == "light_on":
            light_on()
        elif option == "light_off":
            light_off()
        elif option == "prank_on":
            prank_on()

    # Redirect back to the form
    return redirect(url_for('control'))

# Display all jobs in a nice manner
@app.route("/events")
def events():
    return str(pretty_jobs(jobs))


if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Attempt to retrieve the current ip. Loops until there is an IP to display
    while True:
        try:
            s.connect(('8.8.8.8', 1))
            break
        except OSError:
            print("[Server] ERROR: Unable to get ip. Retry in 10", flush=True, file=sys.stderr)
            time.sleep(10)

    ip = s.getsockname()[0]
    print(ip, flush=True, file=sys.stderr)
    send_ip(ip) # Send the ip to the linked program

    app.run(debug=False, host='0.0.0.0') # Start the server
