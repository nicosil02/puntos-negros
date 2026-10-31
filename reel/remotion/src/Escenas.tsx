import React from "react";
import { Video } from "@remotion/media";
import { AbsoluteFill, Img, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import datos from "./datos.json";
import { Cifra, Velo } from "./Comunes";
import { C, M, fontFamily, resorte, tramo } from "./estilo";

type P = { dur: number };

// Fondo de video estirado a la duración de la escena
const Fondo: React.FC<{ src: string; segundos: number; dur: number; oscuro?: number }> = ({ src, segundos, dur, oscuro = 0 }) => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill>
      <Video src={staticFile(src)} muted playbackRate={(segundos * fps) / dur} objectFit="cover" style={{ width: "100%", height: "100%" }} />
      {oscuro > 0 && <AbsoluteFill style={{ background: `rgba(12,14,17,${oscuro})` }} />}
    </AbsoluteFill>
  );
};

// 1. Titulares: cada uno entra desde abajo; los anteriores suben, se achican y se apagan
export const Titulares: React.FC<P> = ({ dur }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tit = datos.titulares;
  const paso = Math.round(dur * 0.17);
  const entradas = tit.map((_, i) => 8 + i * paso);
  return (
    <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 35%, #2a1408 0%, ${C.fondo} 60%)`, fontFamily }}>
      {tit.map((s, i) => {
        const a = resorte(f, fps, entradas[i], 22);
        if (f < entradas[i]) return null;
        const atras = entradas.slice(i + 1).reduce((x, e) => x + resorte(f, fps, e, 26), 0);
        const salida = Math.max(0, atras - 1.6);
        return (
          <div
            key={s.img}
            style={{
              position: "absolute", left: M, right: M, top: 520, padding: "30px 34px 34px", borderRadius: 22, background: "#fff",
              boxShadow: "0 30px 80px rgba(0,0,0,.55)", transformOrigin: "50% 0%",
              translate: `0px ${(1 - a) * 700 - atras * 120}px`,
              scale: String(1 - 0.07 * atras),
              rotate: `${(1 - a) * (i % 2 ? 4 : -4)}deg`,
              opacity: Math.max(0, 1 - salida) * (a > 0 ? 1 : 0),
              filter: `brightness(${1 - 0.35 * Math.min(atras, 1.5)})`,
              zIndex: i,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 30, fontWeight: 800, marginBottom: 18 }}>
              <span style={{ color: "#b3300a" }}>{s.medio.toUpperCase()}</span>
              <span style={{ color: "#666", fontWeight: 600 }}>{s.fecha}</span>
            </div>
            <Img src={staticFile(`titulares/${s.img}`)} style={{ width: "100%", display: "block" }} />
          </div>
        );
      })}
      <AbsoluteFill style={{ background: `linear-gradient(to bottom, rgba(12,14,17,0) 1050px, ${C.fondo} 1180px)` }} />
      <Cifra valor={2890} etiqueta="fallecidos en siniestros de tránsito en 2025" desde={Math.round(dur * 0.68)} />
    </AbsoluteFill>
  );
};

// 2. Vuelo de Lima a la Panamericana Norte en Comas
export const Comas: React.FC<P> = ({ dur }) => (
  <AbsoluteFill>
    <Fondo src="clips/comas.mp4" segundos={12.5} dur={dur} />
    <Velo />
    <Etiqueta texto="Panamericana Norte · Comas" desde={Math.round(dur * 0.45)} />
    <Cifra valor={17} etiqueta="fallecidos en un tramo de 200 metros, de 2021 a 2024" desde={Math.round(dur * 0.55)} />
  </AbsoluteFill>
);

const Etiqueta: React.FC<{ texto: string; desde: number }> = ({ texto, desde }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = resorte(f, fps, desde);
  return (
    <div style={{ position: "absolute", left: M, top: 190, fontFamily, fontSize: 40, fontWeight: 700, color: C.tinta, opacity: a, translate: `${-30 * (1 - a)}px 0px`,
      background: "rgba(12,14,17,.75)", padding: "12px 22px", borderRadius: 14, borderLeft: `6px solid ${C.acento}` }}>
      {texto}
    </div>
  );
};

// 3. El Perú: siniestros año por año, las columnas de los puntos negros y, desde "Casi la mitad", Lima con la Panamericana
export const Peru: React.FC<P> = ({ dur }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const casi = datos.subtitulos.flatMap((b) => b.palabras).find((p) => p.t === "Casi" && p.ini > datos.cortes[2]);
  const cambio = Math.min(dur - fps, Math.round(((casi?.ini ?? datos.cortes[3]) - datos.cortes[2]) * fps) + 6);
  const fuente = (f / cambio) * 10.93; // segundo del clip del Perú
  const anio = 2021 + Math.min(4, Math.floor(fuente));
  const a = 1 - tramo(fuente, 4.8, 5.4);
  const sale = 1 - tramo(f, cambio - 8, cambio + 4);
  return (
    <AbsoluteFill>
      <Sequence durationInFrames={cambio + 10}><Fondo src="clips/peru.mp4" segundos={10.93} dur={cambio} /></Sequence>
      <Sequence from={cambio - 10}>
        <AbsoluteFill style={{ opacity: tramo(f, cambio - 10, cambio + 4) }}><Fondo src="clips/lima.mp4" segundos={10.43} dur={dur - cambio + 10} /></AbsoluteFill>
      </Sequence>
      <Velo />
      <div style={{ position: "absolute", left: M, top: 190, fontFamily, opacity: a * resorte(f, fps, 4) }}>
        <div style={{ fontSize: 120, fontWeight: 800, color: C.tinta, letterSpacing: -3 }}>{anio}</div>
        <div style={{ fontSize: 36, color: C.suave, fontWeight: 500 }}>cada punto es un siniestro fatal</div>
      </div>
      <AbsoluteFill style={{ opacity: sale }}>
        <Cifra valor={286} etiqueta="puntos negros, lugares con 3 o más siniestros fatales en 200 metros" desde={Math.round(cambio * 0.5)} />
      </AbsoluteFill>
      <Sequence from={cambio}>
        <Cifra valor={125} etiqueta="de los 286 puntos negros están sobre la Panamericana" desde={4} />
      </Sequence>
    </AbsoluteFill>
  );
};

// 4. No es casualidad: lugares con 5 o más siniestros, en la realidad y al azar
export const Azar: React.FC<P> = ({ dur }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const barra = (valor: number, color: string, texto: string, desde: number) => {
    const a = resorte(f, fps, desde, 30);
    return (
      <div style={{ marginTop: 34, opacity: Math.min(1, a * 2) }}>
        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          <div style={{ height: 96, width: `${(valor / 55) * 70 * a}%`, background: color, borderRadius: 14 }} />
          <span style={{ fontSize: 96, fontWeight: 800, color, letterSpacing: -3 }}>{Math.round(valor * a)}</span>
        </div>
        <div style={{ fontSize: 40, color: C.tinta, fontWeight: 500, marginTop: 12 }}>{texto}</div>
      </div>
    );
  };
  return (
    <AbsoluteFill>
      <Fondo src="clips/filtro.mp4" segundos={8.43} dur={dur} oscuro={0.35} />
      <Velo />
      <div style={{ position: "absolute", left: M, right: M, top: 880, fontFamily }}>
        <div style={{ fontSize: 44, fontWeight: 700, color: C.tinta, opacity: resorte(f, fps, 6) }}>Lugares con 5 o más siniestros fatales</div>
        {barra(55, C.acento, "en la realidad", Math.round(dur * 0.2))}
        {barra(31, "#9aa1ab", "si se repartieran al azar en la misma vía", Math.round(dur * 0.42))}
      </div>
    </AbsoluteFill>
  );
};

// 5. El Gobierno ya los había identificado: 83 tramos, 61 volvieron a tener siniestros fatales
export const Ministerio: React.FC<P> = ({ dur }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const lado = 62, gap = 12, cols = 10;
  const x0 = (1080 - cols * (lado + gap) + gap) / 2;
  const pinta = tramo(f, dur * 0.42, dur * 0.66);
  const fin = resorte(f, fps, Math.round(dur * 0.8));
  const n61 = Math.round(61 * pinta);
  const cifra = (valor: string, l1: string, l2: string, op: number) => (
    <div style={{ position: "absolute", left: M, top: 1170, display: "flex", alignItems: "center", gap: 30, opacity: op }}>
      <span style={{ fontSize: 170, fontWeight: 800, color: C.acento, letterSpacing: -6, lineHeight: 1 }}>{valor}</span>
      <span style={{ fontSize: 44, color: C.tinta, lineHeight: 1.2 }}>{l1}<br /><b>{l2}</b></span>
    </div>
  );
  return (
    <AbsoluteFill style={{ background: C.fondo, fontFamily }}>
      <div style={{ position: "absolute", left: M, right: M, top: 220, opacity: resorte(f, fps, 0) }}>
        <div style={{ fontSize: 36, fontWeight: 600, color: C.suave }}>En 2022 el Gobierno identificó</div>
        <div style={{ fontSize: 84, fontWeight: 800, color: C.tinta, letterSpacing: -3, lineHeight: 1.05, marginTop: 8, whiteSpace: "nowrap" }}>83 tramos peligrosos</div>
      </div>
      {Array.from({ length: 83 }, (_, k) => {
        const a = resorte(f, fps, 6 + k * 0.9, 20);
        const naranja = k < n61;
        return (
          <div key={k} style={{ position: "absolute", left: x0 + (k % cols) * (lado + gap), top: 420 + Math.floor(k / cols) * (lado + gap),
            width: lado, height: lado, borderRadius: 14, background: naranja ? C.acento : C.gris, scale: String(a),
            boxShadow: naranja ? "0 0 24px rgba(234,88,12,.45)" : "none" }} />
        );
      })}
      {n61 > 0 && cifra(String(n61), "volvieron a tener", "siniestros fatales", 1 - fin)}
      {cifra("203", "fallecidos", "desde entonces", fin)}
    </AbsoluteFill>
  );
};

// 6. Desde el satélite: punto negro y la misma vía 1.5 km después
const PARES = [
  { n: 59, lugar: "Lurín · Panamericana Sur", m: 10 },
  { n: 191, lugar: "Yungay · Carretera PE-3N", m: 7 },
  { n: 170, lugar: "Guadalupe · Panamericana Norte", m: 7 },
];
export const Satelite: React.FC<P> = ({ dur }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tramoPar = (dur * 0.62) / PARES.length;
  const i = Math.min(PARES.length - 1, Math.floor(f / tramoPar));
  const p = PARES[i];
  const t0 = i * tramoPar;
  const a = resorte(f, fps, t0, 22);
  const lado = (1080 - 2 * M - 24) / 2;
  const foto = (src: string, x: number, borde: string, retraso: number) => {
    const b = resorte(f, fps, t0 + retraso, 22);
    return (
      <div style={{ position: "absolute", left: x, top: 420, width: lado, height: lado, borderRadius: 18, overflow: "hidden", border: `5px solid ${borde}`, opacity: b, translate: `0px ${60 * (1 - b)}px` }}>
        <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", scale: String(1.15 - 0.1 * tramo(f, t0, t0 + tramoPar)) }} />
      </div>
    );
  };
  return (
    <AbsoluteFill style={{ background: C.fondo, fontFamily }}>
      <div style={{ position: "absolute", left: M, right: M, top: 220, opacity: a }}>
        <div style={{ fontSize: 52, fontWeight: 800, color: C.tinta }}>{p.lugar}</div>
        <div style={{ fontSize: 36, color: C.suave, marginTop: 6 }}>{p.m} fallecidos en 200 metros</div>
      </div>
      {foto(`sat/sat_${p.n}_pn.jpg`, M, C.acento, 0)}
      {foto(`sat/sat_${p.n}_ctrl.jpg`, M + lado + 24, "transparent", 5)}
      <div style={{ position: "absolute", left: M, top: 420 + lado + 18, fontSize: 36, fontWeight: 800, color: C.acento, opacity: a }}>Punto negro</div>
      <div style={{ position: "absolute", left: M + lado + 24, top: 420 + lado + 18, fontSize: 32, color: C.suave, opacity: a }}>1.5 km después, sin siniestros</div>
      <Cifra texto="1 de cada 2" etiqueta="son atropellos, con paraderos y comercio a pocos metros" desde={Math.round(dur * 0.45)} />
    </AbsoluteFill>
  );
};

// 7. Cierre: la pregunta sobre el dashboard oscurecido
export const Cierre: React.FC<P> = ({ dur }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = resorte(f, fps, 4, 16);
  const b = resorte(f, fps, 20);
  return (
    <AbsoluteFill style={{ fontFamily }}>
      <Fondo src="clips/dashboard.mp4" segundos={Math.min(17.9, dur / fps)} dur={dur} oscuro={interpolate(f, [0, 10], [0.3, 0.88], { extrapolateRight: "clamp" })} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", textAlign: "center", paddingBottom: 300 }}>
        <div style={{ fontSize: 112, fontWeight: 800, color: C.tinta, lineHeight: 1.05, letterSpacing: -3, scale: String(0.85 + 0.15 * a), opacity: a }}>
          ¿Hay uno en
          <br />
          tu ruta diaria?
        </div>
        <div style={{ marginTop: 50, fontSize: 52, fontWeight: 700, color: C.acento, opacity: b }}>Revisa el dashboard</div>
        <div style={{ marginTop: 14, fontSize: 40, color: C.suave, opacity: b }}>Enlace en la publicación</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// Créditos al final, con música sola
export const Creditos: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tit = datos.titulares.map((s) => `${s.medio} (${s.fecha.slice(-4)})`).join(", ");
  const filas: [string, string][] = [
    ["Datos", datos.fuente.replace(/;/g, ",")],
    ["Titulares", tit],
    ["Voz", "generada con IA (Qwen3-TTS) a partir de la voz del autor"],
    ["Música", "“Floating Cities”, Kevin MacLeod (incompetech.com), CC BY 4.0"],
    ["Autor", "Nicolás Silva Andújar"],
  ];
  return (
    <AbsoluteFill style={{ background: C.fondo, fontFamily, padding: `260px ${M}px` }}>
      {filas.map(([k, v], i) => {
        const a = resorte(f, fps, i * 4);
        return (
          <div key={k} style={{ marginBottom: 44, opacity: a, translate: `0px ${20 * (1 - a)}px` }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: C.suave, letterSpacing: 2 }}>{k.toUpperCase()}</div>
            <div style={{ fontSize: 38, color: C.tinta, marginTop: 8, lineHeight: 1.3 }}>{v}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

