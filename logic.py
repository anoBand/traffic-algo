# logic.py
import random
import time
import math

class Vehicle:
    def __init__(self, vehicle_id, direction, turn_type, lane_mode, config, debug=False):
        self.id = vehicle_id
        self.direction = direction # 'N', 'S', 'E', 'W'
        self.turn_type = turn_type # 'S', 'L', 'R'
        
        if lane_mode == "SPLIT":
            if turn_type == 'L': self.lane = 0
            elif turn_type == 'R': self.lane = 1
            else: self.lane = 1 # Straight: Outer lane when left is dedicated
        else: # SHARED
            if turn_type == 'L': self.lane = 0 # Left turns stay inner
            elif turn_type == 'R': self.lane = 1 # Right turns stay outer
            else: self.lane = random.choice([0, 1]) # Straight can use both
        
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
        self.has_stopped_at_red = False # For Right Turn Stop-and-Go
        self.center = config['center']

    def set_initial_position(self, direction, config):
        cx, cy = config['center']
        offsets = [20, 55] 
        off = offsets[self.lane]

        if direction == 'N': return cx - off, -30 
        if direction == 'S': return cx + off, 830 
        if direction == 'E': return 830, cy - off 
        if direction == 'W': return -30, cy + off 
        return 0, 0

    def move(self, is_green, lead_vehicle, stop_line, delta_t, time_scale, conflicting_vehicles=None):
        if self.exit_time: return
        current_speed = self.base_speed * time_scale
        can_move = True
        dist_to_stop = self.get_distance_to_stop(stop_line)

        # 신호 제어 (범위를 0~60으로 확장하여 정지선 앞 정지 시에도 로직 작동)
        if 0 <= dist_to_stop < 60 and not self.has_turned:
            if not is_green:
                if self.turn_type == 'R':
                    # 우회전 빨간불: 일시 정지 후 주행 가능 (Stop-and-Go)
                    if not self.has_stopped_at_red:
                        if dist_to_stop < 10:
                            can_move = False
                            self.reaction_timer += delta_t * time_scale
                            if self.reaction_timer > 1.2: # 1.2초 완전 정지
                                self.has_stopped_at_red = True
                                self.reaction_timer = 0.0
                        else:
                            # 정지선 가까이 서서히 접근
                            current_speed *= 0.6
                    else:
                        # 일시정지 완료 후 충돌 체크
                        if self.is_conflicting(conflicting_vehicles):
                            can_move = False
                else:
                    can_move = False
                    self.waiting_for_green = True
                    self.reaction_timer = 0.0
            elif is_green:
                if self.waiting_for_green:
                    if lead_vehicle is None or self.get_distance_to_lead(lead_vehicle) > self.length + 10:
                        if self.reaction_timer < 1.0:
                            can_move = False
                            self.reaction_timer += delta_t * time_scale
                        else:
                            self.waiting_for_green = False
                    else:
                        self.waiting_for_green = False
                # 초록불일 때 우회전은 일시정지 없이 진행
                if self.turn_type == 'R': self.has_stopped_at_red = True

        # 앞차 간격
        if lead_vehicle and self.get_distance_to_lead(lead_vehicle) < self.length + 8:
            can_move = False

        if can_move:
            self.stopped = False
            cx, cy = self.center
            # ... (궤적 로직 생략)
            
            # 궤적 로직 (RHT)
            if not self.has_turned:
                turn_trigger = False
                # 좌회전 궤적 (안쪽 -> 바깥쪽)
                if self.turn_type == 'L':
                    if self.direction == 'N' and self.y > cy + 20: turn_trigger = True
                    elif self.direction == 'S' and self.y < cy - 20: turn_trigger = True
                    elif self.direction == 'E' and self.x < cx - 20: turn_trigger = True
                    elif self.direction == 'W' and self.x > cx + 20: turn_trigger = True
                    
                    if turn_trigger:
                        self.has_turned = True
                        if self.direction == 'N': self.y = cy + 55; self.x = cx + 20
                        elif self.direction == 'S': self.y = cy - 55; self.x = cx - 20
                        elif self.direction == 'E': self.x = cx - 55; self.y = cy + 20
                        elif self.direction == 'W': self.x = cx + 55; self.y = cy - 20

                # 우회전 궤적 (바깥쪽 -> 바깥쪽)
                elif self.turn_type == 'R':
                    if self.direction == 'N' and self.y > cy - 55: turn_trigger = True
                    elif self.direction == 'S' and self.y < cy + 55: turn_trigger = True
                    elif self.direction == 'E' and self.x < cx + 55: turn_trigger = True
                    elif self.direction == 'W' and self.x > cx - 55: turn_trigger = True

                    if turn_trigger:
                        self.has_turned = True
                        if self.direction == 'N': self.y = cy - 20; self.x = cx - 55
                        elif self.direction == 'S': self.y = cy + 20; self.x = cx + 55
                        elif self.direction == 'E': self.x = cx + 20; self.y = cy - 55
                        elif self.direction == 'W': self.x = cx - 20; self.y = cy + 55
            
            if not self.has_turned:
                if self.direction == 'N': self.y += current_speed
                if self.direction == 'S': self.y -= current_speed
                if self.direction == 'E': self.x -= current_speed
                if self.direction == 'W': self.x += current_speed
            else:
                # 회전 후 주행 방향 (RHT)
                if self.turn_type == 'L':
                    if self.direction == 'N': self.x += current_speed
                    elif self.direction == 'S': self.x -= current_speed
                    elif self.direction == 'E': self.y += current_speed
                    elif self.direction == 'W': self.y -= current_speed
                else: # Right Turn
                    if self.direction == 'N': self.x -= current_speed
                    elif self.direction == 'S': self.x += current_speed
                    elif self.direction == 'E': self.y -= current_speed
                    elif self.direction == 'W': self.y += current_speed
        else:
            self.stopped = True
            self.wait_time += delta_t * time_scale

        if self.x < -100 or self.x > 900 or self.y < -100 or self.y > 900:
            self.exit_time = time.time()

    def is_conflicting(self, vehicles):
        if not vehicles: return False
        # 우회전 진입 시 충돌 가능성 체크
        for v in vehicles:
            if v.id == self.id: continue
            # 같은 방향(Approach)에서 오는 차량은 무시 (뒤따르는 차에 의한 블로킹 방지)
            if v.direction == self.direction and not v.has_turned: continue
            
            # 교차로 내 핵심 영역에 있는 차량과의 거리 체크
            dist = self.get_distance_to_lead(v)
            if dist < 85: return True
        return False

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
            v.move(is_green, lead, self.stop_lines[v.direction], delta_t, self.time_scale, conflicting_vehicles=self.vehicles)
            
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
            turn_type = random.choice(['S', 'L', 'R'])
            new_v = Vehicle(self.vehicle_counter, direction, turn_type, self.lane_mode, {'center': self.center})
            self.vehicles.append(new_v)
            self.vehicle_counter += 1
            self.next_spawn_time = self.simulated_time + (0.05 / self.spawn_rate) + random.uniform(-0.1, 0.1)
