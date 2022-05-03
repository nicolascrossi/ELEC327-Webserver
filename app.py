import datetime
from pickle import TRUE
import sys
from typing import List, Tuple

from flask import Flask, render_template, request, redirect, url_for
import schedule
import time
import threading
import socket
import signal

IP_HDR = "IP_ADDR"
OFF_HDR = "LIGHT_OFF"
ON_HDR = "LIGHT_ON"
PRANK_ON_HDR = "PRANK_ON"

app = Flask(__name__)

# [(time, str rep, job object), ...]
jobs: List[Tuple[datetime.time, str, schedule.Job]] = []


def send_ip(ip: str):
    print(f"{IP_HDR}:{ip}", flush=True)
    print("[SERVER] Sent ip", file=sys.stderr, flush=True)


def light_off():
    print(f"{OFF_HDR}", flush=True)
    print("[SERVER] Sent off", file=sys.stderr, flush=True)


def light_on():
    print(f"{ON_HDR}", flush=True)
    print("[SERVER] Sent on", file=sys.stderr, flush=True)


def prank_on():
    print(f"{PRANK_ON_HDR}", flush=True)
    print("[SERVER] Sent prank on", file=sys.stderr, flush=True)


def jobs_sort(job: Tuple[datetime.time, str, schedule.Job]):
    return job[0]


def pretty_jobs(ugly_jobs: List[Tuple[datetime.time, str, schedule.Job]]):
    return [j[1] for j in ugly_jobs]


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


end_scheduler = run_continuously()


def quit_handler(signum, frame):
    print("Shutting down scheduler...")
    end_scheduler.set()
    exit(0)


signal.signal(signal.SIGINT, quit_handler)


@app.route("/")
def hello_world():
    return render_template("hello.html")


@app.route("/control")
def control():
    return render_template("control.html", set_events=pretty_jobs(jobs))


@app.route("/control_form", methods=['POST'])
def control_form():
    option = request.form.get("options")
    if option == "set_event":
        print("Managing events")
        manage_e_option = request.form.get("e_mod_type")
        if manage_e_option == "add_event":
            print("Adding event")
            e_option = request.form.get("e_options")
            if e_option == "e_light_on":
                print(f"Scheduling on at {request.form.get('e_time')}", flush=True, file=sys.stderr)
                job = schedule.every().day.at(request.form.get("e_time")).do(light_on)
                jobs.append((job.at_time, f"Light ON at {job.at_time}", job))
                jobs.sort(key=jobs_sort)
            elif e_option == "e_light_off":
                print(f"Scheduling off at {request.form.get('e_time')}", flush=True, file=sys.stderr)
                job = schedule.every().day.at(request.form.get("e_time")).do(light_off)
                jobs.append((job.at_time, f"Light OFF at {job.at_time}", job))
                jobs.sort(key=jobs_sort)
            elif e_option == "e_prank_on":
                print(f"Scheduling prank mode on at {request.form.get('e_time')}", flush=True, file=sys.stderr)
                job = schedule.every().day.at(request.form.get("e_time")).do(prank_on)
                jobs.append((job.at_time, f"Prank mode ON at {job.at_time}", job))
                jobs.sort(key=jobs_sort)
        elif manage_e_option == "remove_event":
            print("Deleting event")
            to_delete_str = request.form.get("events")
            print(to_delete_str)

            to_delete = None
            for j in jobs:
                if j[1] == to_delete_str:
                    to_delete = j
                    break

            if to_delete:
                jobs.remove(to_delete)
                schedule.cancel_job(to_delete[2])

    else:
        print("Making change")
        if option == "light_on":
            light_on()
        elif option == "light_off":
            light_off()
        elif option == "prank_on":
            prank_on()

    return redirect(url_for('control'))


@app.route("/events")
def events():
    return str(jobs)


if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        try:
            s.connect(('8.8.8.8', 1))
            break
        except OSError:
            print("[Server] ERROR: Unable to get ip. Retry in 10", flush=True, file=sys.stderr)
            time.sleep(10)

    ip = s.getsockname()[0]
    print(ip, flush=True, file=sys.stderr)
    send_ip(ip)
    app.run(debug=False, host='0.0.0.0')
