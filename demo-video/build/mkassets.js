const fs=require('fs'),path=require('path'),QR=require('qrcode');
const names=['shield-check','trending-up','refresh-cw','users','eye','star','monitor-smartphone','clipboard-check','phone','camera','mic','plus','chevron-left','triangle-alert','zap','cloud','globe','chart-column','check','video','monitor','square-user','scan-face','message-circle','phone-off','arrow-right','user-round','book-user','tv-minimal','file-text','sparkles','badge-check','signal','wifi','battery-full','check-check','image','map-pin','ellipsis-vertical','search','instagram','facebook','linkedin','circle-check','house','car-front','building-2'];
const out={};
for(const n of names){const p=path.join('node_modules/lucide-static/icons',n+'.svg'); if(fs.existsSync(p)) out[n]=fs.readFileSync(p,'utf8').replace(/<!--.*?-->/s,'').replace(/\n\s*/g,' ').replace(/ width="24" height="24"/,'').replace(/class="[^"]*"/,''); else console.log('missing',n);}
(async()=>{
  const qr={};
  for(const [k,u] of [['demo','https://calendly.com/mukul-singh-chat360/30min'],['site','https://chat360.ai']])
    qr[k]=await QR.toString(u,{type:'svg',margin:0,errorCorrectionLevel:'M',color:{dark:'#0b1020',light:'#ffffff00'}});
  const wa=require('simple-icons').siWhatsapp.path;
  fs.writeFileSync('assets/data.js','window.ICONS='+JSON.stringify(out)+';\nwindow.QRS='+JSON.stringify(qr)+';\nwindow.WA_PATH='+JSON.stringify(wa)+';\nwindow.AVMAP='+fs.readFileSync('../out/avatar_map.json','utf8')+';\nwindow.TL='+fs.readFileSync('../out/timeline.json','utf8')+';\n');
  console.log(Object.keys(out).length,'icons');
})();
