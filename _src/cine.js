(function(){
  var hero=document.getElementById('cineHero'); if(!hero) return;
  var video=document.getElementById('cineVideo');
  video.src='/cine.mp4';
  video.muted=true; video.playsInline=true; try{video.load();}catch(e){}
  var duration=0, ready=false, targetT=0, currT=0, lastSet=-1;
  function isHome(){return true;}
  var cbA=document.getElementById('cbA'),cbB=document.getElementById('cbB'),cbC=document.getElementById('cbC'),cue=document.getElementById('cineCue'),skip=document.getElementById('cineSkip');
  var sky=document.getElementById('cineSky');
  var qL=sky.querySelector('.q-l'),qM=sky.querySelector('.q-m'),qR=sky.querySelector('.q-r');
  var cbBh2=cbB.getElementsByTagName('h2')[0];
  function setP(el,x,y){if(el)el.style.transform='translate('+x.toFixed(1)+'px,'+y.toFixed(1)+'px)';}
  function clamp(v,a,b){return v<a?a:(v>b?b:v);}
  function smooth(a,b,x){x=clamp((x-a)/(b-a),0,1);return x*x*(3-2*x);}
  function band(p,a,b,c,d){return smooth(a,b,p)*(1-smooth(c,d,p));}
  function prog(){var max=hero.offsetHeight-window.innerHeight;return max>0?clamp(window.pageYOffset/max,0,1):0;}
  function beats(p){
    var oA=band(p,0.01,0.03,0.30,0.34), oC=smooth(0.61,0.66,p);
    cbA.style.opacity=oA;cbA.style.transform='translateY('+(1-oA)*22+'px)';
    cbC.style.opacity=oC;cbC.style.transform='translateY('+(1-oC)*22+'px)';
    var gate=band(p,0.30,0.35,0.64,0.68),sep,grow;
    if(p<0.44){sep=1-smooth(0.345,0.44,p);grow=0.12*smooth(0.345,0.44,p);}
    else if(p<=0.53){sep=0;grow=0.12;}
    else{var ex=smooth(0.53,0.61,p);sep=ex;grow=0.12+0.5*ex;}
    var lo=smooth(0.32,0.375,p)*(1-smooth(0.60,0.645,p));
    var tO=band(p,0.43,0.45,0.545,0.57);
    cbB.style.opacity=gate; if(cbBh2)cbBh2.style.opacity=tO;
    sky.style.transform='scale('+(1+grow).toFixed(3)+')'; sky.style.opacity=lo;
    var UX=0.33,UY=-0.95,D=240;
    setP(qL,-UX*D*sep,-UY*D*sep); setP(qM,-UX*D*0.5*sep,-UY*D*0.5*sep); setP(qR,UX*D*sep,UY*D*sep);
    if(cue)cue.style.opacity=(p>0.03)?0:1;
    if(skip){ var so=1-smooth(0.9,0.99,p); skip.style.opacity=so; skip.style.pointerEvents=so<0.05?'none':'auto'; }
  }
  function onScroll(){ if(!isHome())return; var p=prog(); targetT=p*(video.duration||11.13); beats(p); }
  video.addEventListener('loadedmetadata',function(){ duration=video.duration||11.13; onScroll(); });
  video.addEventListener('loadeddata',function(){ ready=true; try{video.currentTime=0.001;}catch(e){} });
  if(skip){ skip.addEventListener('click',function(){ var end=hero.offsetTop+hero.offsetHeight-window.innerHeight; var root=document.documentElement, prev=root.style.scrollBehavior; root.style.scrollBehavior='auto'; window.scrollTo(0,end); root.style.scrollBehavior=prev; if(duration){ targetT=duration; currT=duration; try{video.currentTime=Math.max(0,duration-0.05);}catch(e){} } }); }
  window.addEventListener('scroll',onScroll,{passive:true});
  window.addEventListener('resize',onScroll);
  function tick(){
    var dur=video.duration||0;
    if(isHome() && video.readyState>=2 && dur){
      currT += (targetT-currT)*0.2;
      if(Math.abs(targetT-currT)<0.006) currT=targetT;
      if(Math.abs(currT-lastSet)>0.008){ try{ video.currentTime=clamp(currT,0,dur-0.02); lastSet=currT; }catch(e){} }
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
  onScroll();
})();
