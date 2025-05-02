import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Constants
pressures_bar = [0.4, 0.6, 0.8, 1.2]
a_um = 75 / 2
a_cm = a_um * 1e-4  # cm
t_um = 1.8
t_cm = t_um * 1e-4  # cm
E = 7e6  # Pa
nu = 0.3
C2f = 2.67
A_channel = 75e-4 * 55e-4  # cm²
E_prime = E / (1 - nu)

# Create PDF
pdf_path = "blocked_area_all_pressures_detailed.pdf"
with PdfPages(pdf_path) as pdf:
    for P_bar in pressures_bar:
        P_pa = P_bar * 1e5

        # Step-by-step
        numerator = a_cm * P_pa * C2f
        denominator = E_prime * t_cm
        factor = numerator / denominator

        w0_cm = a_cm * (factor)**(1/3)
        w0_um = w0_cm * 1e4

        a_sq = a_cm**2
        w_sq = w0_cm**2
        numer = a_sq + w_sq
        denom = 2 * w0_cm
        r_cm = numer / denom

        theta_rad = 2 * np.arcsin(a_cm / r_cm)
        triangle_area = a_cm * (r_cm - w0_cm)
        sector_area = 0.5 * r_cm**2 * theta_rad
        arc_area = sector_area - triangle_area
        blocked_percent = (arc_area / A_channel) * 100

        # Compose detailed output
        text = f"""
BLOCKED AREA CALCULATION AT {P_bar} BAR
----------------------------------------

[1] Input Parameters
Pressure (P)             = {P_bar} bar = {P_pa:.0f} Pa
Membrane radius (a)      = {a_um:.2f} µm = {a_cm:.5f} cm
Membrane thickness (t)   = {t_um:.2f} µm = {t_cm:.5f} cm
Young's modulus (E)      = {E:.2e} Pa
Poisson's ratio (ν)      = {nu}
Constant (C₂f)           = {C2f}
Channel cross-section A  = {A_channel:.5e} cm²

[2] Intermediate Calculations
Effective modulus (E′)   = {E_prime:.2e} Pa

Factor = (a × P × C₂f) / (E' × t)
       = ({a_cm:.5f} × {P_pa:.0f} × {C2f}) / ({E_prime:.2e} × {t_cm:.5f})
       = {numerator:.5f} / {denominator:.5f}
       = {factor:.5f}

w₀ = a × factor^(1/3)
   = {a_cm:.5f} × ({factor:.5f})^(1/3)
   = {w0_cm:.5f} cm = {w0_um:.2f} µm

r = (a² + w₀²) / (2 × w₀)
  = ({a_cm:.5f}² + {w0_cm:.5f}²) / (2 × {w0_cm:.5f})
  = ({a_sq:.5e} + {w_sq:.5e}) / {denom:.5f}
  = {r_cm:.5f} cm

θ = 2 × arcsin(a / r)
  = 2 × arcsin({a_cm:.5f} / {r_cm:.5f})
  = {theta_rad:.5f} rad

Triangle Area = a × (r - w₀)
              = {a_cm:.5f} × ({r_cm:.5f} - {w0_cm:.5f})
              = {triangle_area:.5e} cm²

Sector Area = 0.5 × r² × θ
            = 0.5 × {r_cm:.5f}² × {theta_rad:.5f}
            = {sector_area:.5e} cm²

Arc (Blocked) Area = Sector - Triangle
                   = {sector_area:.5e} - {triangle_area:.5e}
                   = {arc_area:.5e} cm²

[3] Final Result
Blocked Area (%) = (Arc Area / Channel Area) × 100
                 = ({arc_area:.5e} / {A_channel:.5e}) × 100
                 = {blocked_percent:.2f} %

➡️ Final Blocked Area at {P_bar} bar = {blocked_percent:.2f} %
"""

        # Save to PDF
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')
        ax.text(0.01, 0.99, text, va='top', fontsize=10, family='monospace', wrap=True)
        pdf.savefig()
        plt.close()

print(f"✅ PDF saved as: {pdf_path}")
