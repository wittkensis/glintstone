/**
 * home.js — Glintstone www landing page
 * < 4kb. No framework dependencies.
 *
 * Features:
 *   1. Fade-up on scroll — IntersectionObserver
 *   2. Stat counter animation — IntersectionObserver + requestAnimationFrame
 *
 * prefers-reduced-motion is respected: counters snap to final value instantly.
 */

(function () {
  'use strict';

  // ----------------------------------------------------------------
  // 1. Fade-up on scroll
  // ----------------------------------------------------------------
  const fadeTargets = document.querySelectorAll('.fade-up');

  if (fadeTargets.length > 0) {
    const fadeObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            fadeObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    fadeTargets.forEach(function (el) {
      fadeObserver.observe(el);
    });
  }

  // ----------------------------------------------------------------
  // 2. Stat counter animation
  // ----------------------------------------------------------------
  var reducedMotion =
    window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /**
   * Animate a single stat counter from 0 → target over durationMs.
   * If reducedMotion, snap instantly.
   * @param {HTMLElement} el   — the element whose textContent to update
   * @param {number}      target — final integer value
   * @param {number}      durationMs
   */
  function animateCounter(el, target, durationMs) {
    if (reducedMotion) {
      el.textContent = target.toLocaleString();
      return;
    }

    var startTime = null;

    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      var elapsed = timestamp - startTime;
      var progress = Math.min(elapsed / durationMs, 1);
      // ease-out cubic
      var eased = 1 - Math.pow(1 - progress, 3);
      var current = Math.round(eased * target);
      el.textContent = current.toLocaleString();

      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        el.textContent = target.toLocaleString();
      }
    }

    requestAnimationFrame(step);
  }

  var statElements = document.querySelectorAll('[data-stat-target]');

  if (statElements.length > 0) {
    var statObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var el = entry.target;
            var target = parseInt(el.getAttribute('data-stat-target'), 10);
            animateCounter(el, target, 1200);
            statObserver.unobserve(el);
          }
        });
      },
      { threshold: 0.4 }
    );

    statElements.forEach(function (el) {
      statObserver.observe(el);
    });
  }

})();
