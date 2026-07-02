// The diorama room (HS-71-01's atmosphere, React-hosted): the DioPal
// gradient + the pulsing warm spotlight (CSS) and the rising dust motes
// (one cheap rAF over ~18 specks — the same DioMotes port, lifecycle-managed).
import { useEffect, useRef } from "react";

export function Stage() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let w = 0;
    let h = 0;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const N = 18;
    const motes = Array.from({ length: N }, () => ({
      x: Math.random(), y: Math.random(),
      r: 0.6 + Math.random() * 1.6,
      s: 0.006 + Math.random() * 0.014,
      a: 0.06 + Math.random() * 0.12,
      drift: (Math.random() - 0.5) * 0.01,
    }));
    function resize() {
      if (!canvas || !ctx) return;
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    function draw(dt: number) {
      if (!ctx) return;
      ctx.clearRect(0, 0, w, h);
      for (const m of motes) {
        if (!reduce) {
          m.y -= m.s * dt;
          m.x += m.drift * dt;
          if (m.y < -0.02) {
            m.y = 1.02;
            m.x = Math.random();
          }
        }
        ctx.beginPath();
        ctx.arc(m.x * w, m.y * h, m.r, 0, 6.283);
        ctx.fillStyle = "rgba(255,246,238," + m.a + ")";
        ctx.fill();
      }
    }
    let raf = 0;
    let last = 0;
    function loop(t: number) {
      const dt = Math.min((t - last) / 1000, 0.05);
      last = t;
      draw(dt);
      if (!reduce) raf = requestAnimationFrame(loop);
    }
    resize();
    window.addEventListener("resize", resize);
    raf = requestAnimationFrame(loop);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <div className="desk-stage" aria-hidden="true">
      <div className="desk-stage-glow" />
      <canvas ref={canvasRef} className="desk-stage-motes" />
    </div>
  );
}
