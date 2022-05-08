import os
import sys
import time
from datetime import datetime
from datetime import timedelta
from threading import Timer
import random
import copy
import pandas as pd
import plotly.express as px
import math


class Sensor:
    def __init__(self, sensor_name):
        self.sensor_name = sensor_name
        self.last_send_time = None
        self.signal_list = []
        self.last_success = True
        self.send_status = []
        self.delay_time = []

    def update_send_status(self, send_status, delay_time):
        self.send_status.append(send_status)
        self.delay_time.append(delay_time)

    def update_last_sent_time(self, new_sent_time):
        if self.last_success:
            self.last_send_time = new_sent_time
        else:
            return

    def generate_data(self):
        if self.last_send_time:
            self.signal_list.append(self.last_send_time.replace(microsecond=0))
            return self.sensor_name, (datetime.now() - self.last_send_time).total_seconds()
        else:
            self.last_send_time = datetime.now()
            self.signal_list.append(self.last_send_time.replace(microsecond=0))
            return self.sensor_name, 32

    def calculate_delay_time(self, new_receive_time):
        return (new_receive_time - self.last_send_time).total_seconds()

    def calculate_send_rate(self):
        success_time = 0
        total_delay_time = 0
        total_delay_count = 0
        if len(self.send_status) == 0:
            return 0, 0, 0, 0
        for i in range(len(self.send_status)):
            if self.send_status[i]:
                success_time += 1
                if round(self.delay_time[i]) != 0:
                    total_delay_count += 1
                    total_delay_time += self.delay_time[i]
        return len(self.send_status), success_time, total_delay_count, total_delay_time


class System:
    STATUS_ONLINE = "ONLINE"
    STATUS_SLEEP = "SLEEP"

    def __init__(self, live_time_interval, sleep_time_interval):
        self.live_time_interval = live_time_interval
        self.sleep_time_interval = sleep_time_interval
        self.status = None
        self.sensor_data = []
        self.wake_up_time = None
        self.need_exit = False

    def exit_system(self):
        self.need_exit = True

    def run_system(self):
        if not self.need_exit:
            self.wake_up()
            # stay here and wait for sleep
            wake_up_timer = Timer(self.live_time_interval, self.sleep)
            wake_up_timer.start()

            # stay here and wait for wake up
            sleep_timer = Timer(self.live_time_interval + self.sleep_time_interval, self.run_system)
            sleep_timer.start()
        else:
            sys.exit(0)

    def wake_up(self):
        self.status = self.STATUS_ONLINE
        self.wake_up_time = datetime.now()
        write_log_to_file("System Wake Up {}".format(self.wake_up_time.strftime("%m/%d/%Y, %H:%M:%S")))

    def sleep(self):
        write_log_to_file("System go sleep")
        self.status = self.STATUS_SLEEP

    def push_data(self, sensor_data):
        receive_time = datetime.now()
        if self.status == self.STATUS_ONLINE:
            self.sensor_data.append(sensor_data)
            return receive_time
        else:
            return None


def random_bool():
    return bool(random.randint(0, 2))


def simulate_send_receive_data(system: System, sensors, iteration_count, sensor_transmission_interval):
    system.run_system()

    iteration_max = 0
    total_send_time_list = []
    while iteration_max < iteration_count:
        # iterator all sensor and try to push data
        sensor = sensors[random.randint(0, len(sensors) - 1)]
        if random_bool():
            new_data, time_from_last_sent = sensor.generate_data()

            if time_from_last_sent >= sensor_transmission_interval:
                sensor.update_last_sent_time(datetime.now())
                receive_time = system.push_data(new_data)

                if receive_time:
                    delay_time = sensor.calculate_delay_time(new_receive_time=receive_time)
                    write_log_to_file("Send success " + new_data + ", Received time: "
                                      + receive_time.strftime("%m/%d/%Y, %H:%M:%S.%f")[:-3]
                                      + " Delay time: {}".format(round(delay_time, 5)))
                    sensor.update_send_status(True if receive_time else False, delay_time)
                    sensor.last_success = True
                else:
                    sensor.last_success = False
                    sensor.update_send_status(True if receive_time else False, -1)
                    write_log_to_file("Send delay {} due server sleep".format(new_data))
        time.sleep(0.5)
        iteration_max = max([len(s.send_status) for s in sensors])
    master_signal_list = []
    for sensor in sensors:
        write_log_to_file('=' * 50)
        sent_time, success_time, total_delay_count, total_delay_time = sensor.calculate_send_rate()
        write_log_to_file("Sensor name: " + sensor.sensor_name)
        write_log_to_file("Total send data: " + str(sent_time))
        write_log_to_file(
            "Sensor success rate: {}%".format(round(float(success_time) * 100 / sent_time, 2)) if sent_time > 0 else 0)
        write_log_to_file("AVG delay time: " + str(
            round(float(total_delay_time) / total_delay_count, 5) if total_delay_count > 0 else 0))

        sensor_delay_times = copy.deepcopy(sensor.delay_time)
        sensor_delay_times.sort(reverse=True)
        top_delay = [i for i in sensor_delay_times if i > 1]
        master_signal_list.extend(sensor.signal_list)
        if len(top_delay) > 0:
            write_log_to_file("Top 5 worst delay time: " + ", ".join([str(i) for i in top_delay[:5]]))
        else:
            write_log_to_file("Not have delay data.")

    system.exit_system()
    return master_signal_list


output_file_path = 'output.txt'


def remove_olg_logs():
    if os.path.exists(output_file_path):
        os.remove(output_file_path)


def write_log_to_file(str_log):
    print(str_log)
    with open(output_file_path, 'a', encoding='utf8') as f:
        f.write(str(str_log) + '\n')


if __name__ == '__main__':
    num_of_sensors = 32
    system_live_time_interval = 1  # time the system is live
    system_sleep_interval = 2  # sleeping time after sleep
    num_iteration = 5  # when one sensor is reach this iteration, random send data will stop.
    m_sensor_transmission_interval = 32  # min time for 2 time transmit  data of a sensor
    remove_olg_logs()

    write_log_to_file('========================= STARTING ==========================')
    write_log_to_file("Parameters")
    write_log_to_file("Num Of Sensors {}".format(num_of_sensors))
    write_log_to_file("System wake up interval {}".format(system_live_time_interval))
    write_log_to_file("System sleep interval {}".format(system_sleep_interval))
    write_log_to_file("Num iteration {}".format(num_iteration))

    simulation_system = System(live_time_interval=system_live_time_interval, sleep_time_interval=system_sleep_interval)
    simulation_sensors = [Sensor("T" + str(i)) for i in range(num_of_sensors)]
    m_signal_list = simulate_send_receive_data(simulation_system, simulation_sensors, num_iteration,
                                               m_sensor_transmission_interval)

    m_signal_list.sort()
    time_elapsed = int((m_signal_list[-1] - m_signal_list[0]).total_seconds())
    timestamp = pd.date_range(m_signal_list[0], m_signal_list[-1], freq='s')
    # plot
    df1 = pd.DataFrame({'timestamp': m_signal_list,
                        'signal': [1] * len(m_signal_list)})
    df2 = pd.DataFrame({'timestamp': timestamp})
    df3 = pd.merge(df2, df1, on='timestamp',how='left')
    df3 = df3.drop_duplicates(subset='timestamp')
    df3.signal = df3.signal.fillna(0)
    print(df3.head())
    print(df3.tail())
    print(len(df3))
    fig = px.line(df3,x='timestamp',y='signal')
    fig.show()
    write_log_to_file('========================= FINISH ==========================')
