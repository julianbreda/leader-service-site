/* Leader Service site behaviour. Config is injected by the build as window.LS_CONFIG. */
(function(){
  var C = window.LS_CONFIG || {};
  // Lead destination comes from /lead-config.js (window.LS_LEADS), not from the build.
  var L = window.LS_LEADS || {}, target = (L.endpoints || {})[L.use] || '';
  C.leadEndpoint = target; C.leadKey = L.key || ''; C.web3formsKey = L.emailBackupKey || '';

  // Old hash URLs (#/privacy-policy etc.) from the single-page site -> real pages
  var h = location.hash;
  if (h && h.indexOf('#/') === 0) {
    var map = C.legacyRoutes || {}, key = h.slice(2).replace(/\/$/, '');
    if (map[key] !== undefined) { location.replace(map[key]); return; }
  }

  var nav = document.getElementById('nav'), menu = document.getElementById('mobileMenu');
  var isHome = document.body.classList.contains('is-home');
  function updateNav(){ if(!isHome) nav.classList.add('solid'); else nav.classList.toggle('solid', window.scrollY > 40); }
  window.addEventListener('scroll', updateNav, {passive:true}); updateNav();

  // reveal-on-scroll
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function(es){ es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } }); }, {threshold:.12});
    document.querySelectorAll('.r, .band-div').forEach(function(el){ io.observe(el); });
  } else { document.querySelectorAll('.r, .band-div').forEach(function(el){ el.classList.add('in'); }); }

  document.getElementById('burger').addEventListener('click', function(){
    var open = menu.classList.toggle('open'); document.body.classList.toggle('menu-open', open);
  });
  menu.addEventListener('click', function(e){ if(e.target.closest('a')){ menu.classList.remove('open'); document.body.classList.remove('menu-open'); } });

  // Residential / Commercial toggles
  document.querySelectorAll('.seg-toggle').forEach(function(tog){
    var group = tog.dataset.seg;
    tog.querySelectorAll('.seg-btn').forEach(function(btn){
      btn.addEventListener('click', function(){
        var val = btn.dataset.segVal;
        document.querySelectorAll('.seg-toggle[data-seg="'+group+'"] .seg-btn').forEach(function(b){
          var on = b.dataset.segVal === val; b.classList.toggle('active', on); b.setAttribute('aria-selected', on);
        });
        document.querySelectorAll('.seg-panel[data-seg-panel]').forEach(function(p){
          var m = p.dataset.segPanel === val; p.hidden = !m;
          if (m) p.querySelectorAll('.r').forEach(function(el){ el.classList.add('in'); });
        });
      });
    });
  });

  // ---- attribution: remember first-touch UTM / click ids for the lead ----
  var ATTR_KEYS = ['utm_source','utm_medium','utm_campaign','utm_term','utm_content','gclid','fbclid','msclkid'];
  function store(k, v){ try { localStorage.setItem(k, v); } catch(e){} }
  function load(k){ try { return localStorage.getItem(k); } catch(e){ return null; } }
  (function(){
    var q = new URLSearchParams(location.search), got = {};
    ATTR_KEYS.forEach(function(k){ if (q.get(k)) got[k] = q.get(k); });
    if (Object.keys(got).length) store('ls_attr', JSON.stringify(got));
    if (!load('ls_landing')) { store('ls_landing', location.pathname); store('ls_referrer', document.referrer || ''); }
  })();

  // ---- booking / lead form ----
  document.querySelectorAll('form.lead-form').forEach(function(f){
    var bars = f.querySelectorAll('.book-steps .ps'), stepNum = f.querySelector('.stepNum');
    var msg = f.querySelector('.formmsg'), btn = f.querySelector('button[type=submit]'), label = btn.textContent;
    function steps(done){
      var s = done ? 3 : ((f.name.value.trim()?1:0) + (f.phone.value.trim()?1:0));
      bars.forEach(function(b,i){ b.classList.toggle('on', i < s); });
      if (stepNum) stepNum.textContent = done ? 3 : Math.min(3, s+1);
    }
    f.addEventListener('input', function(){ steps(false); }); steps(false);
    var note = f.querySelector('.emerg-note');
    if (note) f.urgency.addEventListener('change', function(){ note.hidden = !/Emergency/.test(f.urgency.value); });

    function say(text, err){ msg.textContent = text; msg.style.display = 'block'; msg.classList.toggle('err', !!err); }

    f.addEventListener('submit', function(e){
      e.preventDefault();
      if (f.website && f.website.value) return; // honeypot: bots fill hidden field
      if (!f.name.value.trim()) { f.name.focus(); return; }
      var phone = f.phone.value.replace(/\D/g,'');
      if (phone.length < 10) { f.phone.focus(); say('Please enter a 10-digit phone number so we can call you back.', true); return; }
      var smsBox = f.querySelector('[name=sms_consent]');
      var lead = {
        source: 'website',
        site: location.hostname,
        submitted_at: new Date().toISOString(),
        name: f.name.value.trim(),
        phone: f.phone.value.trim(),
        email: (f.email && f.email.value.trim()) || '',
        address: (f.address && f.address.value.trim()) || '',
        city: (f.city && f.city.value.trim()) || '',
        postal_code: (f.postal_code && f.postal_code.value.trim().toUpperCase()) || '',
        service: f.service.value,
        urgency: f.urgency.value,
        message: (f.message && f.message.value.trim()) || '',
        property_type: /Commercial|Mechanical/.test(f.service.value) ? 'commercial' : 'residential',
        page_url: location.href,
        page_title: document.title,
        landing_page: load('ls_landing') || '',
        referrer: load('ls_referrer') || '',
        attribution: JSON.parse(load('ls_attr') || '{}'),
        sms_consent: !!(smsBox && smsBox.checked),
        sms_consent_text: smsBox ? smsBox.parentNode.querySelector('.consent-text').textContent.replace(/\s+/g,' ').trim() : '',
        consent_disclosure_version: (f.consent_disclosure_version || {}).value || '',
        consent_timestamp: smsBox && smsBox.checked ? new Date().toISOString() : ''
      };
      btn.disabled = true; btn.textContent = 'Sending…';
      send(lead).then(function(){
        steps(true); btn.textContent = 'Request received ✓';
        say('Thank you — a Leader Service coordinator will call you shortly to confirm. For emergencies, call ' + C.phone + '.');
        f.querySelectorAll('input,select,textarea,button').forEach(function(el){ el.disabled = true; });
        if (window.gtag) gtag('event', 'generate_lead', {service: lead.service, urgency: lead.urgency});
      }).catch(function(){
        btn.disabled = false; btn.textContent = label;
        say('Sorry — your request could not be sent. Please call ' + C.phone + ' or email ' + C.email + ' and we will look after you right away.', true);
      });
    });
  });

  // Primary: Leaders Hub webhook. Backup: email via Web3Forms. Both optional, configured at build.
  function post(url, body, headers){
    return fetch(url, {method:'POST', headers: Object.assign({'Content-Type':'application/json','Accept':'application/json'}, headers||{}), body: JSON.stringify(body)})
      .then(function(r){ if(!r.ok) throw new Error(r.status); return r; });
  }
  function emailBackup(lead){
    if (!C.web3formsKey) return Promise.reject(new Error('no backup'));
    return post('https://api.web3forms.com/submit', Object.assign({access_key: C.web3formsKey, subject: 'Website lead: ' + lead.service + ' — ' + lead.name, from_name: 'ldrservice.com'}, flat(lead)));
  }
  function flat(o){ var r = {}; for (var k in o) r[k] = typeof o[k] === 'object' ? JSON.stringify(o[k]) : o[k]; return r; }
  function send(lead){
    if (C.leadEndpoint) {
      var hdr = C.leadKey ? {'X-Lead-Key': C.leadKey} : {};
      return post(C.leadEndpoint, lead, hdr).then(function(r){ if (C.web3formsKey) emailBackup(lead).catch(function(){}); return r; })
        .catch(function(){ return emailBackup(lead); });
    }
    return emailBackup(lead);
  }

  // call tracking event
  document.addEventListener('click', function(e){
    var a = e.target.closest('a[href^="tel:"]');
    if (a && window.gtag) gtag('event', 'click_to_call', {location: a.dataset.loc || 'page'});
  });
})();
