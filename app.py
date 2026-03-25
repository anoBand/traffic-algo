# app.py
import tkinter as tk
from tkinter import ttk, messagebox
import time
from logic import TrafficEngine

class TrafficSimApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Traffic Phase B: Split-Phase RHT")
        self.root.geometry("1200x850")

        self.duration_var = tk.DoubleVar(value=30.0)
        self.spawn_rate_var = tk.DoubleVar(value=0.04)
        self.scale_var = tk.DoubleVar(value=1.0)
        self.lane_mode_var = tk.StringVar(value="SHARED")
        self.signal_mode_var = tk.StringVar(value="SIMULTANEOUS") 
        self.target_var = tk.IntVar(value=500)

        self.setup_ui()
        self.reset_simulation()
        self.update_loop()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(main_frame, width=800, height=800, bg="#2c3e50")
        self.canvas.pack(side=tk.LEFT, padx=10)

        ctrl = ttk.LabelFrame(main_frame, text="Simulation Controls", padding="15")
        ctrl.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        ttk.Label(ctrl, text="Lane Configuration:").pack(anchor=tk.W)
        ttk.Radiobutton(ctrl, text="Split (Dedicated Left)", variable=self.lane_mode_var, value="SPLIT").pack(anchor=tk.W)
        ttk.Radiobutton(ctrl, text="Shared (Left+Straight)", variable=self.lane_mode_var, value="SHARED").pack(anchor=tk.W)
        
        ttk.Label(ctrl, text="\nSignal Phasing (RHT):").pack(anchor=tk.W)
        ttk.Radiobutton(ctrl, text="Sequential (S then L)", variable=self.signal_mode_var, value="SEQUENTIAL").pack(anchor=tk.W)
        ttk.Radiobutton(ctrl, text="Simultaneous (Protected Approach)", variable=self.signal_mode_var, value="SIMULTANEOUS").pack(anchor=tk.W)

        ttk.Separator(ctrl, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        ttk.Label(ctrl, text="Signal Duration (s):").pack(anchor=tk.W)
        ttk.Scale(ctrl, from_=10, to=100, variable=self.duration_var, orient=tk.HORIZONTAL).pack(fill=tk.X)
        self.dur_label = ttk.Label(ctrl, text="30.0s")
        self.dur_label.pack()

        ttk.Label(ctrl, text="\nTraffic Density:").pack(anchor=tk.W)
        ttk.Scale(ctrl, from_=0.01, to=0.15, variable=self.spawn_rate_var, orient=tk.HORIZONTAL).pack(fill=tk.X)
        self.spawn_label = ttk.Label(ctrl, text="0.04")
        self.spawn_label.pack()

        ttk.Label(ctrl, text="\nSimulation Speed:").pack(anchor=tk.W)
        ttk.Scale(ctrl, from_=0.5, to=10.0, variable=self.scale_var, orient=tk.HORIZONTAL).pack(fill=tk.X)
        self.scale_label = ttk.Label(ctrl, text="1.0x")
        self.scale_label.pack()

        self.play_btn = ttk.Button(ctrl, text="▶ Play", command=self.toggle_play)
        self.play_btn.pack(fill=tk.X, pady=10)
        ttk.Button(ctrl, text="🔄 Reset", command=self.reset_simulation).pack(fill=tk.X)

        stats = ttk.LabelFrame(ctrl, text="Status", padding="10")
        stats.pack(fill=tk.X, pady=20)
        self.passed_label = ttk.Label(stats, text="Passed: 0")
        self.passed_label.pack(anchor=tk.W)
        self.wait_label = ttk.Label(stats, text="Avg Wait: 0.00s")
        self.wait_label.pack(anchor=tk.W)
        self.phase_label = ttk.Label(stats, text="Phase: N_SL", foreground="#f1c40f", font=("Arial", 11, "bold"))
        self.phase_label.pack(anchor=tk.W, pady=5)

    def draw_base_map(self):
        self.canvas.delete("all")
        # Roads (2 lanes each way)
        self.canvas.create_rectangle(300, 0, 500, 800, fill="#34495e", outline="")
        self.canvas.create_rectangle(0, 300, 800, 500, fill="#34495e", outline="")
        
        # Lane Dividers (RHT)
        for i in range(0, 800, 40):
            if not (300 <= i <= 500):
                self.canvas.create_line(400, i, 400, i+20, fill="#f1c40f", width=2)
                self.canvas.create_line(i, 400, i+20, 400, fill="#f1c40f", width=2)
                self.canvas.create_line(350, i, 350, i+20, fill="white", dash=(5,5)) # N bound lane
                self.canvas.create_line(450, i, 450, i+20, fill="white", dash=(5,5)) # S bound lane
                self.canvas.create_line(i, 350, i+20, 350, fill="white", dash=(5,5)) # W bound lane
                self.canvas.create_line(i, 450, i+20, 450, fill="white", dash=(5,5)) # E bound lane

        # Stop lines (Incoming lanes only)
        self.canvas.create_line(300, 300, 400, 300, fill="white", width=4) # N
        self.canvas.create_line(400, 500, 500, 500, fill="white", width=4) # S
        self.canvas.create_line(500, 300, 500, 400, fill="white", width=4) # E
        self.canvas.create_line(300, 400, 300, 500, fill="white", width=4) # W

        # Signal UI
        self.light_uis = {}
        # Place signals on the FAR side of each approach
        self.draw_signal_box('N', 310, 510) 
        self.draw_signal_box('S', 430, 240) 
        self.draw_signal_box('E', 240, 310) 
        self.draw_signal_box('W', 510, 430) 

    def draw_signal_box(self, direction, x, y):
        self.canvas.create_rectangle(x, y, x+60, y+20, fill="#1c2833", outline="white", width=1)
        self.light_uis[f'{direction}_R'] = self.canvas.create_oval(x+2, y+2, x+14, y+18, fill="#f00")
        self.light_uis[f'{direction}_Y'] = self.canvas.create_oval(x+17, y+2, x+29, y+18, fill="#440")
        self.light_uis[f'{direction}_L'] = self.canvas.create_text(x+38, y+10, text="←", fill="#040", font=("Arial", 10, "bold"))
        self.light_uis[f'{direction}_S'] = self.canvas.create_oval(x+47, y+2, x+59, y+18, fill="#040")

    def toggle_play(self):
        self.engine.is_running = not self.engine.is_running
        self.play_btn.config(text="Pause" if self.engine.is_running else "Play")

    def reset_simulation(self):
        self.engine = TrafficEngine(
            duration=self.duration_var.get(),
            target_count=self.target_var.get(),
            time_scale=self.scale_var.get(),
            spawn_rate=self.spawn_rate_var.get(),
            lane_mode=self.lane_mode_var.get(),
            signal_mode=self.signal_mode_var.get()
        )
        self.draw_base_map()

    def update_loop(self):
        self.dur_label.config(text=f"{self.duration_var.get():.1f}s")
        self.spawn_label.config(text=f"{self.spawn_rate_var.get():.3f}")
        self.scale_label.config(text=f"{self.scale_var.get():.1f}x")
        if self.engine.is_running:
            self.engine.time_scale = self.scale_var.get()
            self.engine.spawn_rate = self.spawn_rate_var.get()
            finished = self.engine.step(0.02)
            self.render()
            if finished:
                self.engine.is_running = False
                messagebox.showinfo("Done", "Simulation Finished")
                self.reset_simulation()
        self.root.after(20, self.update_loop)

    def render(self):
        self.canvas.delete("vehicle")
        cur_phase = self.engine.phases[self.engine.current_phase_idx]
        yellow, all_red = self.engine.in_yellow, self.engine.in_all_red
        
        # Reset all lights to RED
        for d in ['N', 'S', 'E', 'W']:
            self.canvas.itemconfig(self.light_uis[f'{d}_R'], fill="#f00")
            self.canvas.itemconfig(self.light_uis[f'{d}_Y'], fill="#440")
            self.canvas.itemconfig(self.light_uis[f'{d}_L'], fill="#040")
            self.canvas.itemconfig(self.light_uis[f'{d}_S'], fill="#040")

        if not all_red:
            active_dirs, active_types = [], []
            if self.engine.signal_mode == "SEQUENTIAL":
                if cur_phase == "NS_S": active_dirs, active_types = ['N', 'S'], ['S']
                elif cur_phase == "NS_L": active_dirs, active_types = ['N', 'S'], ['L']
                elif cur_phase == "EW_S": active_dirs, active_types = ['E', 'W'], ['S']
                elif cur_phase == "EW_L": active_dirs, active_types = ['E', 'W'], ['L']
            else: # SIMULTANEOUS (Approach-based Split Phase)
                if cur_phase == "NORTH_SL": active_dirs, active_types = ['N'], ['S', 'L']
                elif cur_phase == "SOUTH_SL": active_dirs, active_types = ['S'], ['S', 'L']
                elif cur_phase == "EAST_SL": active_dirs, active_types = ['E'], ['S', 'L']
                elif cur_phase == "WEST_SL": active_dirs, active_types = ['W'], ['S', 'L']

            for d in active_dirs:
                self.canvas.itemconfig(self.light_uis[f'{d}_R'], fill="#400") # Red OFF
                if yellow:
                    self.canvas.itemconfig(self.light_uis[f'{d}_Y'], fill="yellow")
                else:
                    for t in active_types:
                        self.canvas.itemconfig(self.light_uis[f'{d}_{t}'], fill="#0f0" if t == 'L' else "green")

        # Vehicles
        for v in self.engine.vehicles:
            # Base color by turn type
            if v.turn_type == 'S': base_color = "#3498db"
            elif v.turn_type == 'L': base_color = "#9b59b6"
            else: base_color = "#e67e22" # Right Turn (R)

            # Color change based on wait time
            if v.wait_time > 25: color = "#c0392b" # Dark Red (Urgent)
            elif v.wait_time > 10: color = "#f39c12" # Orange/Yellow (Alert)
            else: color = base_color

            self.canvas.create_rectangle(v.x-10, v.y-10, v.x+10, v.y+10, fill=color, outline="white", tags="vehicle")
            
            # Direction indicators: L, R (Straight has no indicator)
            indicator = ""
            if v.turn_type == 'L': indicator = "L"
            elif v.turn_type == 'R': indicator = "R"
            
            if indicator:
                self.canvas.create_text(v.x, v.y, text=indicator, fill="white", font=("Arial", 9, "bold"), tags="vehicle")

        avg_wait = self.engine.total_wait_time / max(1, self.engine.passed_count)
        self.passed_label.config(text=f"Passed: {self.engine.passed_count}")
        self.wait_label.config(text=f"Avg Wait: {avg_wait:.2f}s")
        self.phase_label.config(text=f"Phase: {cur_phase}{' (Y)' if yellow else ''}{' (AR)' if all_red else ''}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TrafficSimApp(root)
    root.mainloop()
