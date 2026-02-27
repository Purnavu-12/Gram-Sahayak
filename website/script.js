/**
 * Gram Sahayak — Interactive Frontend Script
 * Voice-First AI for Rural India
 */
(function () {
  'use strict';

  // --- Theme Toggle ---
  const themeToggle = document.getElementById('theme-toggle');
  const footerThemeToggle = document.getElementById('footer-theme-toggle');
  const themeIcon = themeToggle ? themeToggle.querySelector('.theme-icon') : null;

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (themeIcon) {
      themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
    try {
      localStorage.setItem('gram-sahayak-theme', theme);
    } catch (_) {
      // localStorage unavailable
    }
  }

  function toggleTheme() {
    var current = document.documentElement.getAttribute('data-theme');
    setTheme(current === 'dark' ? 'light' : 'dark');
  }

  // Load saved theme
  try {
    var savedTheme = localStorage.getItem('gram-sahayak-theme');
    if (savedTheme) {
      setTheme(savedTheme);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      setTheme('light');
    } else {
      // Ensure icon is in sync with the inline <head> script's choice
      setTheme(document.documentElement.getAttribute('data-theme') || 'dark');
    }
  } catch (_) {
    // localStorage unavailable
  }

  if (themeToggle) themeToggle.addEventListener('click', toggleTheme);
  if (footerThemeToggle) footerThemeToggle.addEventListener('click', toggleTheme);

  // --- High Contrast Toggle ---
  var highContrastToggle = document.getElementById('high-contrast-toggle');
  if (highContrastToggle) {
    highContrastToggle.addEventListener('click', function () {
      var current = document.documentElement.getAttribute('data-contrast');
      var next = current === 'high' ? '' : 'high';
      document.documentElement.setAttribute('data-contrast', next);
      try {
        localStorage.setItem('gram-sahayak-contrast', next);
      } catch (_) {
        // localStorage unavailable
      }
    });
  }

  // Load saved contrast
  try {
    var savedContrast = localStorage.getItem('gram-sahayak-contrast');
    if (savedContrast) {
      document.documentElement.setAttribute('data-contrast', savedContrast);
    }
  } catch (_) {
    // localStorage unavailable
  }

  // --- Font Size Controls ---
  var currentFontScale = 1;
  try {
    var savedScale = localStorage.getItem('gram-sahayak-font-scale');
    if (savedScale) {
      currentFontScale = parseFloat(savedScale);
      document.documentElement.style.fontSize = (currentFontScale * 100) + '%';
    }
  } catch (_) {
    // localStorage unavailable
  }

  var increaseFontBtn = document.getElementById('increase-font');
  var decreaseFontBtn = document.getElementById('decrease-font');

  if (increaseFontBtn) {
    increaseFontBtn.addEventListener('click', function () {
      if (currentFontScale < 1.5) {
        currentFontScale += 0.1;
        document.documentElement.style.fontSize = (currentFontScale * 100) + '%';
        try { localStorage.setItem('gram-sahayak-font-scale', String(currentFontScale)); } catch (_) {}
      }
    });
  }

  if (decreaseFontBtn) {
    decreaseFontBtn.addEventListener('click', function () {
      if (currentFontScale > 0.8) {
        currentFontScale -= 0.1;
        document.documentElement.style.fontSize = (currentFontScale * 100) + '%';
        try { localStorage.setItem('gram-sahayak-font-scale', String(currentFontScale)); } catch (_) {}
      }
    });
  }

  // --- Mobile Navigation ---
  var hamburger = document.getElementById('hamburger');
  var navLinks = document.querySelector('.nav-links');

  if (hamburger && navLinks) {
    hamburger.addEventListener('click', function () {
      var isOpen = navLinks.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', String(isOpen));
    });

    // Close on link click
    navLinks.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        navLinks.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // --- Animated Counter ---
  function animateCounters() {
    var counters = document.querySelectorAll('[data-count]');
    counters.forEach(function (counter) {
      if (counter.dataset.animated) return;

      var target = parseInt(counter.dataset.count, 10);
      var duration = 2000;
      var start = 0;
      var startTime = null;

      function step(timestamp) {
        if (!startTime) startTime = timestamp;
        var progress = Math.min((timestamp - startTime) / duration, 1);
        // Ease out cubic
        var eased = 1 - Math.pow(1 - progress, 3);
        counter.textContent = Math.floor(eased * target);
        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          counter.textContent = target;
        }
      }

      counter.dataset.animated = 'true';
      requestAnimationFrame(step);
    });
  }

  // --- Intersection Observer for Animations ---
  var observerOptions = { threshold: 0.15, rootMargin: '0px 0px -50px 0px' };

  var scrollObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        // Animate counters when hero stats come into view
        if (entry.target.classList.contains('hero-stats') || entry.target.querySelector('[data-count]')) {
          animateCounters();
        }
      }
    });
  }, observerOptions);

  // Observe elements
  document.querySelectorAll('.feature-card, .scheme-card, .step, .hero-stats, .section-header').forEach(function (el) {
    el.classList.add('animate-on-scroll');
    scrollObserver.observe(el);
  });

  // Trigger counters once hero section is visible
  var heroStats = document.querySelector('.hero-stats');
  if (heroStats) {
    scrollObserver.observe(heroStats);
  }

  // --- Language Wheel Auto-Rotate ---
  var langItems = document.querySelectorAll('.lang-item');
  var activeLangLabel = document.getElementById('active-lang');
  var currentLangIndex = 0;

  function rotateLang() {
    if (langItems.length === 0) return;
    langItems[currentLangIndex].classList.remove('active');
    currentLangIndex = (currentLangIndex + 1) % langItems.length;
    langItems[currentLangIndex].classList.add('active');
    if (activeLangLabel) {
      activeLangLabel.textContent = langItems[currentLangIndex].querySelector('.lang-english').textContent;
    }
  }

  var langInterval = null;
  if (langItems.length > 0) {
    langInterval = setInterval(rotateLang, 2000);
  }

  // Pause rotation on hover
  var langWheel = document.getElementById('language-wheel');
  if (langWheel) {
    langWheel.addEventListener('mouseenter', function () {
      if (langInterval !== null) {
        clearInterval(langInterval);
        langInterval = null;
      }
    });
    langWheel.addEventListener('mouseleave', function () {
      if (langInterval === null && langItems.length > 0) {
        langInterval = setInterval(rotateLang, 2000);
      }
    });
  }

  // --- Multi-Language Chat Conversations ---
  var allChatConversations = {
    en: [
      { type: 'bot', text: 'Hello! 🙏 I am Gram Sahayak. How can I help you today?' },
      { type: 'user', text: 'I want to know about farming schemes' },
      { type: 'bot', text: 'Sure! Let me check your eligibility...' },
      { type: 'bot', text: '✅ You are eligible for 3 schemes:\n• PM-KISAN\n• Crop Insurance\n• Irrigation Subsidy' },
      { type: 'user', text: 'I want to apply for PM-KISAN' },
      { type: 'bot', text: '📝 Done! Your PM-KISAN application is submitted. Track ID: #GS-2026-4821' }
    ],
    hi: [
      { type: 'bot', text: 'नमस्ते! 🙏 मैं ग्राम सहायक हूँ। आज आपकी क्या मदद करूँ?' },
      { type: 'user', text: 'मुझे किसान योजना की जानकारी चाहिए' },
      { type: 'bot', text: 'बिल्कुल! पात्रता जाँच रहा हूँ...' },
      { type: 'bot', text: '✅ आप 3 योजनाओं के पात्र हैं:\n• पीएम-किसान\n• फसल बीमा\n• सिंचाई सब्सिडी' },
      { type: 'user', text: 'पीएम-किसान के लिए आवेदन करना है' },
      { type: 'bot', text: '📝 हो गया! आवेदन जमा हो गया। ट्रैक ID: #GS-2026-4821' }
    ],
    bn: [
      { type: 'bot', text: 'নমস্কার! 🙏 আমি গ্রাম সহায়ক। আজ কীভাবে সাহায্য করতে পারি?' },
      { type: 'user', text: 'কৃষক প্রকল্প সম্পর্কে জানতে চাই' },
      { type: 'bot', text: 'অবশ্যই! যোগ্যতা পরীক্ষা করছি...' },
      { type: 'bot', text: '✅ আপনি ৩টি প্রকল্পের যোগ্য:\n• পিএম-কিসান\n• ফসল বীমা\n• সেচ ভর্তুকি' },
      { type: 'user', text: 'পিএম-কিসানের জন্য আবেদন করতে চাই' },
      { type: 'bot', text: '📝 হয়ে গেছে! আবেদন জমা হয়েছে। ট্র্যাক ID: #GS-2026-4821' }
    ],
    te: [
      { type: 'bot', text: 'నమస్కారం! 🙏 నేను గ్రామ సహాయక్. మీకు ఎలా సహాయం చేయగలను?' },
      { type: 'user', text: 'రైతు పథకాల గురించి తెలుసుకోవాలి' },
      { type: 'bot', text: 'తప్పకుండా! అర్హత తనిఖీ చేస్తున్నాను...' },
      { type: 'bot', text: '✅ మీరు 3 పథకాలకు అర్హులు:\n• పిఎం-కిసాన్\n• పంట బీమా\n• నీటిపారుదల సబ్సిడీ' },
      { type: 'user', text: 'పిఎం-కిసాన్ కోసం దరఖాస్తు చేయాలి' },
      { type: 'bot', text: '📝 పూర్తయింది! దరఖాస్తు సమర్పించబడింది. ట్రాక్ ID: #GS-2026-4821' }
    ],
    mr: [
      { type: 'bot', text: 'नमस्कार! 🙏 मी ग्राम सहायक. आज मी तुम्हाला कशी मदत करू?' },
      { type: 'user', text: 'मला शेतकरी योजनांबद्दल माहिती हवी आहे' },
      { type: 'bot', text: 'नक्कीच! पात्रता तपासत आहे...' },
      { type: 'bot', text: '✅ तुम्ही 3 योजनांसाठी पात्र आहात:\n• पीएम-किसान\n• पीक विमा\n• सिंचन अनुदान' },
      { type: 'user', text: 'पीएम-किसानसाठी अर्ज करायचा आहे' },
      { type: 'bot', text: '📝 झाले! अर्ज सादर झाला. ट्रॅक ID: #GS-2026-4821' }
    ],
    ta: [
      { type: 'bot', text: 'வணக்கம்! 🙏 நான் கிராம சகாயக். உங்களுக்கு எப்படி உதவ முடியும்?' },
      { type: 'user', text: 'விவசாய திட்டங்கள் பற்றி தெரிந்துகொள்ள வேண்டும்' },
      { type: 'bot', text: 'நிச்சயமாக! தகுதியை சரிபார்க்கிறேன்...' },
      { type: 'bot', text: '✅ நீங்கள் 3 திட்டங்களுக்கு தகுதியானவர்:\n• பிஎம்-கிசான்\n• பயிர் காப்பீடு\n• நீர்ப்பாசன மானியம்' },
      { type: 'user', text: 'பிஎம்-கிசானுக்கு விண்ணப்பிக்க வேண்டும்' },
      { type: 'bot', text: '📝 முடிந்தது! விண்ணப்பம் சமர்ப்பிக்கப்பட்டது. டிராக் ID: #GS-2026-4821' }
    ],
    gu: [
      { type: 'bot', text: 'નમસ્તે! 🙏 હું ગ્રામ સહાયક છું. આજે હું તમને કેવી રીતે મદદ કરી શકું?' },
      { type: 'user', text: 'મારે ખેડૂત યોજનાઓ વિશે જાણવું છે' },
      { type: 'bot', text: 'ચોક્કસ! પાત્રતા તપાસી રહ્યો છું...' },
      { type: 'bot', text: '✅ તમે 3 યોજનાઓ માટે પાત્ર છો:\n• પીએમ-કિસાન\n• પાક વીમો\n• સિંચાઈ સબસિડી' },
      { type: 'user', text: 'પીએમ-કિસાન માટે અરજી કરવી છે' },
      { type: 'bot', text: '📝 થઈ ગયું! અરજી જમા થઈ ગઈ. ટ્રેક ID: #GS-2026-4821' }
    ],
    kn: [
      { type: 'bot', text: 'ನಮಸ್ಕಾರ! 🙏 ನಾನು ಗ್ರಾಮ ಸಹಾಯಕ. ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?' },
      { type: 'user', text: 'ರೈತ ಯೋಜನೆಗಳ ಬಗ್ಗೆ ತಿಳಿಯಬೇಕು' },
      { type: 'bot', text: 'ಖಂಡಿತ! ಅರ್ಹತೆ ಪರಿಶೀಲಿಸುತ್ತಿದ್ದೇನೆ...' },
      { type: 'bot', text: '✅ ನೀವು 3 ಯೋಜನೆಗಳಿಗೆ ಅರ್ಹರು:\n• ಪಿಎಂ-ಕಿಸಾನ್\n• ಬೆಳೆ ವಿಮೆ\n• ನೀರಾವರಿ ಸಬ್ಸಿಡಿ' },
      { type: 'user', text: 'ಪಿಎಂ-ಕಿಸಾನ್‌ಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಬೇಕು' },
      { type: 'bot', text: '📝 ಆಯಿತು! ಅರ್ಜಿ ಸಲ್ಲಿಸಲಾಗಿದೆ. ಟ್ರ್ಯಾಕ್ ID: #GS-2026-4821' }
    ],
    ml: [
      { type: 'bot', text: 'നമസ്കാരം! 🙏 ഞാൻ ഗ്രാം സഹായക്. ഇന്ന് എങ്ങനെ സഹായിക്കാം?' },
      { type: 'user', text: 'കർഷക പദ്ധതികളെ കുറിച്ച് അറിയണം' },
      { type: 'bot', text: 'തീർച്ചയായും! യോഗ്യത പരിശോധിക്കുന്നു...' },
      { type: 'bot', text: '✅ നിങ്ങൾ 3 പദ്ധതികൾക്ക് യോഗ്യരാണ്:\n• പിഎം-കിസാൻ\n• വിള ഇൻഷുറൻസ്\n• ജലസേചന സബ്‌സിഡി' },
      { type: 'user', text: 'പിഎം-കിസാനിന് അപേക്ഷിക്കണം' },
      { type: 'bot', text: '📝 കഴിഞ്ഞു! അപേക്ഷ സമർപ്പിച്ചു. ട്രാക്ക് ID: #GS-2026-4821' }
    ],
    pa: [
      { type: 'bot', text: 'ਸਤ ਸ੍ਰੀ ਅਕਾਲ! 🙏 ਮੈਂ ਗ੍ਰਾਮ ਸਹਾਇਕ ਹਾਂ। ਅੱਜ ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?' },
      { type: 'user', text: 'ਮੈਨੂੰ ਕਿਸਾਨ ਯੋਜਨਾਵਾਂ ਬਾਰੇ ਜਾਣਕਾਰੀ ਚਾਹੀਦੀ ਹੈ' },
      { type: 'bot', text: 'ਬਿਲਕੁਲ! ਯੋਗਤਾ ਜਾਂਚ ਰਿਹਾ ਹਾਂ...' },
      { type: 'bot', text: '✅ ਤੁਸੀਂ 3 ਯੋਜਨਾਵਾਂ ਲਈ ਯੋਗ ਹੋ:\n• ਪੀਐਮ-ਕਿਸਾਨ\n• ਫ਼ਸਲ ਬੀਮਾ\n• ਸਿੰਚਾਈ ਸਬਸਿਡੀ' },
      { type: 'user', text: 'ਪੀਐਮ-ਕਿਸਾਨ ਲਈ ਅਰਜ਼ੀ ਦੇਣੀ ਹੈ' },
      { type: 'bot', text: '📝 ਹੋ ਗਿਆ! ਅਰਜ਼ੀ ਜਮ੍ਹਾ ਹੋ ਗਈ। ਟ੍ਰੈਕ ID: #GS-2026-4821' }
    ],
    or: [
      { type: 'bot', text: 'ନମସ୍କାର! 🙏 ମୁଁ ଗ୍ରାମ ସହାୟକ। ଆଜି କିପରି ସାହାଯ୍ୟ କରିବି?' },
      { type: 'user', text: 'ମୋତେ ଚାଷୀ ଯୋଜନା ବିଷୟରେ ଜାଣିବାକୁ ଦିଅ' },
      { type: 'bot', text: 'ନିଶ୍ଚୟ! ଯୋଗ୍ୟତା ଯାଞ୍ଚ କରୁଛି...' },
      { type: 'bot', text: '✅ ଆପଣ ୩ଟି ଯୋଜନା ପାଇଁ ଯୋଗ୍ୟ:\n• ପିଏମ-କିସାନ\n• ଫସଲ ବୀମା\n• ଜଳସେଚନ ସବସିଡି' },
      { type: 'user', text: 'ପିଏମ-କିସାନ ପାଇଁ ଆବେଦନ କରିବାକୁ ଚାହୁଁଛି' },
      { type: 'bot', text: '📝 ହୋଇଗଲା! ଆବେଦନ ଦାଖଲ ହୋଇଛି। ଟ୍ରାକ ID: #GS-2026-4821' }
    ],
    as: [
      { type: 'bot', text: 'নমস্কাৰ! 🙏 মই গ্ৰাম সহায়ক। আজি কেনেদৰে সহায় কৰিব পাৰোঁ?' },
      { type: 'user', text: 'মোক কৃষক আঁচনিৰ বিষয়ে জানিব লাগে' },
      { type: 'bot', text: 'নিশ্চয়! যোগ্যতা পৰীক্ষা কৰি আছোঁ...' },
      { type: 'bot', text: '✅ আপুনি ৩টা আঁচনিৰ যোগ্য:\n• পিএম-কিষাণ\n• শস্য বীমা\n• জলসিঞ্চন ৰাজসাহায্য' },
      { type: 'user', text: 'পিএম-কিষাণৰ বাবে আবেদন কৰিব লাগে' },
      { type: 'bot', text: '📝 হৈ গ\'ল! আবেদন দাখিল হৈছে। ট্ৰেক ID: #GS-2026-4821' }
    ],
    ur: [
      { type: 'bot', text: 'السلام علیکم! 🙏 میں گرام سہایک ہوں۔ آج کیسے مدد کروں؟' },
      { type: 'user', text: 'مجھے کسان اسکیم کے بارے میں جاننا ہے' },
      { type: 'bot', text: 'بالکل! اہلیت جانچ رہا ہوں...' },
      { type: 'bot', text: '✅ آپ 3 اسکیموں کے اہل ہیں:\n• پی ایم-کسان\n• فصل انشورنس\n• آبپاشی سبسڈی' },
      { type: 'user', text: 'پی ایم-کسان کے لیے درخواست دینی ہے' },
      { type: 'bot', text: '📝 ہو گیا! درخواست جمع ہو گئی۔ ٹریک ID: #GS-2026-4821' }
    ],
    mai: [
      { type: 'bot', text: 'प्रणाम! 🙏 हम ग्राम सहायक छी। आइ कोना मदद करू?' },
      { type: 'user', text: 'हमरा किसान योजनाक बारेमे जानकारी चाही' },
      { type: 'bot', text: 'जरूर! पात्रता जाँच रहल छी...' },
      { type: 'bot', text: '✅ अहाँ 3 योजनाक पात्र छी:\n• पीएम-किसान\n• फसल बीमा\n• सिंचाई सब्सिडी' },
      { type: 'user', text: 'पीएम-किसान लेल आवेदन करक चाही' },
      { type: 'bot', text: '📝 भऽ गेल! आवेदन जमा भऽ गेल। ट्रैक ID: #GS-2026-4821' }
    ],
    sa: [
      { type: 'bot', text: 'नमस्कारः! 🙏 अहं ग्रामसहायकः। अद्य किं साहाय्यं करोमि?' },
      { type: 'user', text: 'कृषकयोजनानां विषये ज्ञातुम् इच्छामि' },
      { type: 'bot', text: 'अवश्यम्! पात्रतां परीक्षयामि...' },
      { type: 'bot', text: '✅ भवान् ३ योजनानां पात्रः:\n• पीएम-किसान\n• सस्यबीमा\n• सिञ्चनानुदानम्' },
      { type: 'user', text: 'पीएम-किसान-योजनायै आवेदनं कर्तुम् इच्छामि' },
      { type: 'bot', text: '📝 सम्पन्नम्! आवेदनं समर्पितम्। ट्रैक ID: #GS-2026-4821' }
    ],
    ks: [
      { type: 'bot', text: 'आदाब! 🙏 बि छुस ग्राम सहायक। आज कथि मदद करि हेकव?' },
      { type: 'user', text: 'मि छुस किसान योजनन हंद जानकारी मंगान' },
      { type: 'bot', text: 'बिलकुल! पात्रता जाँच करान छुस...' },
      { type: 'bot', text: '✅ तोहि छुक 3 योजनन हंद पात्र:\n• पीएम-किसान\n• फसल बीमा\n• सिंचाई सब्सिडी' },
      { type: 'user', text: 'पीएम-किसान बापथ आवेदन करनव छुस' },
      { type: 'bot', text: '📝 वोतुव! आवेदन जमा गव। ट्रैक ID: #GS-2026-4821' }
    ],
    ne: [
      { type: 'bot', text: 'नमस्ते! 🙏 म ग्राम सहायक हुँ। कसरी मद्दत गर्न सक्छु?' },
      { type: 'user', text: 'मलाई किसान योजनाको बारेमा जानकारी चाहिन्छ' },
      { type: 'bot', text: 'अवश्य! योग्यता जाँच गर्दैछु...' },
      { type: 'bot', text: '✅ तपाईं 3 योजनाको लागि योग्य:\n• पीएम-किसान\n• बाली बीमा\n• सिंचाइ अनुदान' },
      { type: 'user', text: 'पीएम-किसानको लागि आवेदन गर्नुपर्छ' },
      { type: 'bot', text: '📝 भयो! आवेदन पेश भयो। ट्र्याक ID: #GS-2026-4821' }
    ],
    sd: [
      { type: 'bot', text: 'سلام! 🙏 مان گرام سهايڪ آهيان. اڄ ڪيئن مدد ڪريان؟' },
      { type: 'user', text: 'مون کي هارين جي اسڪيم بابت ڄاڻڻ آهي' },
      { type: 'bot', text: 'ضرور! اهليت جانچي رهيو آهيان...' },
      { type: 'bot', text: '✅ توهان 3 اسڪيمن لاءِ اهل آهيو:\n• پي ايم-ڪسان\n• فصل بيمو\n• آبپاشي سبسڊي' },
      { type: 'user', text: 'پي ايم-ڪسان لاءِ درخواست ڏيڻي آهي' },
      { type: 'bot', text: '📝 ٿي ويو! درخواست جمع ٿي وئي. ٽريڪ ID: #GS-2026-4821' }
    ],
    doi: [
      { type: 'bot', text: 'नमस्कार! 🙏 मैं ग्राम सहायक हां। अज्ज कीं मदद करें?' },
      { type: 'user', text: 'मिगी किसान योजना दे बारे च जानकारी चाहिदी ऐ' },
      { type: 'bot', text: 'जरूर! पात्रता जाँच करा दा हां...' },
      { type: 'bot', text: '✅ तुस 3 योजनाएं दे पात्र ओ:\n• पीएम-किसान\n• फसल बीमा\n• सिंचाई सब्सिडी' },
      { type: 'user', text: 'पीएम-किसान आस्तै आवेदन करना ऐ' },
      { type: 'bot', text: '📝 होई गेआ! आवेदन जमा होई गेआ। ट्रैक ID: #GS-2026-4821' }
    ],
    kok: [
      { type: 'bot', text: 'नमस्कार! 🙏 हांव ग्राम सहायक. आज कशी मजत करूं?' },
      { type: 'user', text: 'म्हाका शेतकार योजनां विशीं म्हायती जाय' },
      { type: 'bot', text: 'खात्रीन! पात्रताय तपासतां...' },
      { type: 'bot', text: '✅ तूं 3 योजनांक पात्र आसा:\n• पीएम-किसान\n• पीक विमो\n• शिंपणावळ अनुदान' },
      { type: 'user', text: 'पीएम-किसान खातीर अर्ज करूंक जाय' },
      { type: 'bot', text: '📝 जालें! अर्ज दाखल जालो. ट्रॅक ID: #GS-2026-4821' }
    ],
    mni: [
      { type: 'bot', text: 'খোইরু! 🙏 ঐহাক্না গ্রাম সহায়ক। ঙসি অদোমদা করিগে?' },
      { type: 'user', text: 'ঐখোয়না লৌমী স্কীমশিংগী মরমদা খঙবা পাম্মী' },
      { type: 'bot', text: 'য়ামদ্রবনি! য়োগ্যতা য়েংশিনবা...' },
      { type: 'bot', text: '✅ অদোম 3 স্কীমগী য়োগ্য ওই:\n• পি.এম-কিষাণ\n• লৌউ ইনস্যুরেন্স\n• তোয়ীন থমবল সবসিদি' },
      { type: 'user', text: 'পি.এম-কিষাণগীদমক এপ্লাই তৌবা পাম্মী' },
      { type: 'bot', text: '📝 লোয়রে! এপ্লিকেসন সবমিট তৌরে। ট্র্যাক ID: #GS-2026-4821' }
    ],
    brx: [
      { type: 'bot', text: 'फिसाजों! 🙏 आं ग्राम सहायक। दिनै माबोर मदद खालामनो हागौ?' },
      { type: 'user', text: 'आंखौ हालो सोदोबथारि बिथांनाय फोरमानि मोनसे नांगौ' },
      { type: 'bot', text: 'गोनांथार! जायखि सिनायनाय...' },
      { type: 'bot', text: '✅ नों 3 बिथांनायनि जायखि:\n• पीएम-किसान\n• बारनि बिमा\n• दैसा आयदान' },
      { type: 'user', text: 'पीएम-किसानआव एप्लाय खालामनो नांगौ' },
      { type: 'bot', text: '📝 जादों! आबेदन दाखिल जादों। ट्रेक ID: #GS-2026-4821' }
    ],
    sat: [
      { type: 'bot', text: 'ᱡᱚᱦᱟᱨ! 🙏 ᱤᱧ ᱜᱽᱨᱟᱢ ᱥᱟᱦᱟᱭᱟᱠ᱾ ᱛᱤᱱᱟᱹ ᱚᱠᱛᱚ ᱜᱚᱲᱚ ᱫᱟᱲᱮᱭᱟᱜ ᱡᱟ?' },
      { type: 'user', text: 'ᱤᱧᱟᱜ ᱠᱤᱥᱟᱱ ᱡᱚᱡᱚᱱᱟ ᱵᱟᱵᱚᱛ ᱥᱮᱞᱮᱫ ᱞᱟᱹᱜᱤᱫ ᱢᱮ' },
      { type: 'bot', text: 'ᱦᱚᱭ! ᱡᱚᱜᱭᱚᱛᱟ ᱧᱮᱞ ᱮᱫᱟ...' },
      { type: 'bot', text: '✅ ᱟᱢ ᱓ ᱡᱚᱡᱚᱱᱟ ᱞᱟᱹᱜᱤᱫ ᱡᱚᱜᱭᱚ:\n• PM-KISAN\n• ᱫᱟᱨᱟ ᱵᱤᱢᱟ\n• ᱫᱟᱹᱜ ᱥᱩᱵᱥᱤᱰᱤ' },
      { type: 'user', text: 'PM-KISAN ᱞᱟᱹᱜᱤᱫ ᱟᱹᱨᱡᱤ ᱮᱢ ᱢᱮ' },
      { type: 'bot', text: '📝 ᱦᱚᱭ ᱮᱱᱟ! ᱟᱹᱨᱡᱤ ᱡᱟᱢᱟ ᱦᱚᱭ ᱮᱱᱟ᱾ ᱴᱨᱮᱠ ID: #GS-2026-4821' }
    ]
  };

  // --- Chat Demo Animation ---
  var chatMessages = document.getElementById('chat-messages');
  var chatConversation = allChatConversations['hi'];
  var currentChatLang = 'hi';
  var chatIndex = 0;
  var chatTimeoutIds = [];

  function showNextMessage() {
    if (!chatMessages || chatIndex >= chatConversation.length) {
      // Restart after a pause
      var restartId = setTimeout(function () {
        if (chatMessages) {
          chatMessages.innerHTML = '';
          chatIndex = 0;
          showNextMessage();
        }
      }, 4000);
      chatTimeoutIds.push(restartId);
      return;
    }

    var msg = chatConversation[chatIndex];
    var bubble = document.createElement('div');
    bubble.className = 'chat-bubble ' + msg.type;
    bubble.textContent = msg.text;
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    chatIndex++;

    var delay = msg.type === 'user' ? 2000 : 2500;
    var nextId = setTimeout(showNextMessage, delay);
    chatTimeoutIds.push(nextId);
  }

  function switchChatLanguage(langCode) {
    // Clear pending chat timeouts
    chatTimeoutIds.forEach(function (id) { clearTimeout(id); });
    chatTimeoutIds = [];
    // Set conversation for the selected language
    chatConversation = allChatConversations[langCode] || allChatConversations['hi'];
    currentChatLang = langCode;
    chatIndex = 0;
    if (chatMessages) chatMessages.innerHTML = '';
    chatTimeoutIds.push(setTimeout(showNextMessage, 500));
    try { localStorage.setItem('gram-sahayak-lang', langCode); } catch (_) {}
  }

  // --- Language Selection (manual click + geo) ---
  function setActiveLanguage(langCode) {
    var found = false;
    langItems.forEach(function (item, idx) {
      item.classList.remove('active');
      if (item.getAttribute('data-lang') === langCode) {
        item.classList.add('active');
        currentLangIndex = idx;
        found = true;
      }
    });
    if (!found) langCode = 'hi';
    if (activeLangLabel) {
      var activeItem = document.querySelector('.lang-item[data-lang="' + langCode + '"]');
      if (activeItem) {
        activeLangLabel.textContent = activeItem.querySelector('.lang-english').textContent;
      }
    }
    switchChatLanguage(langCode);
  }

  // Make language items clickable for manual selection
  langItems.forEach(function (item) {
    item.setAttribute('role', 'button');
    item.setAttribute('tabindex', '0');
    item.addEventListener('click', function () {
      // Stop auto-rotate on manual selection
      if (langInterval !== null) {
        clearInterval(langInterval);
        langInterval = null;
      }
      var langCode = item.getAttribute('data-lang');
      setActiveLanguage(langCode);
      // Hide geo indicator since user made manual choice
      var geoIndicator = document.getElementById('lang-geo-indicator');
      if (geoIndicator) geoIndicator.hidden = true;
    });
    item.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        item.click();
      }
    });
  });

  // --- Geolocation-based Language Detection ---
  var stateLanguageMap = [
    [28.6, 77.2, 'hi'], [26.8, 80.9, 'hi'], [25.6, 85.1, 'hi'],
    [23.3, 85.3, 'hi'], [23.2, 77.4, 'hi'], [21.3, 81.6, 'hi'],
    [27.0, 74.2, 'hi'], [30.7, 76.8, 'hi'], [31.1, 77.2, 'hi'],
    [30.3, 78.0, 'hi'], [19.1, 72.9, 'mr'], [19.7, 75.7, 'mr'],
    [22.6, 88.4, 'bn'], [22.9, 87.9, 'bn'], [23.8, 91.3, 'bn'],
    [13.1, 80.3, 'ta'], [11.0, 76.9, 'ta'], [17.4, 78.5, 'te'],
    [15.9, 79.7, 'te'], [12.9, 77.6, 'kn'], [15.3, 75.7, 'kn'],
    [10.0, 76.3, 'ml'], [8.5, 76.9, 'ml'], [23.0, 72.6, 'gu'],
    [22.3, 70.8, 'gu'], [31.6, 74.9, 'pa'], [30.7, 76.7, 'pa'],
    [20.3, 85.8, 'or'], [26.1, 91.7, 'as'], [15.4, 74.0, 'kok'],
    [24.8, 93.9, 'mni'], [27.3, 88.6, 'ne'], [34.1, 74.8, 'ks'],
    [32.7, 74.9, 'doi'], [25.5, 87.0, 'sat'], [26.6, 93.0, 'brx'],
    [26.1, 86.0, 'mai'], [25.4, 68.4, 'sd'], [34.2, 77.6, 'ur']
  ];

  function detectLanguageByLocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(function (pos) {
      var lat = pos.coords.latitude;
      var lng = pos.coords.longitude;
      var closestLang = 'hi';
      var minDist = Infinity;
      stateLanguageMap.forEach(function (entry) {
        var d = Math.pow(lat - entry[0], 2) + Math.pow(lng - entry[1], 2);
        if (d < minDist) {
          minDist = d;
          closestLang = entry[2];
        }
      });
      // Only auto-set if user hasn't manually selected a language
      var savedLang = null;
      try { savedLang = localStorage.getItem('gram-sahayak-lang'); } catch (_) {}
      if (!savedLang) {
        setActiveLanguage(closestLang);
        var geoIndicator = document.getElementById('lang-geo-indicator');
        if (geoIndicator) geoIndicator.hidden = false;
      }
    }, function () {
      // Geolocation denied or unavailable — keep default
    }, { timeout: 5000 });
  }

  // Initialize chat with saved language or default, then try geolocation
  var initLang = null;
  try { initLang = localStorage.getItem('gram-sahayak-lang'); } catch (_) {}
  if (initLang && allChatConversations[initLang]) {
    setActiveLanguage(initLang);
  } else {
    // Start with Hindi by default, then try geo-detection in background
    chatTimeoutIds.push(setTimeout(showNextMessage, 1500));
    detectLanguageByLocation();
  }

  // --- Voice Demo Modal ---
  var voiceModal = document.getElementById('voice-modal');
  var modalClose = document.getElementById('modal-close');
  var micButton = document.getElementById('mic-button');
  var micStatus = document.getElementById('mic-status');
  var demoResponse = document.getElementById('demo-response');
  var modalTrigger = null;
  var micTimeouts = [];

  var triggerButtons = [
    document.getElementById('try-voice-btn'),
    document.getElementById('cta-voice-btn'),
    document.getElementById('start-btn')
  ];

  function openModal(trigger) {
    if (voiceModal) {
      modalTrigger = trigger || null;
      voiceModal.hidden = false;
      voiceModal.querySelector('.modal-close').focus();
      document.body.style.overflow = 'hidden';
    }
  }

  function closeModal() {
    if (voiceModal) {
      // Clear any pending mic demo timeouts to prevent race conditions
      micTimeouts.forEach(function (id) { clearTimeout(id); });
      micTimeouts = [];

      voiceModal.hidden = true;
      document.body.style.overflow = '';
      if (micButton) micButton.classList.remove('active');
      if (micStatus) micStatus.textContent = 'Tap to start speaking';
      if (demoResponse) {
        demoResponse.classList.remove('visible');
        demoResponse.textContent = '';
      }
      // Restore focus to the button that opened the modal
      if (modalTrigger && typeof modalTrigger.focus === 'function') {
        modalTrigger.focus();
        modalTrigger = null;
      }
    }
  }

  // Focus trap: keep Tab/Shift+Tab within the modal
  if (voiceModal) {
    voiceModal.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab') return;
      var focusable = voiceModal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (focusable.length === 0) return;
      var first = focusable[0];
      var last = focusable[focusable.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    });
  }

  triggerButtons.forEach(function (btn) {
    if (btn) btn.addEventListener('click', function () { openModal(btn); });
  });

  if (modalClose) modalClose.addEventListener('click', closeModal);

  // Close on overlay click
  if (voiceModal) {
    voiceModal.addEventListener('click', function (e) {
      if (e.target === voiceModal) closeModal();
    });
  }

  // Close on Escape
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && voiceModal && !voiceModal.hidden) {
      closeModal();
    }
  });

  // Mic button demo interaction
  var demoResponses = [
    '🎤 Detected language: Hindi (हिन्दी)\n\n"I want to know about farming schemes"\n\n✅ Searching 700+ schemes for eligibility...',
    '🎤 Detected language: Bengali (বাংলা)\n\n"আমার পেনশন সম্পর্কে জানতে চাই"\n\n✅ Found 2 pension schemes you may be eligible for.',
    '🎤 Detected language: Tamil (தமிழ்)\n\n"கல்வி உதவித்தொகை பற்றி தெரிந்து கொள்ள விரும்புகிறேன்"\n\n✅ Found 5 education scholarships matching your profile.',
    '🎤 Detected language: Telugu (తెలుగు)\n\n"ఇంటి నిర్మాణ పథకం గురించి"\n\n✅ You are eligible for PM Awas Yojana. Shall I help you apply?'
  ];
  var demoResponseIndex = 0;

  if (micButton) {
    micButton.addEventListener('click', function () {
      if (micButton.classList.contains('active')) return;

      micButton.classList.add('active');
      if (micStatus) micStatus.textContent = 'Listening...';
      if (demoResponse) {
        demoResponse.classList.remove('visible');
        demoResponse.textContent = '';
      }

      // Simulate listening (store timeout IDs so they can be cleared)
      micTimeouts.push(setTimeout(function () {
        if (micStatus) micStatus.textContent = 'Processing...';
      }, 2000));

      // Show response
      micTimeouts.push(setTimeout(function () {
        micButton.classList.remove('active');
        if (micStatus) micStatus.textContent = 'Tap to speak again';
        if (demoResponse) {
          demoResponse.textContent = demoResponses[demoResponseIndex];
          demoResponse.classList.add('visible');
          demoResponseIndex = (demoResponseIndex + 1) % demoResponses.length;
        }
      }, 3500));
    });
  }

  // --- Smooth scroll for anchor links ---
  document.querySelectorAll('a[href^="#"]:not([href="#"])').forEach(function (link) {
    link.addEventListener('click', function (e) {
      var target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // --- Animate on initial load ---
  window.addEventListener('load', function () {
    // Trigger counter animation if hero stats are already visible
    if (heroStats) {
      var rect = heroStats.getBoundingClientRect();
      if (rect.top < window.innerHeight) {
        heroStats.classList.add('visible');
        animateCounters();
      }
    }
  });

  // --- Back to Top Button ---
  var backToTop = document.getElementById('back-to-top');
  if (backToTop) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 600) {
        backToTop.hidden = false;
        backToTop.classList.add('visible');
      } else {
        backToTop.classList.remove('visible');
        // Keep hidden attribute in sync after transition
        setTimeout(function () {
          if (!backToTop.classList.contains('visible')) {
            backToTop.hidden = true;
          }
        }, 300);
      }
    }, { passive: true });

    backToTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

})();
