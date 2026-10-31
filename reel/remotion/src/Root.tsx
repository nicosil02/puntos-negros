import { Composition } from "remotion";
import datos from "./datos.json";
import { CREDITOS, Reel } from "./Reel";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition id="Reel" component={Reel} durationInFrames={Math.round((datos.habla + CREDITOS) * 30)} fps={30} width={1080} height={1920} />
  );
};
