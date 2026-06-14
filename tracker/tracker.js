(function () {
  'use strict';

  var INGEST_URL  = (window.DATAMYNA_HOST || '') + '/ingest';
  var FLUSH_MS    = 5000;
  var queue       = [];
  var sessionId   = _sid();
  var userId      = null;
  var flushTimer  = null;

  // ── Helpers ──────────────────────────────────────────────────────────────────

  function _sid() {
    var k = '__fx_sid';
    var s = sessionStorage.getItem(k);
    if (!s) { s = 'sx_' + Math.random().toString(36).slice(2, 12); sessionStorage.setItem(k, s); }
    return s;
  }

  function _now() { return new Date().toISOString(); }

  function _push(eventType, eventName, pagePath, properties) {
    queue.push({
      timestamp:  _now(),
      session_id: sessionId,
      user_id:    userId,
      event_type: eventType,
      event_name: eventName,
      page_path:  pagePath || window.location.pathname,
      properties: properties || {},
    });
  }

  // ── Flush ─────────────────────────────────────────────────────────────────────

  function flush(useBeacon) {
    if (!queue.length) return;
    var batch = queue.splice(0);              // drain queue atomically

    if (useBeacon && navigator.sendBeacon) {
      // sendBeacon survives page close; fetch does not
      var blob = new Blob([JSON.stringify(batch)], { type: 'application/json' });
      var sent = navigator.sendBeacon(INGEST_URL, blob);
      if (!sent) {
        // sendBeacon can fail if the queue is too large — fall through to fetch
        Array.prototype.unshift.apply(queue, batch);
      }
      return;
    }

    fetch(INGEST_URL, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(batch),
      keepalive: true,
    }).catch(function () {
      // Retry: put events back at the front of the queue
      Array.prototype.unshift.apply(queue, batch);
    });
  }

  function startTimer() {
    if (flushTimer) return;
    flushTimer = setInterval(function () { flush(false); }, FLUSH_MS);
  }

  // ── Layer 1 — Autocapture (global click listener) ─────────────────────────────

  document.addEventListener('click', function (e) {
    var el = e.target;
    if (!el) return;

    // Layer 2 — Named event via data-track takes priority
    var named = el.closest ? el.closest('[data-track]') : null;
    if (named) {
      _push('custom', named.getAttribute('data-track'), null, {
        tag:   named.tagName.toLowerCase(),
        text:  named.innerText ? named.innerText.slice(0, 100) : '',
      });
      return;
    }

    // Layer 1 — Generic autocapture
    _push('click', 'click', null, {
      tag:     el.tagName ? el.tagName.toLowerCase() : '',
      id:      el.id      || '',
      classes: el.className && typeof el.className === 'string' ? el.className.slice(0, 100) : '',
      text:    el.innerText ? el.innerText.slice(0, 100) : '',
    });
  }, true);

  // ── Page view on load ─────────────────────────────────────────────────────────

  _push('page_view', 'page_view', window.location.pathname, {
    referrer: document.referrer || '',
    title:    document.title   || '',
  });

  // ── Tab close — flush via sendBeacon ─────────────────────────────────────────

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') flush(true);
  });
  window.addEventListener('beforeunload', function () { flush(true); });

  // ── Public API ────────────────────────────────────────────────────────────────

  window.datamyna = {
    /**
     * Fire a named custom event programmatically.
     * datamyna.track('signup_click', { plan: 'pro' })
     */
    track: function (eventName, properties) {
      _push('custom', eventName, null, properties || {});
    },

    /**
     * Identify the logged-in user. Call after login.
     * datamyna.identify('user_123')
     */
    identify: function (id) {
      userId = String(id);
    },
  };

  startTimer();
})();
