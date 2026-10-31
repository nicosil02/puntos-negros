import { loadFont } from "@remotion/google-fonts/Geist";
import { Easing, interpolate, spring } from "remotion";

export const { fontFamily } = loadFont("normal", { weights: ["400", "500", "600", "700", "800"], subsets: ["latin"] });

export const C = {
  fondo: "#0c0e11",
  tarjeta: "#16191e",
  tinta: "#f5f5f5",
  suave: "#a6adb8",
  acento: "#ea580c",
  gris: "#3a3f47",
};

export const M = 80; // margen lateral (zona segura)

// 0 a 1 entre dos cuadros, con salida suave
export const tramo = (f: number, a: number, b: number) =>
  interpolate(f, [a, b], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });

export const resorte = (f: number, fps: number, desde = 0, damping = 200) =>
  spring({ frame: f - desde, fps, config: { damping } });

export const miles = (n: number) => Math.round(n).toLocaleString("en-US");
