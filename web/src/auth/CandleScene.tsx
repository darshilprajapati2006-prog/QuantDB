import { useMemo } from 'react';

type Candle = { x: number; y: number; h: number; wick: number; green: boolean; delay: number; depth: number };

export function CandleScene() {
  const candles = useMemo<Candle[]>(() => Array.from({ length: 48 }, (_, index) => {
    const trend = 52 + Math.sin(index * 0.28) * 15 + Math.sin(index * 0.09) * 18 - index * 0.32;
    return { x: 12 + index * 24, y: Math.max(6, Math.min(180, trend + Math.sin(index * 2.13) * 9)), h: 10 + Math.abs(Math.cos(index * 1.71)) * 20, wick: 8 + Math.abs(Math.sin(index * 0.63)) * 18, green: Math.sin(index * 1.91) > -0.18, delay: (index % 13) * -0.24, depth: 0.55 + ((index * 7) % 12) / 20 };
  }), []);
  return <div className="auth-candle-scene" aria-hidden="true"><div className="candle-scene-grid"/><div className="candle-scene-glow"/><div className="candle-scene-perspective">{candles.map((candle,index)=><span key={index} className={`scene-candle ${candle.green?'up':'down'}`} style={{left:`${candle.x/12}%`,top:`${candle.y/2}%`,height:candle.h,opacity:candle.depth,animationDelay:`${candle.delay}s`,'--wick':`${candle.wick}px`} as React.CSSProperties}/>)}</div><span className="scene-market-label">QUANTDB · MARKET SIMULATION</span></div>;
}
