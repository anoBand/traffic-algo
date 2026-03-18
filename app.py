# app.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
from logic import SimulationEngine


class TrafficSimApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Traffic Signal Algorithm Simulator")
        self.root.geometry("1150x850")

        # UI 변수 초기값 설정 (Logic과 동기화의 원천)
        self.duration_var = tk.DoubleVar(value=20.0)
        self.scale_var = tk.DoubleVar(value=1.0)
        self.target_var = tk.IntVar(value=300)
        self.spawn_rate_var = tk.DoubleVar(value=4.0)  # Default multiplier

        self.setup_ui()
        self.reset_simulation()  # 여기서 UI 변수값으로 엔진이 생성됨
        self.update_loop()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main_frame, width=800, height=800, bg="#2c3e50")
        self.canvas.pack(side=tk.LEFT, padx=10)

        control_frame = ttk.LabelFrame(main_frame, text="Simulation Control Panel", padding="15")
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        # Signal Duration Slider
        ttk.Label(control_frame, text="Signal Duration (Green, sec):").pack(anchor=tk.W, pady=(0, 5))
        self.duration_slider = ttk.Scale(control_frame, from_=5.0, to=30.0, variable=self.duration_var,
                                         orient=tk.HORIZONTAL)
        self.duration_slider.pack(fill=tk.X, pady=(0, 5))
        self.duration_label = ttk.Label(control_frame, text="20.0s")
        self.duration_label.pack(pady=(0, 15))

        # Spawn Multiplier Slider
        ttk.Label(control_frame, text="Spawn Multiplier (스폰 배율):").pack(anchor=tk.W, pady=(0, 5))
        self.spawn_slider = ttk.Scale(control_frame, from_=1.0, to=10.0, variable=self.spawn_rate_var,
                                      orient=tk.HORIZONTAL)
        self.spawn_slider.pack(fill=tk.X, pady=(0, 5))
        self.spawn_label = ttk.Label(control_frame, text="4.0x")
        self.spawn_label.pack(pady=(0, 15))

        # Time Scale Slider
        ttk.Label(control_frame, text="Simulation Speed (Scale):").pack(anchor=tk.W, pady=(0, 5))
        scale_slider = ttk.Scale(control_frame, from_=0.5, to=5.0, variable=self.scale_var, orient=tk.HORIZONTAL)
        scale_slider.pack(fill=tk.X, pady=(0, 5))
        self.scale_label = ttk.Label(control_frame, text="1.0x")
        self.scale_label.pack(pady=(0, 15))

        # Target Count
        ttk.Label(control_frame, text="Target Passed Cars:").pack(anchor=tk.W, pady=(0, 5))
        target_slider = ttk.Scale(control_frame, from_=100, to=1000, variable=self.target_var, orient=tk.HORIZONTAL)
        target_slider.pack(fill=tk.X, pady=(0, 5))
        self.target_label = ttk.Label(control_frame, text="50")
        self.target_label.pack(pady=(0, 15))

        # Buttons
        self.play_btn = ttk.Button(control_frame, text="▶ Play", command=self.toggle_play)
        self.play_btn.pack(fill=tk.X, pady=5)

        ttk.Button(control_frame, text="🔄 Reset Simulation", command=self.reset_simulation).pack(fill=tk.X, pady=5)

        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        self.view_csv_btn = ttk.Button(control_frame, text="📂 View Results (CSV)", command=self.view_csv)
        self.view_csv_btn.pack(fill=tk.X, pady=5)

        # Statistics Display
        stats_frame = ttk.LabelFrame(control_frame, text="Real-time Stats", padding="10")
        stats_frame.pack(fill=tk.X, pady=20)

        self.stats_passed = ttk.Label(stats_frame, text="Passed: 0", font=('Arial', 10, 'bold'))
        self.stats_passed.pack(anchor=tk.W, pady=2)
        self.stats_wait = ttk.Label(stats_frame, text="Avg Wait: 0.00", font=('Arial', 10, 'bold'))
        self.stats_wait.pack(anchor=tk.W, pady=2)

    def draw_base_map(self):
        self.canvas.delete("all")
        self.canvas.create_rectangle(300, 0, 500, 800, fill="#34495e", outline="")
        self.canvas.create_rectangle(0, 300, 800, 500, fill="#34495e", outline="")
        for i in range(0, 800, 40):
            if not (300 <= i <= 500):
                self.canvas.create_line(400, i, 400, i + 20, fill="#ecf0f1", width=2)
                self.canvas.create_line(i, 400, i + 20, 400, fill="#ecf0f1", width=2)

        stops = {'N': (300, 300, 500, 300), 'S': (300, 500, 500, 500),
                 'E': (300, 300, 300, 500), 'W': (500, 300, 500, 500)}
        for d, coords in stops.items():
            self.canvas.create_line(*coords, fill="#f1c40f", width=5)

        self.light_uis = {
            'N': self.canvas.create_oval(510, 260, 540, 290, fill="gray", outline="white", width=2),
            'S': self.canvas.create_oval(260, 510, 290, 540, fill="gray", outline="white", width=2),
            'E': self.canvas.create_oval(260, 260, 290, 290, fill="gray", outline="white", width=2),
            'W': self.canvas.create_oval(510, 510, 540, 540, fill="gray", outline="white", width=2)
        }

    def toggle_play(self):
        self.engine.is_running = not self.engine.is_running
        self.play_btn.config(text="⏸ Pause" if self.engine.is_running else "▶ Play")
        # Disable/Enable sliders during simulation
        state = tk.DISABLED if self.engine.is_running else tk.NORMAL
        self.duration_slider.config(state=state)
        self.spawn_slider.config(state=state)

    def reset_simulation(self, event=None):
        self.engine = SimulationEngine(
            duration=self.duration_var.get(),
            target_count=self.target_var.get(),
            time_scale=self.scale_var.get(),
            spawn_rate=self.spawn_rate_var.get() * 0.005  # Scale multiplier to rate
        )
        self.play_btn.config(text="▶ Play")
        self.duration_slider.config(state=tk.NORMAL)
        self.spawn_slider.config(state=tk.NORMAL)
        self.draw_base_map()

    def view_csv(self):
        filename = "traffic_results.csv"
        if os.path.exists(filename):
            if os.name == 'nt':
                os.startfile(filename)
            else:
                subprocess.call(['open' if os.name == 'posix' else 'xdg-open', filename])
        else:
            messagebox.showwarning("Warning", "No result file found. Run a simulation first.")

    def update_loop(self):
        self.duration_label.config(text=f"{self.duration_var.get():.1f}s")
        self.spawn_label.config(text=f"{self.spawn_rate_var.get():.1f}x")
        self.scale_label.config(text=f"{self.scale_var.get():.1f}x")
        self.target_label.config(text=str(self.target_var.get()))
        self.engine.time_scale = self.scale_var.get()
        self.engine.spawn_rate = self.spawn_rate_var.get() * 0.005 # Scale multiplier to rate

        if self.engine.is_running:
            finished = self.engine.step(delta_t=0.02)
            self.render_objects()
            if finished:
                csv_file = self.engine.save_to_csv()
                avg_wait = self.engine.total_wait_time / max(1, self.engine.passed_count)
                messagebox.showinfo("📊 Result Saved",
                                    f"Simulation Finished!\n\nAvg Wait Time: {avg_wait:.2f} seconds\nResults saved to: {csv_file}")
                self.reset_simulation()
        self.root.after(20, self.update_loop)

    def render_objects(self):
        self.canvas.delete("vehicle")
        ns_color, ew_color = self.engine.light_ns.state.lower(), self.engine.light_ew.state.lower()
        self.canvas.itemconfig(self.light_uis['N'], fill=ns_color)
        self.canvas.itemconfig(self.light_uis['S'], fill=ns_color)
        self.canvas.itemconfig(self.light_uis['E'], fill=ew_color)
        self.canvas.itemconfig(self.light_uis['W'], fill=ew_color)
        avg_wait = self.engine.total_wait_time / max(1, self.engine.passed_count)
        self.stats_passed.config(text=f"Passed: {self.engine.passed_count} / {self.engine.target_count}")
        self.stats_wait.config(text=f"Avg Wait: {avg_wait:.2f}")
        for v in self.engine.vehicles:
            color = "#1abc9c" if v.direction in ['N', 'S'] else "#e67e22"
            if v.stopped: color = "#e74c3c"
            x1, y1, x2, y2 = v.x - 12, v.y - 12, v.x + 12, v.y + 12
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="white", tags="vehicle")


if __name__ == "__main__":
    root = tk.Tk()
    ttk.Style().theme_use('clam')
    app = TrafficSimApp(root)
    root.mainloop()
