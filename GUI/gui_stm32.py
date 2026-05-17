"""
=============================================================
  GUI STM32F407 - MPU9250 + EEPROM 24C04  (v2)
  Khớp firmware: SAVE / WRITE <addr> <val> / READ <addr>
  Sensor data nhận tự động: X:%d\tY:%d\tZ:%d
  pip install customtkinter pyserial matplotlib
=============================================================
"""
import customtkinter as ctk
import serial, serial.tools.list_ports
import threading, time, re
from collections import deque
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib; matplotlib.use("Agg")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT     = "#378ADD"
SUCCESS    = "#639922"
DANGER     = "#E24B4A"
BG_CARD    = "#1e2130"
BG_DARK    = "#161824"
TEXT_SEC   = "#8892a4"
HISTORY    = 80
ACCEL_SENS = 16384.0


class SerialManager:
    def __init__(self):
        self.ser  = None
        self.lock = threading.Lock()

    def connect(self, port, baud=115200):
        try:
            self.ser = serial.Serial(port, baud, timeout=0.1)
            return True
        except Exception as e:
            print(f"[UART] {e}"); return False

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None

    def send(self, cmd):
        if not self.is_connected: return False
        with self.lock:
            try:
                self.ser.write((cmd + "\r").encode()); return True
            except Exception as e:
                print(f"[send] {e}"); return False

    def readline(self):
        if not self.is_connected: return None
        try:
            ln = self.ser.readline()
            if ln: return ln.decode(errors="ignore").strip()
        except Exception: pass
        return None

    @property
    def is_connected(self):
        return self.ser is not None and self.ser.is_open

    @staticmethod
    def list_ports():
        return [p.device for p in serial.tools.list_ports.comports()]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("STM32F407 – MPU9250 + EEPROM 24C04")
        self.geometry("1200x760")
        self.minsize(960, 600)
        self.configure(fg_color=BG_DARK)

        self.serial  = SerialManager()
        self.reading = False
        self.sample  = 0
        self.t_h     = deque(maxlen=HISTORY)
        self.ax_h    = [deque(maxlen=HISTORY) for _ in range(3)]
        self._raw    = [0, 0, 0]

        self._build_ui()

    # ── UI ──────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=BG_CARD, height=50, corner_radius=0)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="  STM32F407  ·  MPU9250 + EEPROM 24C04",
                     font=("Segoe UI", 15, "bold"), text_color=ACCENT
                     ).pack(side="left", padx=16)
        self.lbl_st = ctk.CTkLabel(hdr, text="● Chưa kết nối",
                                    font=("Segoe UI", 12), text_color=DANGER)
        self.lbl_st.pack(side="right", padx=20)

        # Body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=8)

        # Cột trái — scrollable để EEPROM không bị cắt
        left = ctk.CTkScrollableFrame(body, width=292, fg_color="transparent",
                                       scrollbar_button_color="#2a3040")
        left.pack(side="left", fill="y", padx=(0, 8))

        right = ctk.CTkFrame(body, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        self._left(left)
        self._right(right)

    # ── CỘT TRÁI ────────────────────────────────────────────────
    def _left(self, p):
        # UART
        self._hdr(p, "Kết nối UART")
        r = ctk.CTkFrame(p, fg_color="transparent"); r.pack(fill="x", pady=(0,4))
        ctk.CTkLabel(r, text="COM", width=44, text_color=TEXT_SEC,
                     font=("Segoe UI", 12)).pack(side="left")
        self.cmb_port = ctk.CTkComboBox(r, values=[], width=130, font=("Segoe UI",12))
        self.cmb_port.pack(side="left", padx=4)
        ctk.CTkButton(r, text="↻", width=28, fg_color="transparent",
                      border_width=1, font=("Segoe UI",14),
                      command=self._refresh_ports).pack(side="left", padx=2)

        r2 = ctk.CTkFrame(p, fg_color="transparent"); r2.pack(fill="x", pady=(0,8))
        ctk.CTkLabel(r2, text="Baud", width=44, text_color=TEXT_SEC,
                     font=("Segoe UI",12)).pack(side="left")
        self.cmb_baud = ctk.CTkComboBox(r2, values=["115200","9600","57600","38400"],
                                         width=130, font=("Segoe UI",12))
        self.cmb_baud.set("115200"); self.cmb_baud.pack(side="left", padx=4)

        self.btn_conn = ctk.CTkButton(p, text="Kết nối", fg_color=ACCENT,
                                       font=("Segoe UI",13,"bold"),
                                       command=self._toggle_conn)
        self.btn_conn.pack(fill="x", pady=(0,4))
        self._refresh_ports()
        self._sep(p)

        # Sensor
        self._hdr(p, "Gia tốc kế (cập nhật tự động)")
        info = ctk.CTkFrame(p, fg_color="#1a2540", corner_radius=6)
        info.pack(fill="x", pady=(0,8))
        ctk.CTkLabel(info, text="Firmware gửi X/Y/Z mỗi 100ms\nGUI tự parse, không cần bấm gì",
                     font=("Segoe UI",11), text_color="#5b8fd4",
                     justify="left").pack(padx=8, pady=6, anchor="w")

        g = ctk.CTkFrame(p, fg_color="transparent"); g.pack(fill="x", pady=(0,4))
        g.columnconfigure((0,1,2), weight=1)
        self.lv_ax = self._metric(g, "Accel X", "-- g", 0)
        self.lv_ay = self._metric(g, "Accel Y", "-- g", 1)
        self.lv_az = self._metric(g, "Accel Z", "-- g", 2)

        raw_row = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=6)
        raw_row.pack(fill="x", pady=(0,2))
        ctk.CTkLabel(raw_row, text="Raw int16", font=("Segoe UI",10),
                     text_color=TEXT_SEC).pack(side="left", padx=8, pady=4)
        self.lv_raw = ctk.CTkLabel(raw_row, text="X:0  Y:0  Z:0",
                                    font=("Consolas",10), text_color="#5b8fd4")
        self.lv_raw.pack(side="right", padx=8)
        self._sep(p)

        # EEPROM
        self._hdr(p, "EEPROM 24C04")

        # -- SAVE --
        sv = ctk.CTkFrame(p, fg_color="#192a19", corner_radius=8)
        sv.pack(fill="x", pady=(0,10))
        ctk.CTkLabel(sv, text="Ghi block XYZ → EEPROM",
                     font=("Segoe UI",12,"bold"), text_color="#7acc7a"
                     ).pack(anchor="w", padx=10, pady=(8,2))
        ctk.CTkLabel(sv, text="Ghi accel_X/Y/Z hiện tại (6 byte)\nvào địa chỉ 0x00–0x05",
                     font=("Segoe UI",11), text_color="#5a8f5a", justify="left"
                     ).pack(anchor="w", padx=10)
        ctk.CTkButton(sv, text="SAVE — Lưu XYZ ngay",
                      fg_color=SUCCESS, font=("Segoe UI",12,"bold"),
                      command=self._do_save).pack(fill="x", padx=10, pady=(6,10))

        # -- WRITE --
        ctk.CTkLabel(p, text="Ghi 1 byte", font=("Segoe UI",12,"bold"),
                     text_color=TEXT_SEC).pack(anchor="w", pady=(0,4))
        wr = ctk.CTkFrame(p, fg_color="transparent"); wr.pack(fill="x", pady=(0,4))
        ctk.CTkLabel(wr, text="Addr", width=38, text_color=TEXT_SEC,
                     font=("Segoe UI",11)).pack(side="left")
        self.e_waddr = ctk.CTkEntry(wr, width=62, placeholder_text="08",
                                     font=("Consolas",12))
        self.e_waddr.pack(side="left", padx=4)
        ctk.CTkLabel(wr, text="Data", width=38, text_color=TEXT_SEC,
                     font=("Segoe UI",11)).pack(side="left")
        self.e_wdata = ctk.CTkEntry(wr, width=62, placeholder_text="FF",
                                     font=("Consolas",12))
        self.e_wdata.pack(side="left", padx=4)
        ctk.CTkButton(p, text="WRITE — Ghi byte", fg_color="#185FA5",
                      font=("Segoe UI",12,"bold"),
                      command=self._do_write).pack(fill="x", pady=(0,10))

        # -- READ --
        ctk.CTkLabel(p, text="Đọc 1 byte", font=("Segoe UI",12,"bold"),
                     text_color=TEXT_SEC).pack(anchor="w", pady=(0,4))
        rr = ctk.CTkFrame(p, fg_color="transparent"); rr.pack(fill="x", pady=(0,4))
        ctk.CTkLabel(rr, text="Addr", width=38, text_color=TEXT_SEC,
                     font=("Segoe UI",11)).pack(side="left")
        self.e_raddr = ctk.CTkEntry(rr, width=90, placeholder_text="08",
                                     font=("Consolas",12))
        self.e_raddr.pack(side="left", padx=4)
        ctk.CTkButton(p, text="READ — Đọc byte", fg_color="transparent",
                      border_width=1, font=("Segoe UI",12,"bold"),
                      command=self._do_read).pack(fill="x", pady=(0,14))

    # ── CỘT PHẢI ────────────────────────────────────────────────
    def _right(self, p):
        p.rowconfigure(0, weight=0)   # biểu đồ
        p.rowconfigure(1, weight=1)   # terminal — full còn lại
        p.columnconfigure(0, weight=1)

        # Biểu đồ
        cf = ctk.CTkFrame(p, fg_color=BG_CARD, corner_radius=10)
        cf.grid(row=0, column=0, sticky="ew", pady=(0,8))
        ctk.CTkLabel(cf, text="Biểu đồ Accel  (X=xanh · Y=xanh lá · Z=vàng)",
                     font=("Segoe UI",12,"bold"), text_color=ACCENT
                     ).pack(anchor="w", padx=12, pady=(10,4))

        fig = Figure(figsize=(7, 2.4), dpi=96, facecolor=BG_CARD)
        self.ax_fig = fig.add_subplot(111)
        self.ax_fig.set_facecolor(BG_CARD)
        self.ax_fig.tick_params(colors=TEXT_SEC, labelsize=8)
        self.ax_fig.set_ylabel("g", color=TEXT_SEC, fontsize=9)
        for sp in self.ax_fig.spines.values(): sp.set_edgecolor("#2a3040")
        self.ax_fig.grid(True, color="#2a3040", lw=0.6)
        self.ln = [
            self.ax_fig.plot([], [], color="#378ADD", lw=1.5, label="X")[0],
            self.ax_fig.plot([], [], color="#639922", lw=1.5, label="Y")[0],
            self.ax_fig.plot([], [], color="#EF9F27", lw=1.5, label="Z")[0],
        ]
        self.ax_fig.legend(loc="upper right", fontsize=8,
                            facecolor=BG_CARD, edgecolor="none", labelcolor="white")
        fig.tight_layout(pad=0.8)
        self.canvas = FigureCanvasTkAgg(fig, master=cf)
        self.canvas.get_tk_widget().pack(fill="x", padx=8, pady=(0,10))

        # Terminal — expand=True chiếm hết phần còn lại
        tf = ctk.CTkFrame(p, fg_color=BG_CARD, corner_radius=10)
        tf.grid(row=1, column=0, sticky="nsew")
        tf.rowconfigure(1, weight=1)
        tf.columnconfigure(0, weight=1)

        bar = ctk.CTkFrame(tf, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(10,4))
        ctk.CTkLabel(bar, text="Terminal / Log", font=("Segoe UI",12,"bold"),
                     text_color=ACCENT).pack(side="left")
        self.var_hide = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(bar, text="Ẩn data sensor raw",
                        variable=self.var_hide, font=("Segoe UI",11),
                        text_color=TEXT_SEC).pack(side="left", padx=14)
        ctk.CTkButton(bar, text="Xoá", width=56, fg_color="transparent",
                      border_width=1, font=("Segoe UI",11),
                      command=lambda: self.txt.delete("1.0","end")
                      ).pack(side="right")

        self.txt = ctk.CTkTextbox(tf, font=("Consolas",11),
                                   fg_color=BG_DARK, text_color="#c8d0e0",
                                   wrap="word")
        self.txt.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,8))

    # ── HELPERS ─────────────────────────────────────────────────
    def _hdr(self, p, t):
        ctk.CTkLabel(p, text=t, font=("Segoe UI",13,"bold"),
                     text_color=ACCENT).pack(anchor="w", pady=(10,4))

    def _sep(self, p):
        ctk.CTkFrame(p, height=1, fg_color="#2a3040").pack(fill="x", pady=6)

    def _metric(self, parent, label, init, col):
        f = ctk.CTkFrame(parent, fg_color=BG_DARK, corner_radius=8)
        f.grid(row=0, column=col, padx=(0,4) if col<2 else 0, sticky="ew")
        ctk.CTkLabel(f, text=label, font=("Segoe UI",10),
                     text_color=TEXT_SEC).pack(pady=(6,0))
        lbl = ctk.CTkLabel(f, text=init, font=("Consolas",12,"bold"),
                            text_color="white")
        lbl.pack(pady=(0,6))
        return lbl

    def _log(self, msg, raw=False):
        def _do():
            if raw and self.var_hide.get(): return
            self.txt.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
            self.txt.see("end")
        self.after(0, _do)

    # ── KẾT NỐI ─────────────────────────────────────────────────
    def _refresh_ports(self):
        ports = SerialManager.list_ports() or ["(không có)"]
        self.cmb_port.configure(values=ports)
        self.cmb_port.set(ports[0])

    def _toggle_conn(self):
        if self.serial.is_connected:
            self.reading = False; time.sleep(0.15)
            self.serial.disconnect()
            self.btn_conn.configure(text="Kết nối", fg_color=ACCENT)
            self.lbl_st.configure(text="● Chưa kết nối", text_color=DANGER)
            self._log("Đã ngắt kết nối.")
        else:
            port = self.cmb_port.get()
            baud = int(self.cmb_baud.get())
            if self.serial.connect(port, baud):
                self.btn_conn.configure(text="Ngắt kết nối", fg_color=DANGER)
                self.lbl_st.configure(text=f"● {port} @ {baud}", text_color=SUCCESS)
                self._log(f"Kết nối thành công {port} @ {baud} baud")
                self.reading = True
                threading.Thread(target=self._reader, daemon=True).start()
            else:
                self._log(f"[LỖI] Không mở được {port}!")

    # ── READER THREAD ────────────────────────────────────────────
    def _reader(self):
        pat = re.compile(r"X:\s*(-?\d+).*?Y:\s*(-?\d+).*?Z:\s*(-?\d+)")
        while self.reading and self.serial.is_connected:
            line = self.serial.readline()
            if not line:
                continue
            m = pat.search(line)
            if m:
                rx, ry, rz = int(m.group(1)), int(m.group(2)), int(m.group(3))
                self._raw = [rx, ry, rz]
                ax, ay, az = rx/ACCEL_SENS, ry/ACCEL_SENS, rz/ACCEL_SENS
                self.after(0, lambda x=ax,y=ay,z=az,r=[rx,ry,rz]:
                           self._update(x, y, z, r))
                self._log(f"Sensor X={ax:+.3f}g  Y={ay:+.3f}g  Z={az:+.3f}g", raw=True)
            elif line.strip():
                self._log(line)

    def _update(self, ax, ay, az, raw):
        self.lv_ax.configure(text=f"{ax:+.3f} g")
        self.lv_ay.configure(text=f"{ay:+.3f} g")
        self.lv_az.configure(text=f"{az:+.3f} g")
        self.lv_raw.configure(text=f"X:{raw[0]}  Y:{raw[1]}  Z:{raw[2]}")
        self.sample += 1
        self.t_h.append(self.sample)
        for i, v in enumerate([ax, ay, az]):
            self.ax_h[i].append(v)
        t = list(self.t_h)
        for i, ln in enumerate(self.ln):
            ln.set_data(t, list(self.ax_h[i]))
        self.ax_fig.relim(); self.ax_fig.autoscale_view()
        self.canvas.draw_idle()

    # ── LỆNH EEPROM ─────────────────────────────────────────────
    def _do_save(self):
        if not self.serial.is_connected:
            self._log("[LỖI] Chưa kết nối!"); return
        self._log(f">> SAVE  (raw X:{self._raw[0]} Y:{self._raw[1]} Z:{self._raw[2]})")
        self.serial.send("SAVE")

    def _do_write(self):
        if not self.serial.is_connected:
            self._log("[LỖI] Chưa kết nối!"); return
        addr = self.e_waddr.get().strip().upper()
        data = self.e_wdata.get().strip().upper()
        if not addr or not data:
            self._log("[LỖI] Nhập đủ Addr và Data!"); return
        cmd = f"WRITE {addr} {data}"
        self._log(f">> {cmd}")
        self.serial.send(cmd)

    def _do_read(self):
        if not self.serial.is_connected:
            self._log("[LỖI] Chưa kết nối!"); return
        addr = self.e_raddr.get().strip().upper()
        if not addr:
            self._log("[LỖI] Nhập địa chỉ!"); return
        cmd = f"READ {addr}"
        self._log(f">> {cmd}")
        self.serial.send(cmd)

    def on_close(self):
        self.reading = False
        self.serial.disconnect()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()