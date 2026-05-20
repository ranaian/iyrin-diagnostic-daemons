"""
    Iyr Daemon "AW" monitors laptop battery amps and watts in a Linux environment.
    It continuously reads and logs battery information and power state changes and anomalies.
    It has its own unique log file and shares a common event log with other Iyrin to compile
    a log of power-related events and anomalies for later analysis. 
    The unique log file is bounded by a circular buffer to limit disk usage while providing a 
    window of recent data for analysis.
    The event log is unbounded, but generates relatively few entries and includes the current date
    in the filename to create a new log file each day, limiting the size of individual event logs.
    If your event logs are growing too large, you probably don't need to be monitoring your power 
    data at this level of detail, but you can adjust the interval of the checkin log to reduce the 
    number of "useless" events being logged
    Copyright (C) 2026  Ranaian

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import threading
import time
import os
from datetime import datetime


def get_battery_info(bat_id):
    """Reads battery information from the system's power supply interface
       assumes a Linux system with battery info available under /sys/class/power_supply/BAT*
    """

    base_path = f"/sys/class/power_supply/{bat_id}"
    if not os.path.exists(base_path):
        return None
    try:
        def read_file(filename, default_val="0"):
            try:
                with open(os.path.join(base_path, filename), 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except OSError:
                return default_val

        status = read_file("status", default_val="N/A")
        current = read_file("current_now")
        power = read_file("power_now")

        return {
            "Name": bat_id,
            "Status": status,
            "Current": (int(current) // 1000) if current.isdigit() else 0,
            "Power": (int(power) // 1000) if power.isdigit() else 0,

        }
    except OSError as e:
        print(f"Error reading battery info: {e}")
        return None


def log_event(event_file, message):
    """Logs an event message to the specified event log file with a timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-2]
    with open(event_file, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp} - {message}\n")


def log_battery_info(tar_dir, interval=0.01, max_rows=500):
    """Main function of the daemon - 
       - defines log files 
       - initializes log file with headers and empty rows
       - initializes event log file
       - continuously reads battery info and logs to the main log file in a circular buffer 
       with gap line to increase readability
       - detects certain events such as AC power state changes and unusual battery behavior 
       and appends them to the event log file
       """
    # unique log file for this daemon
    iyr_aw_log = os.path.join(tar_dir, "iyr_aw_log.csv")
    # shared event log for all iyr daemons to log events and anomalies together
    iyr_event_log = os.path.join(
        tar_dir, f"iyr_event_log_{datetime.now().strftime('%Y-%m-%d')}.csv")
    row_size = 100
    header_str = "Time,ActBat,BAT0_S,BAT0_A,BAT0_W,BAT1_S,BAT1_A,BAT1_W"
    headers = header_str.ljust(row_size-1) + "\n"

    if not os.path.exists(iyr_aw_log):
        with open(iyr_aw_log, 'w', newline='', encoding='utf-8') as csvfile:
            csvfile.write(headers)
            empty_line = ''.ljust(row_size-1) + '\n'
            for _ in range(max_rows):
                csvfile.write(empty_line)

    if not os.path.exists(iyr_event_log):
        with open(iyr_event_log, 'w', newline='', encoding='utf-8') as eventfile:
            eventfile.write("Timestamp - Event Description\n")

    last_time = time.time()

    print(
        f"Starting Iyr Daemon \"AW\" - Amperage and Wattage\n"
        f"Logging battery info to {iyr_aw_log} every {interval} seconds")
    log_event(iyr_event_log, "Iyr Daemon \"AW\" - Amperage and Wattage - Initialized at " +
              datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")[:-2])

    # last_bat0_pct = None
    # last_ac_state = None

    with open(iyr_aw_log, 'rb+', buffering=0) as csvfile:
        current_row = 0

        while True:
            bat0 = get_battery_info("BAT0")
            bat1 = get_battery_info("BAT1")
            ac_online = "0" if (bat0 and bat0["Status"] == "Discharging") or (
                bat1 and bat1["Status"] == "Discharging") else "1"
            active = "None"
            if bat0 and bat0["Status"] == "Discharging":
                active = "Bat0"
            elif bat1 and bat1["Status"] == "Discharging":
                active = "Bat1"
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-2]

            # disabled due to overlap with Iyr "VC"

            # Detect AC power state changes and log as events
            # if last_ac_state is not None and ac_online != last_ac_state:
            #     log_event(
            #         iyr_event_log, f"AC State Change: "
            #         f"{'Connected' if ac_online == '1' else 'Disconnected'} at {timestamp}")
            # last_ac_state = ac_online

            # detect battery crosstalk and log as events
            # if bat0 and bat1:
            #     if bat0["Power"] == 0.0 and abs(bat1["Current"] - (bat0["Current"])) < 150:
            #         if last_bat0_pct != 0.0:
            #             log_event(
            #                 iyr_event_log, f"Battery Crosstalk detected: "
            #                 f"BAT0 reporting 0% with Current rail bleed ({bat0["Current"]}mV) "
            #                 f"with BAT1 reporting {bat1["Power"]}% and {bat1["Current"]}mV "
            #                 f"at {timestamp}")

            #     if last_bat0_pct is not None and (last_bat0_pct - bat0["Power"] > 10):
            #         log_event(
            #             iyr_event_log, f"Sudden drop in BAT0 charge detected: "
            #             f"from {last_bat0_pct}% to {bat0["Power"]}% at {timestamp}")

            #     last_bat0_pct = bat0["Power"]

            # periodically log battery info as event
            if time.time() - last_time >= 300:
                b0a = bat0["Current"] if bat0 else "N/A"
                b0w = bat0["Power"] if bat0 else "N/A"
                b1a = bat1["Current"] if bat1 else "N/A"
                b1w = bat1["Power"] if bat1 else "N/A"
                log_event(
                    iyr_event_log, f"System Current Stable at {timestamp}:"
                    f" AC : {ac_online}, active : {active}, "
                    f"BAT0 : {b0a}mA, BAT1 : {b1a}mA, "
                    f"BAT0 : {b0w}mW, BAT1 : {b1w}mW")
                last_time = time.time()

            data_line = (f"{timestamp},{active},"
                         f"{bat0['Status'] if bat0 else 'N/A'},"
                         f"{bat0['Current'] if bat0 else '0'},"
                         f"{bat0['Power'] if bat0 else 'N/A'},"
                         f"{bat1['Status'] if bat1 else 'N/A'},"
                         f"{bat1['Current'] if bat1 else '0'},"
                         f"{bat1['Power'] if bat1 else 'N/A'}".ljust(
                row_size-1) + '\n')
            # data_line = data_str.ljust(row_size-1) + '\n'
            csvfile.seek((current_row+1) * row_size)
            csvfile.write(data_line.encode('ascii'))
            next_row = (current_row + 1) % max_rows
            gap_line = ('' * (row_size - 1) + '\n').encode('ascii')
            csvfile.seek((next_row + 1) * row_size)
            csvfile.write(gap_line)
            os.fsync(csvfile.fileno())
            current_row = next_row
            time.sleep(interval)


script_dir = os.path.dirname(os.path.abspath(__file__))
# log_destination = os.path.join(script_dir, "iyr_log_Current_Charge.csv")
daemon_thread = threading.Thread(
    target=log_battery_info,
    args=(script_dir, 0.01, 500),
    daemon=True
)
daemon_thread.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping Iyr Daemon \"AW\"...")
