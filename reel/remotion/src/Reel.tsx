import React from "react";
import { Audio } from "@remotion/media";
import { AbsoluteFill, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import datos from "./datos.json";
import { Marco, Subtitulos } from "./Comunes";
import { Azar, Cierre, Comas, Creditos, Ministerio, Peru, Satelite, Titulares } from "./Escenas";
import { C } from "./estilo";

export const CREDITOS = 2.5; // segundos
const CRUCE = 8; // cuadros de fundido entre escenas

// Cada escena entra con un fundido corto sobre la anterior
const Escena: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{ opacity: interpolate(f, [0, CRUCE], [0, 1], { extrapolateRight: "clamp" }) }}>{children}</AbsoluteFill>;
};

export const Reel: React.FC = () => {
  const { fps, durationInFrames } = useVideoConfig();
  const k = datos.cortes.map((c) => Math.round(c * fps));
  const dur = (i: number) => k[i + 1] - k[i] + (i < 6 ? CRUCE : 0);
  const habla = k[7];
  return (
    <AbsoluteFill style={{ background: C.fondo }}>
      <Sequence name="Titulares" from={k[0]} durationInFrames={dur(0)}><Escena><Titulares dur={dur(0)} /></Escena></Sequence>
      <Sequence name="Comas" from={k[1]} durationInFrames={dur(1)}><Escena><Comas dur={dur(1)} /></Escena></Sequence>
      <Sequence name="Perú" from={k[2]} durationInFrames={dur(2)}><Escena><Peru dur={dur(2)} /></Escena></Sequence>
      <Sequence name="No es azar" from={k[3]} durationInFrames={dur(3)}><Escena><Azar dur={dur(3)} /></Escena></Sequence>
      <Sequence name="Ministerio" from={k[4]} durationInFrames={dur(4)}><Escena><Ministerio dur={dur(4)} /></Escena></Sequence>
      <Sequence name="Satélite" from={k[5]} durationInFrames={dur(5)}><Escena><Satelite dur={dur(5)} /></Escena></Sequence>
      <Sequence name="Cierre" from={k[6]} durationInFrames={dur(6)}><Escena><Cierre dur={dur(6)} /></Escena></Sequence>
      <Sequence name="Créditos" from={habla}><Escena><Creditos /></Escena></Sequence>
      <Sequence name="Marco" durationInFrames={habla}><Marco /></Sequence>
      <Subtitulos />
      <Audio name="Narración" src={staticFile("narracion.wav")} />
      <Audio
        name="Música"
        src={staticFile("musica.mp3")}
        volume={(f) => 0.13 * interpolate(f, [0, 1.5 * fps, durationInFrames - 2.5 * fps, durationInFrames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}
      />
    </AbsoluteFill>
  );
};
