# STM32F4 — Giao tiếp I2C, UART & DMA

> Đọc cảm biến MPU6050, đọc/ghi EEPROM 24C04 qua I2C · Truyền dữ liệu UART với DMA · Điều khiển qua GUI Python

---

## 📌 Mô tả đề tài

Đề tài xây dựng hệ thống nhúng trên kit **STM32F407VG Discovery** kết hợp giao diện điều khiển trên PC, với các chức năng:

- **Đọc cảm biến IMU MPU6050** (gia tốc X, Y, Z) qua giao thức I2C1
- **Đọc / Ghi EEPROM AT24C04** theo 2 chế độ: ghi byte đơn và ghi block 6 byte
- **Truyền nhận dữ liệu UART2** sử dụng DMA — không chiếm CPU khi truyền
- **Giao diện GUI trên PC** (Python) hiển thị biểu đồ real-time, điều khiển EEPROM
- **Hiển thị trạng thái** qua 3 LED: OK (xanh lá) · BUSY (vàng) · ERROR (đỏ)

---

## 👥 Thành viên nhóm

| Họ và tên | MSSV | Vai trò |
|---|---|---|
| Trần Đặng Khánh Sơn | 2312979 | Trưởng nhóm · Firmware |
| Nguyễn Thị Huyền Trân | 2313555 | Thành viên · GUI |
| Phan Khánh Toàn | 2313494 | Thành viên · Firmware |

---

## 🔧 Phần cứng sử dụng

| Linh kiện | Mô tả | Giao tiếp |
|---|---|---|
| STM32F407VG Discovery | Vi điều khiển chính | — |
| MPU6050 | Cảm biến gia tốc / con quay hồi chuyển | I2C1 (PB6 · PB7) |
| EEPROM AT24C04 | Bộ nhớ lưu trữ phi biến động | I2C1 (PB6 · PB7) |
| USB–UART (CP2102) | Kết nối chip với PC | USART2 (PA2 · PA3) |
| LED xanh lá | Trạng thái OK | GPIO PD12 |
| LED vàng | Trạng thái BUSY | GPIO PD13 |
| LED đỏ | Trạng thái ERROR | GPIO PD14 |

---

## 🗂️ Cấu trúc thư mục

```
STM32F4-I2C-UART-DMA/
│
├── Core/
│   ├── Inc/                      # Header files
│   │   ├── main.h
│   │   ├── i2c.h
│   │   ├── usart.h
│   │   ├── dma.h
│   │   └── gpio.h
│   │
│   └── Src/                      # Source files
│       ├── main.c                # Vòng lặp chính + xử lý lệnh
│       ├── i2c.c                 # Cấu hình I2C1 + DMA RX
│       ├── usart.c               # Cấu hình UART2 + DMA TX + UART_Printf
│       ├── dma.c                 # Khởi tạo DMA1
│       ├── gpio.c                # Cấu hình 3 LED
│       ├── stm32f4xx_it.c        # Interrupt handlers
│       └── stm32f4xx_hal_msp.c
│
├── GUI/
│   ├── gui_stm32.py              # Mã nguồn giao diện Python
│   ├── gui_stm32.exe             # File thực thi (Windows, không cần cài Python)
│   └── requirements.txt          # Danh sách thư viện Python
│
├── Docs/                         # Báo cáo, sơ đồ mạch
│
└── README.md
```

---

## ⚙️ Cấu hình hệ thống (Firmware)

| Thông số | Giá trị |
|---|---|
| Clock hệ thống | 168 MHz (HSE + PLL) |
| I2C1 clock speed | 100 kHz (Standard Mode) |
| UART2 baud rate | 115200 · 8N1 |
| DMA I2C1 RX | DMA1 Stream0 Channel1 |
| DMA UART2 TX | DMA1 Stream6 Channel4 |

---

## 🖥️ Giao diện GUI (Python)

Giao diện dark-mode xây dựng bằng `customtkinter`, tự động nhận và hiển thị dữ liệu cảm biến qua UART mà không cần thao tác thêm.

### Tính năng

| Khu vực | Chức năng |
|---|---|
| **Kết nối UART** | Chọn cổng COM, baud rate, kết nối / ngắt kết nối |
| **Gia tốc kế** | Hiển thị Accel X / Y / Z (đơn vị g) cập nhật mỗi 100ms |
| **Biểu đồ real-time** | Vẽ đồ thị 3 trục (X=xanh · Y=xanh lá · Z=vàng), lưu 80 mẫu gần nhất |
| **SAVE** | Ghi block 6 byte (X, Y, Z hiện tại) vào EEPROM địa chỉ 0x00–0x05 |
| **WRITE** | Ghi 1 byte vào địa chỉ EEPROM tùy chọn |
| **READ** | Đọc 1 byte từ địa chỉ EEPROM tùy chọn |
| **Terminal / Log** | Hiển thị toàn bộ log có timestamp, tùy chọn ẩn dữ liệu sensor thô |

### Cài đặt & chạy từ mã nguồn

```bash
# 1. Cài thư viện
pip install customtkinter pyserial matplotlib

# 2. Chạy GUI
python gui_stm32.py
```

### Chạy không cần cài Python

Tải file `GUI/gui_stm32.exe` và chạy trực tiếp trên Windows.

---

## 💻 Tập lệnh điều khiển từ PC

Gõ lệnh qua GUI hoặc terminal, kết thúc bằng **Enter**:

| Lệnh | Cú pháp | Mô tả |
|---|---|---|
| `SAVE` | `SAVE` | Ghi block 6 byte (X, Y, Z hiện tại) vào EEPROM địa chỉ 0x00 |
| `WRITE` | `WRITE <addr_hex> <val_hex>` | Ghi 1 byte vào địa chỉ EEPROM chỉ định |
| `READ` | `READ <addr_hex>` | Đọc 1 byte từ địa chỉ EEPROM chỉ định |

**Ví dụ:**
```
WRITE 08 FF     → Ghi 0xFF vào ô nhớ 0x08
READ 08         → Đọc nội dung ô nhớ 0x08
SAVE            → Lưu X/Y/Z hiện tại vào EEPROM
```

---

## 🚀 Hướng dẫn chạy dự án (Firmware)

### Công cụ sử dụng

| Công cụ | Mục đích | Link |
|---|---|---|
| STM32CubeMX | Cấu hình ngoại vi, sinh code HAL | [Tải về](https://www.st.com/en/development-tools/stm32cubemx.html) |
| Keil MDK-ARM (µVision) | Biên dịch & nạp firmware | [Tải về](https://www.keil.com/download/product/) |
| Driver CP2102 | Kết nối USB–UART với PC | [Tải về](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers) |
| ST-Link Driver | Nạp firmware qua ST-Link | Đi kèm kit Discovery |

### Các bước

```bash
# 1. Clone repo
git clone https://github.com/MMikeDangon1408/STM32F4-I2C-UART-DMA.git
```

2. Mở **STM32CubeMX** → **File** → **Load Project** → chọn file `.ioc` trong thư mục vừa clone
3. Kiểm tra cấu hình ngoại vi → bấm **Generate Code** (Toolchain: MDK-ARM)
4. Mở file `MDK-ARM\BTNChuong4_Nhom5.uvprojx` bằng **Keil µVision**
5. Build: **F7** hoặc **Project** → **Build Target**
6. Nạp firmware: **Flash** → **Download** (hoặc **F8**)
7. Mở `GUI/gui_stm32.exe` để điều khiển và quan sát dữ liệu

---

## 📊 Sơ đồ hoạt động

```
         ┌──────────────────────────────────────────────┐
         │              STM32F407VG                     │
         │                                              │
MPU6050 ─┤─ I2C1 ──► Đọc accel X, Y, Z mỗi 100ms      │
EEPROM  ─┤─ I2C1 ──► Ghi / Đọc byte & block            │
         │                                              │
         │             DMA1 (chạy nền)                  │
         │              ├── Stream0: I2C1 RX            │
         │              └── Stream6: UART2 TX           │
         │                                              │
         │─ UART2 ◄─────────────── Lệnh từ GUI/PC       │
         │─ UART2 ──────────────► Dữ liệu lên GUI/PC   │
         │                                              │
         │─ GPIO ──► LED OK(PD12) / BUSY(PD13) / ERROR(PD14)
         └──────────────────────────────────────────────┘
                              │ USB-UART (CP2102)
                    ┌─────────▼─────────┐
                    │   GUI Python      │
                    │  · Biểu đồ XYZ   │
                    │  · SAVE/WRITE/READ│
                    │  · Terminal log   │
                    └───────────────────┘
```

---

## 📝 Ghi chú kỹ thuật

- Địa chỉ I2C MPU6050: `0xD0` (AD0 = GND)
- Địa chỉ I2C EEPROM AT24C04: `0xA0`
- Xác nhận chip MPU6050 qua thanh ghi `WHO_AM_I` (0x75) — kỳ vọng trả về `0x68`
- GUI tự parse dữ liệu theo format firmware: `X:%d\tY:%d\tZ:%d`
- Hệ số quy đổi raw → g: `ACCEL_SENS = 16384.0` (±2g, độ phân giải 16-bit)
- LED xanh nhấp nháy liên tục = hệ thống đang đọc cảm biến bình thường

---

## 📄 Giấy phép

Dự án phục vụ mục đích học tập. Mã nguồn HAL được cấp phép bởi STMicroelectronics.
