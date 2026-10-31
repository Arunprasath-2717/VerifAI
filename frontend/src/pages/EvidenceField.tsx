import { useEffect, useRef } from 'react';
import { Mesh, Program, Renderer, Triangle } from 'ogl';

const vertex = "attribute vec2 uv; attribute vec2 position; varying vec2 vUv; void main(){vUv=uv;gl_Position=vec4(position,0.0,1.0);}";
const fragment = "precision highp float;\nuniform vec2 uResolution;\nuniform vec2 uPointer;\nuniform float uTime;\nvarying vec2 vUv;\nfloat hash(vec2 p){p=fract(p*vec2(123.34,456.21));p+=dot(p,p+45.32);return fract(p.x*p.y);}\nfloat ring(float d,float r,float s){return exp(-abs(d-r)/s);}\nvoid main(){\n vec2 uv=(vUv-.5)*vec2(uResolution.x/max(uResolution.y,1.),1.);\n vec2 p=uv-vec2(.12,.025)-(uPointer-.5)*.07;\n float a=atan(p.y,p.x);\n float d=length(p);\n float t=uTime*.14;\n float warped=d+.022*sin(a*8.+t*2.)+.008*sin(a*17.-t*3.);\n float rings=0.;\n for(int i=0;i<6;i++){float n=float(i);rings+=ring(warped,.24+n*.087+.018*sin(n*2.2+t),.0025+n*.00025)*(.19+n*.013);}\n float halo=exp(-d*d*5.)*.34;\n float beam=pow(max(0.,cos(a*3.-t)),36.)*exp(-d*2.4)*.14;\n vec3 col=vec3(.009,.025,.023);\n col+=vec3(.14,.28,.18)*(rings+halo);\n col+=vec3(.30,.58,.28)*beam;\n col+=vec3(.035,.09,.065)*exp(-pow((p.y+.38+.025*sin(p.x*3.+t))/.09,2.))*.20;\n vec2 grid=floor((uv+vec2(2.))*vec2(36.,23.));\n float star=step(.9967,hash(grid));\n vec2 cell=fract((uv+vec2(2.))*vec2(36.,23.))-.5;\n col+=vec3(.32,.55,.36)*star*exp(-dot(cell,cell)*180.)*.20;\n gl_FragColor=vec4(col,1.);\n}";

// Original GPU atmosphere: a subtle, continuously evolving evidence field.
// The static CSS background remains visible if WebGL is unavailable.
export function EvidenceField() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const host = ref.current;
    if (!host || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    let renderer: Renderer;
    try {
      renderer = new Renderer({ alpha: false, dpr: Math.min(window.devicePixelRatio || 1, 1.5), antialias: false });
    } catch { return; }
    const gl = renderer.gl;
    const program = new Program(gl, {
      vertex, fragment,
      uniforms: {
        uResolution: { value: [1, 1] },
        uTime: { value: 0 },
        uPointer: { value: [0.5, 0.5] },
      },
    });
    const mesh = new Mesh(gl, { geometry: new Triangle(gl), program });
    const canvas = gl.canvas;
    canvas.className = 'vc2-field-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    host.appendChild(canvas);
    let frame = 0;
    let visible = true;
    let previous = 0;
    const target = { x: 0.5, y: 0.5 };
    const pointer = { x: 0.5, y: 0.5 };
    const resize = () => {
      renderer.setSize(Math.max(1, host.clientWidth), Math.max(1, host.clientHeight));
      program.uniforms.uResolution.value = [gl.drawingBufferWidth, gl.drawingBufferHeight];
    };
    const onPointer = (e: PointerEvent) => {
      const b = host.getBoundingClientRect();
      target.x = Math.max(0, Math.min(1, (e.clientX-b.left)/b.width));
      target.y = Math.max(0, Math.min(1, 1-(e.clientY-b.top)/b.height));
    };
    const render = (now: number) => {
      frame = requestAnimationFrame(render);
      if (!visible || document.hidden || now - previous < 30) return;
      previous = now;
      pointer.x += (target.x-pointer.x)*.04;
      pointer.y += (target.y-pointer.y)*.04;
      program.uniforms.uPointer.value = [pointer.x, pointer.y];
      program.uniforms.uTime.value = now*.001;
      renderer.render({ scene: mesh });
    };
    const observer = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; });
    const resizeObserver = new ResizeObserver(resize);
    observer.observe(host);
    resizeObserver.observe(host);
    host.addEventListener('pointermove', onPointer, { passive:true });
    resize();
    frame = requestAnimationFrame(render);
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      resizeObserver.disconnect();
      host.removeEventListener('pointermove', onPointer);
      if (canvas.parentNode === host) host.removeChild(canvas);
      gl.getExtension('WEBGL_lose_context')?.loseContext();
    };
  }, []);
  return <div className="vc2-field" ref={ref} aria-hidden="true" />;
}

