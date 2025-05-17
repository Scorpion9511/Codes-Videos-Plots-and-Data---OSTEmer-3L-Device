import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# === Constants for experimental blocked area from conductance ===
rho = 8.96  # Ohm·cm (1M KCl)
l = 0.0075  # cm
A = 75e-4 * 55e-4  # cm²
inv_A = 1 / A
rho_l = rho * l
R1 = 1 / 0.0012  # Ohms (open valve)

# === Pressure values and measured conductance ===
pressures_bar = [0.0, 0.4, 0.6, 0.8, 1.2]
conductance_mS = [1.2, 0.54, 0.43, 0.28, 0.16]

# === Calculate Experimental Blocked Area ===
blocked_area_exp = []
delta_R_list = []
R1_prime_list = []
inv_A_prime_list = []
A_prime_list = []

for G in conductance_mS[1:]:
    R1_prime = 1 / (G / 1000)
    delta_R = R1_prime - R1
    inv_A_prime = inv_A + delta_R / rho_l
    A_prime = 1 / inv_A_prime
    blocked_fraction = (1 - A_prime / A) * 100
    R1_prime_list.append(R1_prime)
    delta_R_list.append(delta_R)
    inv_A_prime_list.append(inv_A_prime)
    A_prime_list.append(A_prime)
    blocked_area_exp.append(blocked_fraction)

# Insert for 0 bar
R1_prime_list.insert(0, R1)
delta_R_list.insert(0, 0.0)
inv_A_prime_list.insert(0, inv_A)
A_prime_list.insert(0, A)
blocked_area_exp.insert(0, 0.0)

# === Theoretical Calculation Constants ===
a_um = 75 / 2
a = a_um * 1e-4  # cm
t_um = 1.8
t = t_um * 1e-4  # cm
E = 7e6  # Pa
nu = 0.3
E_prime = E / (1 - nu)
C2f = 2.67

pressures_pa = np.array(pressures_bar) * 1e5

# === Deflection and Theoretical Blocked Area ===
def calc_deflection(P):
    factor = (a * P * C2f) / (E_prime * t)
    return a * (factor)**(1/3) if P > 0 else 0.0, factor

def calc_blocked_area_percent(w, a, A_total):
    if w == 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    r = (a**2 + w**2) / (2 * w)
    theta = 2 * np.arcsin(a / r)
    sector = 0.5 * r**2 * theta
    triangle = a * (r - w)
    arc = sector - triangle
    percent = (arc / A_total) * 100
    return percent, r, theta, sector, triangle, arc

# === Compute theoretical values ===
deflections, factors = [], []
blocked_area_theoretical, r_list, theta_list = [], [], []
sector_area_list, triangle_area_list, arc_area_list = [], [], []

for P in pressures_pa:
    w, factor = calc_deflection(P)
    percent, r, theta, sector, triangle, arc = calc_blocked_area_percent(w, a, A)
    deflections.append(w)
    factors.append(factor)
    blocked_area_theoretical.append(percent)
    r_list.append(r)
    theta_list.append(theta)
    sector_area_list.append(sector)
    triangle_area_list.append(triangle)
    arc_area_list.append(arc)

# === Save to Excel ===
df_combined = pd.DataFrame({
    "Pressure (bar)": pressures_bar,
    "Pressure (Pa)": pressures_pa,
    "Conductance (mS)": conductance_mS,
    "R1' (Ohm)": R1_prime_list,
    "ΔR (Ohm)": delta_R_list,
    "1/A' (cm⁻²)": inv_A_prime_list,
    "A' (cm²)": A_prime_list,
    "Experimental Blocked Area (%)": blocked_area_exp,
    "Deflection Factor": factors,
    "Deflection w0 (cm)": deflections,
    "Curvature Radius r (cm)": r_list,
    "Theta (rad)": theta_list,
    "Sector Area (cm²)": sector_area_list,
    "Triangle Area (cm²)": triangle_area_list,
    "Arc Area (cm²)": arc_area_list,
    "Theoretical Blocked Area (%)": blocked_area_theoretical
})
df_combined.to_excel("blocked_area_full_calculations.xlsx", index=False)

# === Plot to PDF with Clear Labels ===
with PdfPages("blocked_area_labeled_plot.pdf") as pdf:
    fig, ax1 = plt.subplots(figsize=(9, 5))
    ax1.set_xlabel("Pressure (bar)")
    ax1.set_ylabel("Conductance (mS)", color='tab:blue')
    ax1.plot(pressures_bar, conductance_mS, 'o-', color='tab:blue', label="Conductance")
    for x, y in zip(pressures_bar, conductance_mS):
        ax1.text(x, y + 0.03, f"{y:.2f}", color='tab:blue', fontsize=8, ha='center', va='bottom')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    ax2 = ax1.twinx()
    ax2.set_ylabel("Blocked Area (%)", color='black')
    ax2.plot(pressures_bar, blocked_area_exp, 's--', color='tab:green', label="Experimental Blocked Area")
    ax2.plot(pressures_bar, blocked_area_theoretical, 'd-.', color='tab:red', label="Theoretical Blocked Area")
    
    for x, y in zip(pressures_bar, blocked_area_exp):
        ax2.text(x + 0.03, y + 2, f"{y:.1f}", color='tab:green', fontsize=8, ha='left', va='bottom')

    for x, y in zip(pressures_bar, blocked_area_theoretical):
        ax2.text(x - 0.03, y - 3, f"{y:.1f}", color='tab:red', fontsize=8, ha='right', va='top')

    ax2.tick_params(axis='y', labelcolor='black')

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="lower center", bbox_to_anchor=(0.5, -0.25), ncol=2)

    plt.title("Conductance and Blocked Area vs Pressure")
    plt.grid(True)
    plt.tight_layout()
    pdf.savefig()
    plt.close()
