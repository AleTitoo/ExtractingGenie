(function(){
function mount(host){if(host.shadowRoot)return;const root=host.attachShadow({mode:"open"});root.innerHTML="<style>:host{display:inline-block}svg{display:block;width:100%;height:100%;overflow:visible}</style><svg id=\"icon\" viewBox=\"0 0 256 256\" role=\"img\" aria-label=\"Animated Platinum-189 icon with randomly orbiting electrons on two shells\">\n<defs>\n<linearGradient id=\"blue\" x1=\"28\" y1=\"220\" x2=\"220\" y2=\"28\" gradientUnits=\"userSpaceOnUse\"><stop stop-color=\"#2563eb\"/><stop offset=\".55\" stop-color=\"#159be9\"/><stop offset=\"1\" stop-color=\"#52d9ee\"/></linearGradient>\n<radialGradient id=\"nucleus\"><stop stop-color=\"#73e4f3\"/><stop offset=\"1\" stop-color=\"#229de4\"/></radialGradient>\n<filter id=\"glow\" x=\"-150%\" y=\"-150%\" width=\"400%\" height=\"400%\"><feGaussianBlur stdDeviation=\"2.6\"/></filter>\n</defs>\n<g fill=\"none\" stroke=\"url(#blue)\" stroke-width=\"2.3\"><circle cx=\"128\" cy=\"128\" r=\"77\"/><circle cx=\"128\" cy=\"128\" r=\"98\"/></g>\n<g id=\"nucleons\" opacity=\".2\" fill=\"url(#nucleus)\" transform=\"translate(128 128) scale(.8) translate(-128 -112)\"></g>\n<text x=\"128\" y=\"137\" text-anchor=\"middle\" font-family=\"Segoe UI,Arial,sans-serif\" font-weight=\"600\" font-size=\"25\" fill=\"#69d7ef\">Pt<tspan font-size=\"12\" baseline-shift=\"super\" dx=\"2\">189</tspan></text>\n<g id=\"electrons\"></g><g id=\"sparks\" pointer-events=\"none\"></g>\n</svg>";

const ns='http://www.w3.org/2000/svg';
function element(tag,attrs,parent){const node=document.createElementNS(ns,tag);for(const [key,value] of Object.entries(attrs))node.setAttribute(key,value);parent.append(node);return node;}
const nucleus=root.querySelector('#nucleons');
for(const [y,xs] of [[76,[108,128,148]],[94,[98,118,138,158]],[112,[88,108,128,148,168]],[130,[98,118,138,158]],[148,[108,128,148]]])for(const x of xs)element('circle',{cx:x,cy:y,r:11.5},nucleus);
const random=(a,b)=>a+Math.random()*(b-a),smooth=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t)};
function orbitSpeeds(){const direction=Math.random()<.5?-1:1;return{innerSpeed:random(.12,.23)*direction,outerSpeed:random(.46,.68)*direction};}
const container=root.querySelector('#electrons'),sparkLayer=root.querySelector('#sparks');
let time=0,last=0,running=!matchMedia('(prefers-reduced-motion: reduce)').matches,nextJump=1.5,excited=null;
const electrons=Array.from({length:18},(_,index)=>{const group=element('g',{},container);const glow=element('circle',{r:index===17?13:9,fill:'#a8efff',filter:'url(#glow)',opacity:0},group);const ball=element('circle',{r:index===17?9:5.5,fill:index===17?'#70e3f3':'url(#blue)'},group);return{index,group,glow,ball,angle:index===17?-Math.PI*.22:-Math.PI/2+index*2*Math.PI/17,radius:index===17?98:77,...orbitSpeeds(),flash:-10,opacity:1,x:0,y:0,hop:null,dodge:null,relocated:false};});
function startJump(){if(excited)return;const choices=electrons.slice(0,17).filter(e=>e.opacity>.85&&e.dodge===null);if(!choices.length){nextJump=time+.3;return;}excited=choices[Math.floor(Math.random()*choices.length)];excited.hop=time;nextJump=Infinity;}
function relocate(e){const radius=e.index===17?98:77;let best=e.angle,bestClearance=-Infinity;for(let attempt=0;attempt<100;attempt++){const angle=random(0,Math.PI*2),x=128+radius*Math.cos(angle),y=128+radius*Math.sin(angle);let clearance=Infinity;for(const other of electrons){if(other===e||other.opacity<.1)continue;const size=(e.index===17?9:5.5)+(other.index===17?9:5.5);clearance=Math.min(clearance,Math.hypot(x-other.x,y-other.y)-size);}if(clearance>bestClearance){best=angle;bestClearance=clearance;}if(clearance>6)break;}e.angle=best;Object.assign(e,orbitSpeeds());e.relocated=true;}
const pairCooldown=new Map(),sparks=[];
function spark(x,y){if(sparks.length>16)return;const node=element('g',{transform:`translate(${x} ${y})`,stroke:'#72bdd4','stroke-width':.8,'stroke-linecap':'round'},sparkLayer);element('path',{d:'M-2 0H2 M0-2V2'},node);sparks.push({node,born:time});}
function update(dt){time+=dt;
 if(time>=nextJump)startJump();
 for(const e of electrons){
  e.opacity=1;
  if(e.dodge!==null){const age=time-e.dodge;if(age<.11)e.opacity=1-smooth(age/.11);else{if(!e.relocated)relocate(e);e.opacity=age<.16?0:smooth((age-.16)/.22);}if(age>=.38){e.dodge=null;e.relocated=false;e.opacity=1;}}
  e.radius=e.index===17?98:77;
  if(e.hop!==null){const progress=time-e.hop;if(progress<.85)e.radius=77+21*smooth(progress/.85);else if(progress<1.55)e.radius=98;else if(progress<2.45)e.radius=98-21*smooth((progress-1.55)/.9);else{e.radius=77;e.hop=null;excited=null;nextJump=time+random(1.2,2.5);}}
  const shellBlend=Math.max(0,Math.min(1,(e.radius-77)/21));const velocity=e.innerSpeed+(e.outerSpeed-e.innerSpeed)*shellBlend;e.angle+=velocity*dt;e.x=128+e.radius*Math.cos(e.angle);e.y=128+e.radius*Math.sin(e.angle);e.group.setAttribute('transform',`translate(${e.x} ${e.y})`);e.group.setAttribute('opacity',e.opacity);
  const jumpAge=e.hop===null?-1:time-e.hop;const red=jumpAge>=0&&jumpAge<.85?Math.sin(Math.PI*jumpAge/.85):jumpAge>=1.55&&jumpAge<2.45?Math.sin(Math.PI*(jumpAge-1.55)/.9):0;const flash=Math.max(0,1-(time-e.flash)/.16);e.ball.setAttribute('fill',red>0?'#cd7180':e.index===17?'#70e3f3':'url(#blue)');e.glow.setAttribute('fill',red>0?'#cd7180':'#72bdd4');e.glow.setAttribute('opacity',Math.max(red*.12,flash*.09));
 }
 for(let i=0;i<electrons.length;i++)for(let j=i+1;j<electrons.length;j++){const a=electrons[i],b=electrons[j],key=i+':'+j;if(a.opacity<.45||b.opacity<.45||a.dodge!==null||b.dodge!==null)continue;const distance=Math.hypot(a.x-b.x,a.y-b.y),threshold=(a.index===17?9:5.5)+(b.index===17?9:5.5);if(distance<threshold&&time-(pairCooldown.get(key)??-10)>.4){a.flash=b.flash=time;pairCooldown.set(key,time);spark((a.x+b.x)/2,(a.y+b.y)/2);const choices=[a,b].filter(e=>e.hop===null);if(choices.length){const avoid=choices[Math.floor(Math.random()*choices.length)];avoid.dodge=time;avoid.relocated=false;}}}
 for(let i=sparks.length-1;i>=0;i--){const s=sparks[i],age=time-s.born;s.node.setAttribute('opacity',.18*Math.max(0,1-age/.16));if(age>.16){s.node.remove();sparks.splice(i,1);}}
}
const motion=matchMedia('(prefers-reduced-motion: reduce)');motion.addEventListener('change',e=>{running=!e.matches;last=0;});
function frame(now){const dt=last?Math.min(.05,(now-last)/1000):0;last=now;if(running&&!document.hidden)update(dt);requestAnimationFrame(frame);}update(0);requestAnimationFrame(frame);

}
window.PlatinumIcon={mount};document.querySelectorAll("[data-platinum-icon]").forEach(mount);
})();
