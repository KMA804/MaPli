/**
 * Template Name: MediTrust
 * Template URL: https://bootstrapmade.com/meditrust-bootstrap-hospital-website-template/
 * Updated: Jul 04 2025 with Bootstrap v5.3.7
 * Author: BootstrapMade.com
 * License: https://bootstrapmade.com/license/
 */



// Mobile nav toggle
const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
const navmenu = document.querySelector('#navmenu');

if (mobileNavToggle) {
  mobileNavToggle.addEventListener('click', function (e) {
    navmenu.classList.toggle('navmenu-mobile');
    this.classList.toggle('bi-list');
    this.classList.toggle('bi-x');
  });
}


(function () {
  "use strict";

  /**
   * Apply .scrolled class to the body as the page is scrolled down
   */
  function toggleScrolled() {
    const selectBody = document.querySelector('body');
    const selectHeader = document.querySelector('#header');
    if (!selectHeader.classList.contains('scroll-up-sticky') && !selectHeader.classList.contains('sticky-top') && !selectHeader.classList.contains('fixed-top')) return;
    window.scrollY > 100 ? selectBody.classList.add('scrolled') : selectBody.classList.remove('scrolled');
  }

  /**
   * Mobile nav toggle
   */
  function mobileNavToggle() {
    const body = document.querySelector('body');
    const mobileNavToggleBtn = document.querySelector('.mobile-nav-toggle');
    const navmenu = document.querySelector('#navmenu');

    if (mobileNavToggleBtn) {
      mobileNavToggleBtn.addEventListener('click', function (e) {
        e.preventDefault();
        body.classList.toggle('mobile-nav-active');
        navmenu.classList.toggle('navmenu-mobile');
        this.classList.toggle('bi-list');
        this.classList.toggle('bi-x');
      });
    }
  }

  /**
   * Hide mobile nav on same-page/hash links
   */
  function hideMobileNavOnClick() {
    document.querySelectorAll('#navmenu a').forEach(navmenu => {
      navmenu.addEventListener('click', () => {
        if (document.querySelector('.mobile-nav-active')) {
          const body = document.querySelector('body');
          const mobileNavToggleBtn = document.querySelector('.mobile-nav-toggle');
          const navmenu = document.querySelector('#navmenu');

          body.classList.remove('mobile-nav-active');
          navmenu.classList.remove('navmenu-mobile');
          mobileNavToggleBtn.classList.add('bi-list');
          mobileNavToggleBtn.classList.remove('bi-x');
        }
      });
    });
  }

  /**
   * Toggle mobile nav dropdowns
   */
  function toggleMobileDropdowns() {
    document.querySelectorAll('.navmenu .toggle-dropdown').forEach(navmenu => {
      navmenu.addEventListener('click', function (e) {
        e.preventDefault();
        this.parentNode.classList.toggle('active');
        this.parentNode.nextElementSibling.classList.toggle('dropdown-active');
        e.stopImmediatePropagation();
      });
    });
  }

  /**
   * Mobile dropdown handling for direct dropdown links
   */
  function handleMobileDropdowns() {
    document.querySelectorAll('.navmenu .dropdown > a').forEach(function (element) {
      element.addEventListener('click', function (e) {
        if (document.querySelector('.mobile-nav-toggle').style.display !== 'none') {
          e.preventDefault();
          this.parentNode.classList.toggle('dropdown-active');
        }
      });
    });
  }

  /**
   * Close mobile menu when clicking outside
   */
  function closeMobileMenuOnOutsideClick() {
    document.addEventListener('click', function (e) {
      const navmenu = document.querySelector('#navmenu');
      const mobileNavToggleBtn = document.querySelector('.mobile-nav-toggle');

      if (navmenu.classList.contains('navmenu-mobile') &&
        !e.target.closest('#navmenu') &&
        !e.target.closest('.mobile-nav-toggle')) {
        const body = document.querySelector('body');
        body.classList.remove('mobile-nav-active');
        navmenu.classList.remove('navmenu-mobile');
        mobileNavToggleBtn.classList.add('bi-list');
        mobileNavToggleBtn.classList.remove('bi-x');
      }
    });
  }

  /**
   * Header scroll effect
   */
  function headerScrollEffect() {
    const header = document.querySelector('#header');
    if (header) {
      window.addEventListener('scroll', function () {
        if (window.scrollY > 100) {
          header.classList.add('header-scrolled');
          header.style.background = 'rgba(255, 255, 255, 0.98)';
          header.style.boxShadow = '0px 2px 20px rgba(0, 0, 0, 0.1)';
        } else {
          header.classList.remove('header-scrolled');
          header.style.background = 'rgba(255, 255, 255, 0.95)';
          header.style.boxShadow = '0px 2px 20px rgba(0, 0, 0, 0.1)';
        }
      });
    }
  }

  /**
   * Preloader
   */
  function initPreloader() {
    const preloader = document.querySelector('#preloader');
    if (preloader) {
      window.addEventListener('load', () => {
        preloader.remove();
      });
    }
  }

  /**
   * Scroll top button
   */
  function initScrollTop() {
    let scrollTop = document.querySelector('.scroll-top');

    function toggleScrollTop() {
      if (scrollTop) {
        window.scrollY > 100 ? scrollTop.classList.add('active') : scrollTop.classList.remove('active');
      }
    }

    if (scrollTop) {
      scrollTop.addEventListener('click', (e) => {
        e.preventDefault();
        window.scrollTo({
          top: 0,
          behavior: 'smooth'
        });
      });

      window.addEventListener('load', toggleScrollTop);
      document.addEventListener('scroll', toggleScrollTop);
    }
  }

  /**
   * Animation on scroll function and init
   */
  function initAOS() {
    if (typeof AOS !== 'undefined') {
      AOS.init({
        duration: 600,
        easing: 'ease-in-out',
        once: true,
        mirror: false
      });
    }
  }

  /**
   * Initiate Pure Counter
   */
  function initPureCounter() {
    if (typeof PureCounter !== 'undefined') {
      new PureCounter();
    }
  }

  /**
   * Init swiper sliders
   */
  function initSwiper() {
    if (typeof Swiper !== 'undefined') {
      document.querySelectorAll(".init-swiper").forEach(function (swiperElement) {
        let config = JSON.parse(
          swiperElement.querySelector(".swiper-config").innerHTML.trim()
        );

        if (swiperElement.classList.contains("swiper-tab")) {
          initSwiperWithCustomPagination(swiperElement, config);
        } else {
          new Swiper(swiperElement, config);
        }
      });
    }
  }

  function initSwiperWithCustomPagination(swiperElement, config) {
    // Custom swiper initialization for tabs
    new Swiper(swiperElement, config);
  }

  /**
   * Init isotope layout and filters
   */
  function initIsotope() {
    if (typeof Isotope !== 'undefined' && typeof imagesLoaded !== 'undefined') {
      document.querySelectorAll('.isotope-layout').forEach(function (isotopeItem) {
        let layout = isotopeItem.getAttribute('data-layout') ?? 'masonry';
        let filter = isotopeItem.getAttribute('data-default-filter') ?? '*';
        let sort = isotopeItem.getAttribute('data-sort') ?? 'original-order';

        let initIsotope;
        imagesLoaded(isotopeItem.querySelector('.isotope-container'), function () {
          initIsotope = new Isotope(isotopeItem.querySelector('.isotope-container'), {
            itemSelector: '.isotope-item',
            layoutMode: layout,
            filter: filter,
            sortBy: sort
          });
        });

        isotopeItem.querySelectorAll('.isotope-filters li').forEach(function (filters) {
          filters.addEventListener('click', function () {
            isotopeItem.querySelector('.isotope-filters .filter-active').classList.remove('filter-active');
            this.classList.add('filter-active');
            initIsotope.arrange({
              filter: this.getAttribute('data-filter')
            });
            if (typeof initAOS === 'function') {
              initAOS();
            }
          }, false);
        });
      });
    }
  }

  /**
   * Initiate glightbox
   */
  function initGlightbox() {
    if (typeof GLightbox !== 'undefined') {
      const glightbox = GLightbox({
        selector: '.glightbox'
      });
    }
  }

  /**
   * Frequently Asked Questions Toggle
   */
  function initFAQToggle() {
    document.querySelectorAll('.faq-item h3, .faq-item .faq-toggle, .faq-item .faq-header').forEach((faqItem) => {
      faqItem.addEventListener('click', () => {
        faqItem.parentNode.classList.toggle('faq-active');
      });
    });
  }

  /**
   * Smooth scroll for anchor links
   */
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        const target = document.querySelector(this.getAttribute('href'));
        if (target && this.getAttribute('href') !== '#') {
          e.preventDefault();
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      });
    });
  }

  /**
   * Initialize all functions when DOM is loaded
   */
  document.addEventListener('DOMContentLoaded', function () {
    // Navigation
    mobileNavToggle();
    hideMobileNavOnClick();
    toggleMobileDropdowns();
    handleMobileDropdowns();
    closeMobileMenuOnOutsideClick();

    // Header effects
    headerScrollEffect();
    document.addEventListener('scroll', toggleScrolled);

    // UI Components
    initScrollTop();
    initSmoothScroll();
    initFAQToggle();
  });

  /**
   * Initialize functions when window is fully loaded
   */
  window.addEventListener('load', function () {
    initPreloader();
    initAOS();
    initPureCounter();
    initSwiper();
    initIsotope();
    initGlightbox();
    toggleScrolled();

    console.log('MediTrust template loaded successfully');
  });
  /* === JAVASCRIPT PASSWORD TOGGLE === */
  document.addEventListener('DOMContentLoaded', function() {
    const passwordToggle=document.getElementById('passwordToggle');
    const passwordField=document.querySelector('input[type="password"]');

    if (passwordToggle && passwordField) {
      passwordToggle.addEventListener('click', function () {
        const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordField.setAttribute('type', type);
        this.innerHTML = type === 'password' ? '<i class="bi bi-eye"></i>' : '<i class="bi bi-eye-slash"></i>';
      });
    }
  });
})();

