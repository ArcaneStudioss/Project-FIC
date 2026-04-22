/* =============================================
   ENERGIA SOLAR — FEIRA DE CIÊNCIAS
   JavaScript principal
   ============================================= */

document.addEventListener('DOMContentLoaded', function () {

  /* ── NAV SCROLL ── */
  const navbar = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 30);
    updateActiveNav();
  });

  /* ── HAMBURGER ── */
  const hamburger = document.getElementById('hamburger');
  const mobileNav = document.getElementById('mobileNav');
  hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('open');
    mobileNav.classList.toggle('open');
  });
  document.querySelectorAll('.mobile-nav a').forEach(a => {
    a.addEventListener('click', () => {
      hamburger.classList.remove('open');
      mobileNav.classList.remove('open');
    });
  });

  /* ── ACTIVE NAV LINK ── */
  function updateActiveNav() {
    const sections = document.querySelectorAll('section[id]');
    let current = '';
    sections.forEach(s => {
      if (window.scrollY >= s.offsetTop - 100) current = s.id;
    });
    document.querySelectorAll('.nav-links a').forEach(a => {
      a.classList.toggle('active', a.getAttribute('href') === '#' + current);
    });
  }

  /* ── FADE-IN OBSERVER ── */
  const fadeEls = document.querySelectorAll('.fade-in');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.12 });
  fadeEls.forEach(el => observer.observe(el));

  /* ── PROGRESS BARS ── */
  const barObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.querySelectorAll('.progress-bar').forEach(bar => {
          bar.style.width = bar.dataset.width;
        });
        e.target.querySelectorAll('.bar-fill').forEach(bar => {
          bar.style.width = bar.dataset.width;
        });
        barObserver.unobserve(e.target);
      }
    });
  }, { threshold: 0.3 });

  document.querySelectorAll('.progress-list, .chart-bars').forEach(el => {
    barObserver.observe(el);
  });

  /* ── ACCORDION ── */
  document.querySelectorAll('.accordion-header').forEach(header => {
    header.addEventListener('click', () => {
      const item = header.parentElement;
      const body = item.querySelector('.accordion-body');
      const isOpen = item.classList.contains('open');

      // fecha todos
      document.querySelectorAll('.accordion-item').forEach(i => {
        i.classList.remove('open');
        i.querySelector('.accordion-body').classList.remove('open');
      });

      // abre o clicado se estava fechado
      if (!isOpen) {
        item.classList.add('open');
        body.classList.add('open');
      }
    });
  });

  /* ── CALCULADORA SOLAR ── */
  const calcBtn = document.getElementById('calcBtn');
  if (calcBtn) {
    calcBtn.addEventListener('click', calcularEnergia);
  }

  function calcularEnergia() {
    const consumo = parseFloat(document.getElementById('consumo').value) || 0;
    const tarifa  = parseFloat(document.getElementById('tarifa').value)  || 0;
    const telhado = parseFloat(document.getElementById('telhado').value) || 0;
    const horas   = parseFloat(document.getElementById('horas').value)   || 5;

    if (consumo <= 0 || tarifa <= 0) {
      alert('Por favor, preencha o consumo mensal e a tarifa de energia.');
      return;
    }

    // Cálculos aproximados
    const potencia_kwp   = consumo / (horas * 30);           // kWp necessário
    const paineis        = Math.ceil(potencia_kwp / 0.4);    // ~400W por painel
    const area_necessaria = paineis * 1.8;                    // ~1,8 m² por painel
    const economia_mes   = consumo * tarifa * 0.9;           // ~90% de economia
    const custo_sistema  = potencia_kwp * 5000;              // ~R$5000/kWp
    const payback_anos   = custo_sistema / (economia_mes * 12);
    const economia_25    = economia_mes * 12 * 25;           // vida útil 25 anos

    // Exibe resultados
    document.getElementById('res-potencia').textContent   = potencia_kwp.toFixed(2) + ' kWp';
    document.getElementById('res-paineis').textContent    = paineis;
    document.getElementById('res-economia').textContent   = 'R$ ' + economia_mes.toFixed(2).replace('.', ',');
    document.getElementById('res-payback').textContent    = payback_anos.toFixed(1) + ' anos';
    document.getElementById('res-custo').textContent      = 'R$ ' + custo_sistema.toLocaleString('pt-BR');
    document.getElementById('res-economia25').textContent = 'R$ ' + economia_25.toLocaleString('pt-BR');

    const area_ok = area_necessaria <= telhado || telhado === 0;
    const nota = document.getElementById('res-nota');
    if (telhado > 0) {
      nota.textContent = area_ok
        ? `Ótimo! Seu telhado de ${telhado} m² comporta os ${paineis} painéis necessários (${area_necessaria.toFixed(1)} m²). O sistema é viável!`
        : `Atenção: você precisa de ${area_necessaria.toFixed(1)} m² mas seu telhado tem apenas ${telhado} m². Considere uma instalação parcial.`;
    } else {
      nota.textContent = `Você precisará de aproximadamente ${area_necessaria.toFixed(1)} m² de telhado para instalar os ${paineis} painéis solares.`;
    }

    const resultDiv = document.getElementById('calcResult');
    resultDiv.classList.add('show');
    resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  /* ── CONTAGEM ANIMADA (hero stats) ── */
  const heroSection = document.querySelector('.hero');
  let counted = false;
  const countObserver = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && !counted) {
      counted = true;
      animateCounters();
    }
  }, { threshold: 0.5 });
  if (heroSection) countObserver.observe(heroSection);

  function animateCounters() {
    document.querySelectorAll('[data-count]').forEach(el => {
      const target = parseFloat(el.dataset.count);
      const suffix = el.dataset.suffix || '';
      const duration = 1800;
      const start = performance.now();
      const isFloat = el.dataset.float === 'true';

      function update(time) {
        const elapsed = time - start;
        const progress = Math.min(elapsed / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3);
        const value = target * ease;
        el.textContent = isFloat
          ? value.toFixed(1) + suffix
          : Math.round(value) + suffix;
        if (progress < 1) requestAnimationFrame(update);
      }
      requestAnimationFrame(update);
    });
  }

  /* ── SMOOTH SCROLL para links de ancoragem ── */
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        const offset = 70;
        const top = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });

});
