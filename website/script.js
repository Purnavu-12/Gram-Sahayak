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
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setTheme('dark');
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

  var langInterval = setInterval(rotateLang, 2000);

  // Pause rotation on hover
  var langWheel = document.getElementById('language-wheel');
  if (langWheel) {
    langWheel.addEventListener('mouseenter', function () {
      clearInterval(langInterval);
    });
    langWheel.addEventListener('mouseleave', function () {
      langInterval = setInterval(rotateLang, 2000);
    });
  }

  // --- Chat Demo Animation ---
  var chatMessages = document.getElementById('chat-messages');
  var chatConversation = [
    { type: 'bot', text: 'Namaste! 🙏 I am Gram Sahayak. How can I help you today?' },
    { type: 'user', text: 'Mujhe kisan yojana ke baare mein jaankari chahiye' },
    { type: 'bot', text: 'Of course! I can help you find farming schemes. Let me check your eligibility...' },
    { type: 'bot', text: '✅ You are eligible for 3 schemes:\n• PM-KISAN\n• Crop Insurance\n• Irrigation Subsidy' },
    { type: 'user', text: 'PM-KISAN ke liye apply karna hai' },
    { type: 'bot', text: 'Great! I will help you fill the form. What is your full name?' },
    { type: 'user', text: 'Ramesh Kumar' },
    { type: 'bot', text: '📝 Form filled! I have submitted your PM-KISAN application. Track ID: #GS-2026-4821' }
  ];

  var chatIndex = 0;

  function showNextMessage() {
    if (!chatMessages || chatIndex >= chatConversation.length) {
      // Restart after a pause
      setTimeout(function () {
        if (chatMessages) {
          chatMessages.innerHTML = '';
          chatIndex = 0;
          showNextMessage();
        }
      }, 4000);
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
    setTimeout(showNextMessage, delay);
  }

  // Start chat demo after a short delay
  setTimeout(showNextMessage, 1500);

  // --- Voice Demo Modal ---
  var voiceModal = document.getElementById('voice-modal');
  var modalClose = document.getElementById('modal-close');
  var micButton = document.getElementById('mic-button');
  var micStatus = document.getElementById('mic-status');
  var demoResponse = document.getElementById('demo-response');

  var triggerButtons = [
    document.getElementById('try-voice-btn'),
    document.getElementById('cta-voice-btn'),
    document.getElementById('start-btn')
  ];

  function openModal() {
    if (voiceModal) {
      voiceModal.hidden = false;
      voiceModal.querySelector('.modal-close').focus();
      document.body.style.overflow = 'hidden';
    }
  }

  function closeModal() {
    if (voiceModal) {
      voiceModal.hidden = true;
      document.body.style.overflow = '';
      if (micButton) micButton.classList.remove('active');
      if (micStatus) micStatus.textContent = 'Tap to start speaking';
      if (demoResponse) {
        demoResponse.classList.remove('visible');
        demoResponse.textContent = '';
      }
    }
  }

  triggerButtons.forEach(function (btn) {
    if (btn) btn.addEventListener('click', openModal);
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

      // Simulate listening
      setTimeout(function () {
        if (micStatus) micStatus.textContent = 'Processing...';
      }, 2000);

      // Show response
      setTimeout(function () {
        micButton.classList.remove('active');
        if (micStatus) micStatus.textContent = 'Tap to speak again';
        if (demoResponse) {
          demoResponse.textContent = demoResponses[demoResponseIndex];
          demoResponse.classList.add('visible');
          demoResponseIndex = (demoResponseIndex + 1) % demoResponses.length;
        }
      }, 3500);
    });
  }

  // --- Smooth scroll for anchor links ---
  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
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

})();
