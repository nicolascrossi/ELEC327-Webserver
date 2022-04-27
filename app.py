from datetime import datetime
from typing import List, Tuple

from flask import Flask, render_template, request, redirect, url_for
import schedule
import time
import threading
import socket

app = Flask(__name__)

# [(time, str rep, job object), ...]
jobs: List[Tuple[datetime.time, str, schedule.Job]] = []


def send_ip(ip: str):
    print(f"Sending ip: {ip}")
    # TODO: Send the given string to the msp and have it be displayed


def light_off():
    print("light off")
    # TODO: Tell the msp430 to turn off the light


def light_on():
    print("light on")
    # TODO: Tell the msp430 to turn on the light


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
                pass
                print(f"Scheduling on at {request.form.get('e_time')}")
                job = schedule.every().day.at(request.form.get("e_time")).do(light_on)
                jobs.append((job.at_time, f"On at {job.at_time}", job))
                jobs.sort(key=jobs_sort)
            elif e_option == "e_light_off":
                pass
                print(f"Scheduling off at {request.form.get('e_time')}")
                job = schedule.every().day.at(request.form.get("e_time")).do(light_off)
                jobs.append((job.at_time, f"Off at {job.at_time}", job))
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

    return redirect(url_for('control'))


@app.route("/events")
def events():
    return str(jobs)


if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0')
    send_ip(socket.gethostbyname(socket.gethostname()))
    app.run(debug=True)
