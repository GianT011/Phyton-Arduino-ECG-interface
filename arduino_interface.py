import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
from datetime import datetime
from scipy.signal import savgol_filter
import numpy as np
import csv

# Configura la porta seriale
ser = serial.Serial('COM7', 9600)

# Dati
time_data = []
value_data = []
peaks_times = []

measuring = False
start_time = None

# === Funzioni ===

def update_button_color():
    ax_btn.set_facecolor("red" if measuring else "green")
    btn.label.set_color("white")

def calcola_bpm(times, values, window_sec=10, k_soglia=1.5):
    if len(values) < 50:
        return None

    max_time = times[-1]
    idx_start = next((i for i, t in enumerate(times) if t >= max_time - window_sec), len(times) - 1)

    window_times = times[idx_start:]
    window_values = values[idx_start:]

    if len(window_values) < 20:
        return None

    # Calcola soglia dinamica
    mediana = np.median(window_values)
    deviazione_std = np.std(window_values)
    soglia = mediana + k_soglia * deviazione_std

    picchi_times = []
    stato = "sotto"
    i = 1

    while i < len(window_values) - 1:
        val_curr = window_values[i]
        if stato == "sotto" and val_curr > soglia:
            inizio_picco_idx = i
            stato = "sopra"
        elif stato == "sopra" and val_curr < soglia:
            fine_picco_idx = i
            if fine_picco_idx > inizio_picco_idx:
                sub_vals = window_values[inizio_picco_idx:fine_picco_idx + 1]
                sub_times = window_times[inizio_picco_idx:fine_picco_idx + 1]
                if sub_vals:
                    max_idx = np.argmax(sub_vals)
                    t_picco = sub_times[max_idx]

                    if not picchi_times or t_picco - picchi_times[-1] > 0.3:
                        picchi_times.append(t_picco)
                        peaks_times.append(t_picco)  # Salva anche per visualizzazione
            stato = "sotto"
        i += 1

    if len(picchi_times) < 2:
        return None

    rr_intervals = np.diff(picchi_times)
    bpm = 60.0 / np.mean(rr_intervals)

    print(f"Picchi rilevati: {len(picchi_times)}, BPM: {bpm:.1f}")
    return round(bpm, 1)

def update(frame):
    global start_time

    if not measuring:
        update_button_color()
        # Mantieni la scala Y fissa o aggiorna se vuoi
        if value_data:
            min_val = min(value_data)
            max_val = max(value_data)
            ax.set_ylim(min_val - 0.1, max_val + 0.1)
        else:
            ax.set_ylim(0, 2)
        return line,

    count = 0
    while ser.in_waiting and count < 20:
        try:
            raw_bytes = ser.readline()
            try:
                line_raw = raw_bytes.decode('utf-8').strip()
                print(f"Received: '{line_raw}'")
            except UnicodeDecodeError:
                continue

            if ',' not in line_raw:
                continue

            t_str, v_str = line_raw.split(",")
            timestamp = int(t_str) / 1000.0
            value = float(v_str)
            print(f"Timestamp: {timestamp:.2f}, Value: {value}")

            if start_time is None:
                start_time = timestamp
            rel_time = timestamp - start_time

            time_data.append(rel_time)
            value_data.append(value)
            count += 1

        except Exception as e:
            print(f"Errore di parsing: {e} | Riga: '{line_raw if 'line_raw' in locals() else 'n/a'}'")

    line.set_data(time_data, value_data)

    if time_data:
        ax.set_xlim(max(0, time_data[-1] - 10), time_data[-1] + 1)

    if value_data:
        min_val = min(value_data)
        max_val = max(value_data)
        # Aggiungi un piccolo margine sopra e sotto per non tagliare i dati
        ax.set_ylim(min_val - 0.1 * abs(min_val), max_val + 0.1 * abs(max_val))
    else:
        ax.set_ylim(0, 2)

    bpm = calcola_bpm(time_data, value_data)
    print(f"Calcolato BPM: {bpm}")
    bpm_text.set_text(f"BPM: {bpm}" if bpm else "BPM: --")

    update_button_color()
    return line,


def toggle_measure(event):
    global measuring, start_time, peaks_times
    measuring = not measuring
    if measuring:
        btn.label.set_text("FERMA")
        start_time = None
        time_data.clear()
        value_data.clear()
        peaks_times.clear()
    else:
        btn.label.set_text("AVVIA")
    update_button_color()
    plt.draw()

def salva_grafico(event):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_img = f"ecg_{timestamp}.jpg"
    filename_csv = f"picchi_{timestamp}.csv"

    plt.savefig(filename_img, format='jpg')
    print(f"Grafico salvato come: {filename_img}")

    if peaks_times:
        with open(filename_csv, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Tempo (s)'])
            for t in peaks_times:
                writer.writerow([round(t, 3)])
        print(f"Picchi salvati in: {filename_csv}")

# === Setup grafico ===
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.3)
line, = ax.plot([], [], color='blue', label="Segnale ECG")
peaks_line, = ax.plot([], [], 'ro', label="Picchi")

ax.set_xlabel("Tempo (s)")
ax.set_ylabel("Valore analogico")
ax.set_title("Monitor ECG in tempo reale")
ax.grid(True, linestyle='--', alpha=0.6)
ax.set_xlim(0, 10)
ax.set_ylim(-10, 10)
bpm_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12,
                   verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))

# Bottone AVVIA/FERMA
ax_btn = plt.axes([0.35, 0.05, 0.2, 0.075])
btn = Button(ax_btn, "AVVIA")
btn.on_clicked(toggle_measure)
ax_btn.set_facecolor("green")
btn.label.set_color("white")

# Bottone SALVA
ax_save = plt.axes([0.6, 0.05, 0.2, 0.075])
btn_save = Button(ax_save, "SALVA")
btn_save.on_clicked(salva_grafico)
ax_save.set_facecolor("#007ACC")

# Animazione
ani = animation.FuncAnimation(fig, update, blit=False, interval=50)
plt.legend()
plt.show()