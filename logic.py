# logic.py
import random
import time
import math

class Vehicle:
    def __init__(self, vehicle_id, direction, turn_type, lane_mode, config, debug=False):
        self.id = vehicle_id
        self.direction = direction # 'N', 'S', 'E', 'W' (출발 방향)
        self.turn_type = turn_type # 'S' (Straight), 'L' (Left)
        
        if lane_mode == "SPLIT":
            self.lane = 0 if turn_type == 'L' else 1
        else: # SHARED
            self.lane = 0 if turn_type == 'L' else random.choice([0, 1])
        
        self.spawn_time = time.time()
        self.exit_time = None
        self.wait_time = 0.0
        self.base_speed = 2.5
        self.length = 25
        self.stopped = False
        self.x, self.y = self.set_initial_position(direction, config)
        self.reaction_timer = 0.0
        self.waiting_for_green = False
        self.has_turned = False
        self.center = config['center']

    def set_initial_position(self, direction, config):
        cx, cy = config['center']
        # RHT: 진행 방향의 우측 차로 사용
        # lane 0(안쪽/좌회전), lane 1(바깥쪽/직진)
        offsets = [20, 55] 
        off = offsets[self.lane]

        if direction == 'N': return cx - off, -30 # 북->남 (중앙선 왼쪽)
        if direction == 'S': return cx + off, 830 # 남->북 (중앙선 오른쪽)
        if direction == 'E': return 830, cy - off # 동->서 (중앙선 위쪽)
        if direction == 'W': return -30, cy + off # 서->동 (중앙선 아래쪽)
        return 0, 0

    def move(self, is_green, lead_vehicle, stop_line, delta_t, time_scale):
        if self.exit_time: return
        current_speed = self.base_speed * time_scale
        can_move = True
        dist_to_stop = self.get_distance_to_stop(stop_line)

        # 신호 제어
        if 5 < dist_to_stop < 60 and not self.has_turned:
            if not is_green:
                can_move = False
                self.waiting_for_green = True
                self.reaction_timer = 0.0
            elif is_green and self.waiting_for_green:
                if lead_vehicle is None or self.get_distance_to_lead(lead_vehicle) > self.length + 10:
                    if self.reaction_timer < 1.0:
                        can_move = False
                        self.reaction_timer += delta_t * time_scale
                    else:
                        self.waiting_for_green = False
                else:
                    self.waiting_for_green = False

        # 앞차 간격
        if lead_vehicle and self.get_distance_to_lead(lead_vehicle) < self.length + 8:
            can_move = False

        if can_move:
            self.stopped = False
            cx, cy = self.center
            
            # 우측통행 좌회전 궤적 로직
            if self.turn_type == 'L' and not self.has_turned:
                turn_trigger = False
                if self.direction == 'N' and self.y > cy + 20: turn_trigger = True
                elif self.direction == 'S' and self.y < cy - 20: turn_trigger = True
                elif self.direction == 'E' and self.x < cx - 20: turn_trigger = True
                elif self.direction == 'W' and self.x > cx + 20: turn_trigger = True
                
                if turn_trigger:
                    self.has_turned = True
                    # 좌회전 후 타겟 도로의 우측(바깥쪽) 차선으로 진입
                    if self.direction == 'N': self.y = cy + 55 # 북->동 (동서로의 아래쪽 차선)
                    elif self.direction == 'S': self.y = cy - 55 # 남->서 (동서로의 위쪽 차선)
                    elif self.direction == 'E': self.x = cx - 55 # 동->남 (남북로의 왼쪽 차선)
                    elif self.direction == 'W': self.x = cx + 55 # 서->북 (남북로의 오른쪽 차선)
            
            if not self.has_turned:
                if self.direction == 'N': self.y += current_speed
                if self.direction == 'S': self.y -= current_speed
                if self.direction == 'E': self.x -= current_speed
                if self.direction == 'W': self.x += current_speed
            else:
                # 회전 후 주행
                if self.direction == 'N': self.x += current_speed
                elif self.direction == 'S': self.x -= current_speed
                elif self.direction == 'E': self.y += current_speed
                elif self.direction == 'W': self.y -= current_speed
        else:
            self.stopped = True
            self.wait_time += delta_t * time_scale

        if self.x < -100 or self.x > 900 or self.y < -100 or self.y > 900:
            self.exit_time = time.time()

    def get_distance_to_stop(self, stop_line):
        if self.direction == 'N': return stop_line - self.y
        if self.direction == 'S': return self.y - stop_line
        if self.direction == 'E': return self.x - stop_line
        if self.direction == 'W': return stop_line - self.x
        return 999

    def get_distance_to_lead(self, lead):
        return ((self.x - lead.x)**2 + (self.y - lead.y)**2)**0.5

class TrafficEngine:
    def __init__(self, duration, target_count, time_scale, spawn_rate=0.04, 
                 lane_mode="SPLIT", signal_mode="SEQUENTIAL"):
        self.duration = float(duration)
        self.target_count = target_count
        self.time_scale = time_scale
        self.spawn_rate = spawn_rate
        self.lane_mode = lane_mode 
        self.signal_mode = signal_mode 
        
        self.passed_count = 0
        self.total_wait_time = 0.0
        self.vehicles = []
        self.vehicle_counter = 0
        self.is_running = False
        self.simulated_time = 0.0
        self.next_spawn_time = 0.0

        if signal_mode == "SEQUENTIAL":
            self.phases = ["NS_S", "NS_L", "EW_S", "EW_L"]
        else: # SIMULTANEOUS (실제로는 Split Phase: 한 Approach씩 통과)
            self.phases = ["NORTH_SL", "SOUTH_SL", "EAST_SL", "WEST_SL"]
            
        self.current_phase_idx = 0
        self.phase_timer = 0.0
        self.yellow_duration = 3.0
        self.all_red_duration = 2.0
        self.in_yellow = False
        self.in_all_red = False
        self.center = (400, 400)
        self.stop_lines = {'N': 300, 'S': 500, 'E': 500, 'W': 300}

    def step(self, delta_t=0.05):
        if not self.is_running: return False
        step_sim_time = delta_t * self.time_scale
        self.simulated_time += step_sim_time
        self.phase_timer += step_sim_time

        current_limit = self.duration
        if self.in_yellow: current_limit = self.yellow_duration
        elif self.in_all_red: current_limit = self.all_red_duration

        if self.phase_timer >= current_limit:
            self.phase_timer = 0.0
            if not self.in_yellow and not self.in_all_red:
                self.in_yellow = True
            elif self.in_yellow:
                self.in_yellow = False
                self.in_all_red = True
            elif self.in_all_red:
                self.in_all_red = False
                self.current_phase_idx = (self.current_phase_idx + 1) % len(self.phases)

        cur_phase = self.phases[self.current_phase_idx]
        active_vehicles = []
        
        for v in self.vehicles:
            is_green = False
            if not self.in_yellow and not self.in_all_red:
                if self.signal_mode == "SEQUENTIAL":
                    if cur_phase == "NS_S" and v.direction in ['N', 'S'] and v.turn_type == 'S': is_green = True
                    elif cur_phase == "NS_L" and v.direction in ['N', 'S'] and v.turn_type == 'L': is_green = True
                    elif cur_phase == "EW_S" and v.direction in ['E', 'W'] and v.turn_type == 'S': is_green = True
                    elif cur_phase == "EW_L" and v.direction in ['E', 'W'] and v.turn_type == 'L': is_green = True
                else: # SIMULTANEOUS (One Approach Mode)
                    if cur_phase == "NORTH_SL" and v.direction == 'N': is_green = True
                    elif cur_phase == "SOUTH_SL" and v.direction == 'S': is_green = True
                    elif cur_phase == "EAST_SL" and v.direction == 'E': is_green = True
                    elif cur_phase == "WEST_SL" and v.direction == 'W': is_green = True

            lead = next((other for other in reversed(active_vehicles) if other.direction == v.direction and other.lane == v.lane), None)
            v.move(is_green, lead, self.stop_lines[v.direction], delta_t, self.time_scale)
            
            if v.exit_time:
                self.passed_count += 1
                self.total_wait_time += v.wait_time
            else:
                active_vehicles.append(v)

        self.vehicles = active_vehicles
        self.spawn_vehicle()
        return self.passed_count >= self.target_count

    def spawn_vehicle(self):
        if self.simulated_time >= self.next_spawn_time:
            direction = random.choice(['N', 'S', 'E', 'W'])
            turn_type = random.choice(['S', 'L'])
            new_v = Vehicle(self.vehicle_counter, direction, turn_type, self.lane_mode, {'center': self.center})
            self.vehicles.append(new_v)
            self.vehicle_counter += 1
            self.next_spawn_time = self.simulated_time + (0.05 / self.spawn_rate) + random.uniform(-0.1, 0.1)
