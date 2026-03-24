# terminal_runner.py
import time
import csv
from logic import TrafficEngine

def main():
    print("Phase B: Comprehensive Efficiency Investigation (2x2 Matrix)")
    print("Testing Lane Configs (Split vs Shared) and Signal Modes (Seq vs Protected-Simul)")
    
    target_count = 500
    time_scale = 40.0 # Fast simulation
    delta_t = 0.05
    repeats = 3
    
    filename = "phase_b_efficiency_comparison.csv"
    
    # 현실적인 교통 환경 변수
    lane_modes = ["SPLIT", "SHARED"]
    signal_modes = ["SEQUENTIAL", "SIMULTANEOUS"]
    durations = [30, 60, 90] 
    spawn_rates = [0.03, 0.06] # Medium, High

    total_configs = len(lane_modes) * len(signal_modes) * len(durations) * len(spawn_rates)
    config_idx = 0

    print("-" * 85)
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Lane Mode", "Signal Mode", "Spawn Rate", "Duration (s)", "Avg Wait Time (s)"])

    for l_mode in lane_modes:
        for s_mode in signal_modes:
            for s_rate in spawn_rates:
                for dur in durations:
                    config_idx += 1
                    scenario_wait_times = []
                    
                    print(f"[{config_idx}/{total_configs}] {l_mode}-{s_mode} | Spawn: {s_rate}, Dur: {dur}s", end="\r")
                    
                    for run in range(1, repeats + 1):
                        engine = TrafficEngine(
                            duration=float(dur), 
                            target_count=target_count, 
                            time_scale=time_scale, 
                            spawn_rate=float(s_rate),
                            lane_mode=l_mode,
                            signal_mode=s_mode
                        )
                        engine.is_running = True
                        
                        while engine.passed_count < target_count:
                            engine.step(delta_t)
                        
                        avg_wait = engine.total_wait_time / engine.passed_count
                        scenario_wait_times.append(avg_wait)
                    
                    mean_wait = sum(scenario_wait_times) / repeats
                    print(f"[{config_idx}/{total_configs}] {l_mode}-{s_mode} | Spawn: {s_rate}, Dur: {dur}s | Mean Wait: {mean_wait:.2f}s")
                    
                    with open(filename, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([l_mode, s_mode, s_rate, dur, f"{mean_wait:.2f}"])

    print("-" * 85)
    print(f"Phase B Investigation complete. Results saved in {filename}")

if __name__ == "__main__":
    main()
