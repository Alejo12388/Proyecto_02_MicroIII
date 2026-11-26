# Librerías importantes
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# Configuración para los gráficos y estilo de las figuras (en plano cartesiano)
plt.style.use(
	"seaborn-v0_8-whitegrid"
	if "seaborn-v0_8-whitegrid" in plt.style.available
	else "default"
)
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["figure.dpi"] = 300

# Variables (base de todos los grupos + específicas de nuestro caso)
class MercadoHeterogeneoImpuestos:
	def __init__(self, a1=10.0, b1=1.0, a2=20.0, b2=2.0, a3=35.0, b3=3.0):
		self.a1, self.b1 = a1, b1
		self.a2, self.b2 = a2, b2
		self.a3, self.b3 = a3, b3

	def oferta_individual(self, P_s):
		q1 = max(0.0, (P_s - self.a1) / self.b1) if P_s >= self.a1 else 0.0
		q2 = max(0.0, (P_s - self.a2) / self.b2) if P_s >= self.a2 else 0.0
		q3 = max(0.0, (P_s - self.a3) / self.b3) if P_s >= self.a3 else 0.0
		return q1, q2, q3

	def oferta_agregada(self, P_s):
		return sum(self.oferta_individual(P_s))
# Planteamos Equilibrio
	def resolver_equilibrio(self, t=0.0):
		low, high = 0.0, 120.0
		for _ in range(100):
			mid = (low + high) / 2.0
			Q_dem = max(0.0, 120.0 - mid - t)
			Q_ofe = self.oferta_agregada(mid)
			if Q_dem > Q_ofe:
				low = mid
			else:
				high = mid

		P_s = (low + high) / 2.0
		P_d = P_s + t
		q1, q2, q3 = self.oferta_individual(P_s)
		Q = q1 + q2 + q3
		recaudo = t * Q
		return {
			"t": t,
			"P_s": P_s,
			"P_d": P_d,
			"Q": Q,
			"q1": q1,
			"q2": q2,
			"q3": q3,
			"recaudo": recaudo,
			"activas": int(q1 > 1e-5) + int(q2 > 1e-5) + int(q3 > 1e-5),
		}
# Triángulo de Harberger (PIE)
	def calcular_pie(self, eq_t, eq_0):
		if eq_t["t"] == 0 or eq_0["Q"] <= eq_t["Q"]:
			return 0.0

		q_grid = np.linspace(eq_t["Q"], eq_0["Q"], 1000)
		P_d_vals = 120.0 - q_grid
		P_s_vals = []
		for q in q_grid:
			low, high = 0.0, 120.0
			for _ in range(50):
				mid = (low + high) / 2.0
				if self.oferta_agregada(mid) < q:
					low = mid
				else:
					high = mid
			P_s_vals.append((low + high) / 2.0)

		P_s_vals = np.asarray(P_s_vals)
		surplus_gap = P_d_vals - P_s_vals
		if hasattr(np, "trapezoid"):
			pie = np.trapezoid(surplus_gap, q_grid)
		elif hasattr(np, "trapz"):
			pie = np.trapz(surplus_gap, q_grid)
		else:
			pie = np.sum(
				0.5 * (surplus_gap[:-1] + surplus_gap[1:]) * np.diff(q_grid)
			)
		return max(0.0, pie)

# Ahora si, simular con diferentes impuestos y generar resultados
def ejecutar_simulacion():
	modelo = MercadoHeterogeneoImpuestos()
	eq_0 = modelo.resolver_equilibrio(t=0.0)

	# 1. Tabla de sensibilidad 1D
	impuestos = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 52.5, 60.0, 75.0, 90.0, 100.0]
	res = []
	for t in impuestos:
		eq = modelo.resolver_equilibrio(t=t)
		pie = modelo.calcular_pie(eq, eq_0)
		res.append(
			{
				"Impuesto (t)": t,
				"P_demanda (P_d)": round(eq["P_d"], 2),
				"P_productor (P_s)": round(eq["P_s"], 2),
				"Q_total": round(eq["Q"], 2),
				"q1 (Eficiente)": round(eq["q1"], 2),
				"q2 (Media)": round(eq["q2"], 2),
				"q3 (Ineficiente)": round(eq["q3"], 2),
				"Recaudo (T)": round(eq["recaudo"], 2),
				"PIE (Harberger)": round(pie, 2),
				"Firmas Activas": eq["activas"],
			}
		)

	df_res = pd.DataFrame(res)
	df_res.to_csv("tabla_sensibilidad_1d.csv", index=False)
	print("✓ Tabla de sensibilidad 1D guardada como 'tabla_sensibilidad_1d.csv'")

	# 2. Figura 1: análisis tradicional de bienestar e incidencia tributaria
	fig, ax = plt.subplots(figsize=(9, 6))
	Q_grid = np.linspace(0, 90, 500)
	ax.plot(
		Q_grid,
		120.0 - Q_grid,
		label="Demanda (P = 120 - Q)",
		color="#009e73",
		lw=2.5,
	)

	def oferta_inversa(q):
		if q < 10:
			return 10 + q
		if q < 32.5:
			return (2 / 3) * q + 40 / 3
		return (6 / 11) * q + 190 / 11

	ax.plot(
		Q_grid,
		[oferta_inversa(q) for q in Q_grid],
		label="Oferta Agregada $P_s(Q)$ [Por Tramos]",
		color="#0072b2",
		lw=2.5,
	)

	#Ahora detemrinamos equilibrio con impuesto y equilibrio sin impuesto
	t_demo = 30.0
	eq_demo = modelo.resolver_equilibrio(t=t_demo)
	Q30, Ps30, Pd30 = eq_demo["Q"], eq_demo["P_s"], eq_demo["P_d"]
	Q0, P0 = eq_0["Q"], eq_0["P_s"]

	# Coloreamos las áreas de bienestar
	Q_ec = np.linspace(0, Q30, 200)
	Q_pie = np.linspace(Q30, Q0, 200)
	ax.fill_between(
		Q_ec,
		Pd30,
		120.0 - Q_ec,
		color="#56b4e9",
		alpha=0.4,
		label="Excedente del Consumidor (EC)",
	)
	ax.fill_between(
		[0, Q30],
		Ps30,
		Pd30,
		color="#f0e442",
		alpha=0.5,
		label=f"Recaudo Fiscal (T = t × Q = {t_demo * Q30:.1f})",
	)
	ax.fill_between(
		Q_ec,
		[oferta_inversa(q) for q in Q_ec],
		Ps30,
		color="#e69f00",
		alpha=0.4,
		label="Excedente del Productor (EP)",
	)
	ax.fill_between(
		Q_pie,
		[oferta_inversa(q) for q in Q_pie],
		120.0 - Q_pie,
		color="#d55e00",
		alpha=0.5,
		label="Pérdida Irrecuperable (PIE)",
	)

	# Líneas guía, puntos de equilibrio y etiquetas
	ax.axhline(Pd30, color="#333333", ls=":", lw=1.2)
	ax.axhline(Ps30, color="#333333", ls=":", lw=1.2)
	ax.axhline(P0, color="#888888", ls="--", lw=1)
	ax.axvline(Q30, color="#333333", ls=":", lw=1.2)
	ax.axvline(Q0, color="#888888", ls="--", lw=1)
	ax.scatter(
		[Q0], [P0], color="#009e73", s=80, zorder=5,
		label=f"Eq. Sin Impuesto (Q*={Q0:.1f}, P*={P0:.1f})",
	)
	ax.scatter([Q30], [Pd30], color="#d55e00", s=70, zorder=5)
	ax.scatter([Q30], [Ps30], color="#0072b2", s=70, zorder=5)
	ax.text(
		15, 85, "EC", fontsize=12, fontweight="bold", color="#005580",
		bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#56b4e9", alpha=0.8),
	)
	ax.text(
		15, 57, f"Recaudo (T)\nt = {t_demo:.0f}", fontsize=11,
		fontweight="bold", color="#665500",
		bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#e69f00", alpha=0.8),
	)
	ax.text(
		15, 30, "EP", fontsize=12, fontweight="bold", color="#804000",
		bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#e69f00", alpha=0.8),
	)
	ax.text(
		53, 54, "PIE", fontsize=12, fontweight="bold", color="#800000",
		bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#d55e00", alpha=0.8),
	)
	ax.set_title(
		"Análisis Tradicional de Bienestar e Incidencia Tributaria (t = 30 COP)",
		fontsize=12,
		fontweight="bold",
	)
	ax.set_xlabel("Cantidad Agregada (Q)", fontsize=10)
	ax.set_ylabel("Precio (COP)", fontsize=10)
	ax.set_xlim(0, 85)
	ax.set_ylim(0, 110)
	ax.legend(loc="upper right", fontsize=8, frameon=True)
	plt.tight_layout()
	plt.savefig("figura1_oferta_tramos_equilibrio.png", dpi=300)
	plt.close()
	# 3. Figura 2: cantidades y bienestar vs. impuesto (1D)
	fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
	t_vals = np.linspace(0, 100, 200)
	q1_l, q2_l, q3_l, rec_l, pie_l = [], [], [], [], []
	for t in t_vals:
		eq = modelo.resolver_equilibrio(t=t)
		q1_l.append(eq["q1"])
		q2_l.append(eq["q2"])
		q3_l.append(eq["q3"])
		rec_l.append(eq["recaudo"])
		pie_l.append(modelo.calcular_pie(eq, eq_0))

	ax1.plot(t_vals, q1_l, label="Tech 1 (Eficiente)", color="#0072b2", lw=2)
	ax1.plot(t_vals, q2_l, label="Tech 2 (Media)", color="#e69f00", lw=2)
	ax1.plot(t_vals, q3_l, label="Tech 3 (Ineficiente)", color="#d55e00", lw=2)
	ax1.axvline(
		52.5,
		color="#8a8a8a",
		ls="--",
		label="Cierre Tech 3 (t=52.5)",
	)
	ax1.axvline(
		90.0,
		color="#8a8a8a",
		ls=":",
		label="Cierre Tech 2 (t=90.0)",
	)
	ax1.set_title("Producción Individual y Cierre de Firmas", fontweight="bold")
	ax1.set_xlabel("Impuesto (t)")
	ax1.set_ylabel("Cantidad (q_i)")
	ax1.legend(fontsize=8)

	ax2.plot(t_vals, rec_l, label="Recaudación (T)", color="#009e73", lw=2.5)
	ax2.plot(t_vals, pie_l, label="Pérdida Irrecuperable (PIE)", color="#d55e00", lw=2.5)
	ax2.set_title("Recaudación vs Costo Social (PIE)", fontweight="bold")
	ax2.set_xlabel("Impuesto (t)")
	ax2.set_ylabel("COP")
	ax2.legend(fontsize=8)
	plt.tight_layout()
	plt.savefig("figura2_sensibilidad_1d.png", dpi=300)
	plt.close()
	print("✓ Figura 2 guardada como 'figura2_sensibilidad_1d.png'")

	# 4. Figura 3: mapa 2D de fronteras de inactividad
	gamma_vals = np.linspace(0.5, 2.5, 100)
	t_vals_2d = np.linspace(0, 100, 100)
	T_g, G_g = np.meshgrid(t_vals_2d, gamma_vals)
	Z = np.zeros_like(T_g)
	for i, gamma in enumerate(gamma_vals):
		modelo_gamma = MercadoHeterogeneoImpuestos(a3=20.0 + 15.0 * gamma)
		for j, t in enumerate(t_vals_2d):
			Z[i, j] = modelo_gamma.resolver_equilibrio(t=t)["activas"]

	fig, ax = plt.subplots(figsize=(8, 6))
	contour = ax.contourf(
		T_g,
		G_g,
		Z,
		levels=[-0.5, 0.5, 1.5, 2.5, 3.5],
		colors=["#e6e6e6", "#d55e00", "#e69f00", "#009e73"],
	)
	cbar = fig.colorbar(contour, ticks=[0, 1, 2, 3])
	cbar.ax.set_yticklabels(
		["0 (Colapso)", "1 (Solo Tech 1)", "2 (Tech 1 y 2)", "3 (Todas)"]
	)
	ax.set_title(
		"Mapa 2D: Tecnologías Activas según Impuesto (t) y Dispersión (γ)",
		fontweight="bold",
	)
	ax.set_xlabel("Impuesto (t)")
	ax.set_ylabel("Dispersión de Costos (γ)")
	plt.tight_layout()
	plt.savefig("figura3_mapa_2d_fronteras.png", dpi=300)
	plt.close()
	print("✓ Figura 3 guardada como 'figura3_mapa_2d_fronteras.png'")
	print("\nFinal")


if __name__ == "__main__":
	ejecutar_simulacion()
