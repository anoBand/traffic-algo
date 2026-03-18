# logic.py
import random
import time
import csv
import os


class TrafficLight:
    def __init__(self, duration):
        self.state = "GREEN"  # GREEN, YELLOW, RED
        self.timer = 0
        self.duration = duration
        self.yellow_duration = max(1.5, duration * 0.1)
        self.red_duration = duration + self.yellow_duration

    def update(self, delta_t, time_scale):
        self.timer += delta_t * time_scale
        current_limit = self.duration if self.state == "GREEN" else (
            self.yellow_duration if self.state == "YELLOW" else self.red_duration)

        if self.timer >= current_limit:
            self.timer = 0
            if self.state == "GREEN":
                self.state = "YELLOW"
            elif self.state == "YELLOW":
                self.state = "RED"
            elif self.state == "RED":
                self.state = "GREEN"


class Vehicle:
    def __init__(self, vehicle_id, direction, lane_config):
        self.id = vehicle_id
        self.direction = direction
        self.spawn_time = time.time()
        self.exit_time = None
        self.wait_time = 0
        self.base_speed = 2.5
        self.length = 25
        self.stopped = False
        self.x, self.y = self.set_initial_position(direction, lane_config)

    def set_initial_position(self, direction, config):
        cx, cy = config['center']
        off = config['offset']
        side_mult = 1 if config['side'] == 'RHT' else -1
        if direction == 'N': return cx + (off * side_mult), -30
        if direction == 'S': return cx - (off * side_mult), 830
        if direction == 'E': return -30, cy - (off * side_mult)
        if direction == 'W': return 830, cy + (off * side_mult)
        return 0, 0

    def move(self, traffic_light_state, lead_vehicle, stop_line, delta_t, time_scale):
        if self.exit_time: return
        current_speed = self.base_speed * time_scale
        can_move = True
        dist_to_stop = self.get_distance_to_stop(stop_line)

        if 5 < dist_to_stop < 50:
            if traffic_light_state in ["RED", "YELLOW"]:
                can_move = False

        if lead_vehicle:
            dist_to_lead = self.get_distance_to_lead(lead_vehicle)
            safe_dist = self.length + (15 * time_scale)
            if dist_to_lead < safe_dist:
                can_move = False

        if can_move:
            self.stopped = False
            if self.direction == 'N': self.y += current_speed
            if self.direction == 'S': self.y -= current_speed
            if self.direction == 'E': self.x += current_speed
            if self.direction == 'W': self.x -= current_speed
        else:
            self.stopped = True
            # 대기 시간에 실제 경과 시간(delta_t * time_scale)을 더해 '초' 단위로 통일
            self.wait_time += delta_t * time_scale

        if self.x < -100 or self.x > 900 or self.y < -100 or self.y > 900:
            self.exit_time = time.time()

    def get_distance_to_stop(self, stop_line):
        if self.direction == 'N': return stop_line - self.y
        if self.direction == 'S': return self.y - stop_line
        if self.direction == 'E': return stop_line - self.x
        if self.direction == 'W': return self.x - stop_line
        return 999

    def get_distance_to_lead(self, lead):
        if self.direction in ['N', 'S']: return abs(self.y - lead.y)
        return abs(self.x - lead.x)


class SimulationEngine:
    def __init__(self, duration, target_count, time_scale, spawn_rate=0.02):
        self.duration = duration
        self.target_count = target_count
        self.time_scale = time_scale
        self.spawn_rate = spawn_rate
        self.passed_count = 0
        self.total_wait_time = 0
        self.vehicles = []
        self.vehicle_counter = 0
        self.is_running = False

        self.light_ns = TrafficLight(duration)
        self.light_ew = TrafficLight(duration)
        self.light_ew.state = "RED"
        self.light_ew.timer = 0

        self.center = (400, 400)
        self.stop_lines = {'N': 300, 'S': 500, 'E': 300, 'W': 500}

    def spawn_vehicle(self):
        if random.random() < (self.spawn_rate * self.time_scale):
            direction = random.choice(['N', 'S', 'E', 'W'])
            config = {'center': self.center, 'offset': 40, 'side': 'RHT'}
            new_v = Vehicle(self.vehicle_counter, direction, config)
            self.vehicles.append(new_v)
            self.vehicle_counter += 1

    def step(self, delta_t=0.05):
        if not self.is_running: return False

        self.light_ns.update(delta_t, self.time_scale)
        self.light_ew.update(delta_t, self.time_scale)

        active_vehicles = []
        for v in self.vehicles:
            if v.exit_time:
                self.passed_count += 1
                self.total_wait_time += v.wait_time
                continue

            lead = next((other for other in reversed(active_vehicles) if other.direction == v.direction), None)
            l_state = self.light_ns.state if v.direction in ['N', 'S'] else self.light_ew.state
            # delta_t를 move 함수에 전달
            v.move(l_state, lead, self.stop_lines[v.direction], delta_t, self.time_scale)
            active_vehicles.append(v)

        self.vehicles = active_vehicles
        self.spawn_vehicle()
        return self.passed_count >= self.target_count

    def save_to_csv(self):
        filename = "traffic_results.csv"
        file_exists = os.path.isfile(filename)
        avg_wait = self.total_wait_time / max(1, self.passed_count)

        with open(filename, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "Signal Duration (s)", "Target Count", "Avg Wait Time (s)"])
            writer.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                self.duration,
                self.passed_count,
                f"{avg_wait:.2f}"
            ])
        return filename
