/* BusJatri — language persistence, shared with the static SEO pages.
   Loaded after app.js; reads/writes the same localStorage key ('bj-lang')
   so one EN/বাংলা choice carries across the whole site. */
(function () {
  var saved = null;
  try { saved = localStorage.getItem('bj-lang'); } catch (e) {}
  if (saved === 'bn' || saved === 'en') LANG = saved;
  else if ((navigator.language || '').toLowerCase().indexOf('bn') === 0) LANG = 'bn';

  document.body.className = LANG === 'bn' ? 'lang-bn' : '';
  var e = document.getElementById('langEN'), b = document.getElementById('langBN');
  if (e) e.classList.toggle('active', LANG === 'en');
  if (b) b.classList.toggle('active', LANG === 'bn');
  document.documentElement.setAttribute('lang', LANG === 'bn' ? 'bn' : 'en');

  var _setLang = window.setLang;
  if (_setLang) {
    window.setLang = function (l) {
      try { localStorage.setItem('bj-lang', l); } catch (err) {}
      _setLang(l);
      document.documentElement.setAttribute('lang', l === 'bn' ? 'bn' : 'en');
    };
  }
})();
