import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import datos from "./datos.json";
import { C, M, fontFamily, miles, resorte, tramo } from "./estilo";

const AUTOR = "Nicolás Silva Andújar";

// Título, aviso de IA, barra de avance y fuente: fijos todo el video
export const Marco: React.FC = () => {
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (
    <AbsoluteFill style={{ fontFamily }}>
      <div style={{ position: "absolute", left: M, right: M, top: 64, height: 6, borderRadius: 3, background: "rgba(255,255,255,.14)" }}>
        <div style={{ width: `${(100 * f) / durationInFrames}%`, height: "100%", borderRadius: 3, background: C.acento }} />
      </div>
      <div style={{ position: "absolute", left: M, right: M, top: 100, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ color: C.acento, fontSize: 40, fontWeight: 800, letterSpacing: 1 }}>PUNTOS NEGROS</span>
        <span style={{ color: C.suave, fontSize: 24, fontWeight: 600, border: `2px solid ${C.suave}`, borderRadius: 30, padding: "8px 20px", background: "rgba(12,14,17,.6)" }}>
          VOZ GENERADA CON IA
        </span>
      </div>
      <div style={{ position: "absolute", left: M, right: M, bottom: 70, color: C.suave, fontSize: 26, lineHeight: 1.35 }}>
        {AUTOR} · Fuente: {datos.fuente}
      </div>
    </AbsoluteFill>
  );
};

// Oscurece arriba y abajo para que el texto se lea sobre mapas y videos
export const Velo: React.FC = () => (
  <AbsoluteFill
    style={{
      background: `linear-gradient(to bottom, rgba(12,14,17,.92) 0px, rgba(12,14,17,0) 300px, rgba(12,14,17,0) 900px, rgba(12,14,17,.9) 1250px, rgba(12,14,17,.97) 1920px)`,
    }}
  />
);

// Subtítulos: un bloque corto a la vez; la palabra que se dice va en naranja
export const Subtitulos: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const b = datos.subtitulos.find((s) => s.ini - 0.05 <= t && t <= s.fin + 0.12);
  if (!b) return null;
  const entra = resorte(f, fps, Math.round(b.ini * fps), 18);
  return (
    <AbsoluteFill style={{ fontFamily, justifyContent: "flex-start", alignItems: "center" }}>
      <div
        style={{
          position: "absolute", top: 1440, maxWidth: 1080 - 2 * M, padding: "18px 34px", borderRadius: 26,
          background: "rgba(22,25,30,.92)", fontSize: 62, fontWeight: 800, color: C.tinta, textAlign: "center", lineHeight: 1.15,
          scale: String(0.92 + 0.08 * entra), opacity: entra,
        }}
      >
        {b.palabras.map((p, i) => {
          const sig = b.palabras[i + 1]?.ini ?? b.fin;
          const activa = p.ini <= t && t < sig + 0.05;
          return (
            <span key={i} style={{ color: activa ? C.acento : C.tinta }}>
              {p.t}
              {i < b.palabras.length - 1 ? " " : ""}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// Cifra grande que cuenta hacia arriba, con su etiqueta; la base queda en y = 1380
export const Cifra: React.FC<{ valor?: number; texto?: string; antes?: string; etiqueta: string; desde: number }> = ({ valor, texto, antes = "", etiqueta, desde }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = resorte(f, fps, desde);
  const n = valor === undefined ? texto : miles(valor * tramo(f, desde, desde + 1.2 * fps));
  return (
    <div style={{ position: "absolute", left: M, right: M, bottom: 1920 - 1380, fontFamily, opacity: a, translate: `0px ${40 * (1 - a)}px` }}>
      <div style={{ color: C.acento, fontSize: String(n).length > 6 ? 150 : 190, fontWeight: 800, lineHeight: 0.95, letterSpacing: -6, whiteSpace: "nowrap" }}>
        {antes}
        {n}
      </div>
      <div style={{ color: C.tinta, fontSize: 44, fontWeight: 500, lineHeight: 1.25, marginTop: 14 }}>{etiqueta}</div>
    </div>
  );
};
