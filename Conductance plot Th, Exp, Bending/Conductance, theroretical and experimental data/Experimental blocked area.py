import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# === Constants ===
rho = 8.96        # Ohm·cm
l = 0.0075        # cm
A_open = 75e-4 * 55e-4  # cm²
inv_A = 1 / A_open
rho_l = rho * l

# === Conductance Data ===
pressures_bar = [0.0, 0.4, 0.6, 0.8, 1.2]
conductance_mS = [1.2, 0.54, 0.43, 0.28, 0.16]

# === Calculations ===
R1 = 1 / (conductance_mS[0] / 1000)
blocked_percent = []
steps_text = []

for P, G_mS in zip(pressures_bar, conductance_mS):
    G_S = G_mS / 1000
    R1_prime = 1 / G_S
    delta_R = R1_prime - R1
    inv_A_prime = inv_A + delta_R / rho_l
    A_prime = 1 / inv_A_prime
    percent_blocked = (1 - A_prime / A_open) * 100
    blocked_percent.append(percent_blocked)

    steps_text.append(
        f"--- Pressure: {P:.1f} bar ---\n"
        f"Conductance G       = {G_mS:.3f} mS\n"
        f"G in S              = {G_S:.5f} S\n"
        f"R1′                 = 1 / G = {R1_prime:.2f} Ohm\n"
        f"ΔR                  = R1′ - R1 = {delta_R:.2f} Ohm\n"
        f"1 / A′              = 1/A + ΔR / (rho * l) = {inv_A_prime:.2e}\n"
        f"A′                  = 1 / (1/A′) = {A_prime:.5e} cm²\n"
        f"Blocked %           = (1 - A′ / A) * 100 = {percent_blocked:.2f} %\n"
    )

# Final results block
final_lines = "\n".join(
    [f"Pressure {p:.1f} bar → Blocked Area = {b:.2f} %" for p, b in zip(pressures_bar, blocked_percent)]
)

# Compile full report
report_text = (
    "EXPERIMENTAL BLOCKED AREA CALCULATION (CONDUCTANCE-BASED)\n"
    + "=" * 60 + "\n\n"
    f"Constants:\n"
    f"Resistivity (rho)       = {rho} Ohm·cm\n"
    f"Channel Length (l)      = {l} cm\n"
    f"Open Area (A)           = {A_open:.5e} cm²\n"
    f"Open Resistance (R1)    = {R1:.2f} Ohm\n\n"
    "Step-by-step Calculations:\n"
    + "-" * 30 + "\n" +
    "\n".join(steps_text) +
    "\nFinal Results:\n" +
    "-" * 30 + "\n" +
    final_lines + "\n"
)

# === Print in Terminal too ===
print(report_text)

# === Save to PDF ===
pdf_path = "experimental_blocked_area_output_fixed.pdf"

with PdfPages(pdf_path) as pdf:
    fig, ax = plt.subplots(figsize=(8.5, 14))  # increased height
    ax.axis('off')
    ax.text(0.01, 1.0, report_text, va='top', fontsize=10, family='monospace')
    pdf.savefig()
    plt.close()

pdf_path
