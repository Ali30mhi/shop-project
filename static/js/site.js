(function () {
  "use strict";

  const root = document.documentElement;

  /* ---------- Dark mode ---------- */
  function initTheme() {
    const button = document.querySelector("[data-theme-toggle]");
    if (!button) return;
    const darkQuery = window.matchMedia("(prefers-color-scheme: dark)");

    function current() {
      return root.dataset.theme || (darkQuery.matches ? "dark" : "light");
    }
    function sync() {
      const dark = current() === "dark";
      button.dataset.state = dark ? "dark" : "light";
      button.setAttribute("aria-label", dark ? "Helles Design aktivieren" : "Dunkles Design aktivieren");
    }

    button.addEventListener("click", function () {
      const next = current() === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      try { localStorage.setItem("theme", next); } catch (e) {}
      sync();
    });
    if (darkQuery.addEventListener) darkQuery.addEventListener("change", sync);
    sync();
  }

  /* ---------- Mobile menu ---------- */
  function initMenu() {
    const button = document.querySelector("[data-menu-toggle]");
    const nav = document.getElementById("main-nav");
    if (!button || !nav) return;

    function setOpen(open) {
      nav.classList.toggle("is-open", open);
      button.setAttribute("aria-expanded", String(open));
    }
    button.addEventListener("click", function () {
      setOpen(!nav.classList.contains("is-open"));
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) setOpen(false);
    });
  }

  /* ---------- Cart drawer ---------- */
  function initDrawer() {
    const drawer = document.getElementById("cart-drawer");
    const overlay = document.querySelector("[data-drawer-overlay]");
    if (!drawer || !overlay) return;
    let lastFocus = null;

    function open() {
      lastFocus = document.activeElement;
      drawer.hidden = false;
      overlay.hidden = false;
      void drawer.offsetWidth;
      drawer.classList.add("is-open");
      overlay.classList.add("is-open");
      document.body.classList.add("no-scroll");
      const closeBtn = drawer.querySelector("[data-drawer-close]");
      if (closeBtn) closeBtn.focus();
    }
    function close() {
      if (drawer.hidden) return;
      drawer.classList.remove("is-open");
      overlay.classList.remove("is-open");
      document.body.classList.remove("no-scroll");
      setTimeout(function () {
        drawer.hidden = true;
        overlay.hidden = true;
      }, 250);
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    document.querySelectorAll("[data-drawer-open]").forEach(function (el) {
      el.addEventListener("click", function (e) {
        e.preventDefault();
        open();
      });
    });
    document.querySelectorAll("[data-drawer-close]").forEach(function (el) {
      el.addEventListener("click", close);
    });
    overlay.addEventListener("click", close);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") close();
    });
    drawer.addEventListener("keydown", function (e) {
      if (e.key !== "Tab") return;
      const focusable = drawer.querySelectorAll("a[href], button:not([disabled]), input:not([disabled])");
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    });

    if (document.body.dataset.openCart === "true") open();
  }

  /* ---------- Product gallery ---------- */
  function initGallery() {
    document.querySelectorAll("[data-gallery]").forEach(function (gallery) {
      const track = gallery.querySelector("[data-gallery-track]");
      const thumbs = gallery.querySelectorAll("[data-gallery-thumb]");
      if (!track || !thumbs.length) return;

      thumbs.forEach(function (thumb) {
        thumb.addEventListener("click", function () {
          const index = Number(thumb.dataset.galleryThumb);
          track.scrollTo({ left: index * track.clientWidth, behavior: "smooth" });
        });
      });

      let ticking = false;
      track.addEventListener("scroll", function () {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function () {
          const index = Math.round(track.scrollLeft / track.clientWidth);
          thumbs.forEach(function (t, n) { t.classList.toggle("is-active", n === index); });
          ticking = false;
        });
      }, { passive: true });
    });
  }

  /* ---------- Sticky buy bar (mobile) ---------- */
  function initBuybar() {
    const bar = document.querySelector("[data-buybar]");
    const mainButton = document.querySelector("[data-buy-button]");
    if (!bar || !mainButton || !("IntersectionObserver" in window)) return;

    const mobile = window.matchMedia("(max-width: 760px)");
    let mainVisible = true;

    function update() {
      const show = mobile.matches && !mainVisible;
      bar.hidden = !show;
      document.body.classList.toggle("has-buybar", show);
    }
    new IntersectionObserver(function (entries) {
      mainVisible = entries[0].isIntersecting;
      update();
    }).observe(mainButton);
    if (mobile.addEventListener) mobile.addEventListener("change", update);
  }

  /* ---------- Variant picker ---------- */
  function initVariantPicker() {
    const picker = document.querySelector("[data-variant-picker]");
    const dataEl = document.getElementById("variant-data");
    if (!picker || !dataEl) return;

    const variants = JSON.parse(dataEl.textContent);
    if (!variants.length) return;

    const list = document.querySelector("[data-variant-list]");
    const form = picker.closest("form");
    const submit = form.querySelector("[data-buy-button]");
    const priceEl = picker.querySelector("[data-price]");
    const compareEl = picker.querySelector("[data-compare]");
    const stockNote = picker.querySelector("[data-stock-note]");
    const colorLabel = picker.querySelector("[data-selected-color]");
    const buybarPrice = document.querySelector("[data-buybar-price]");
    const buybarButton = document.querySelector("[data-buybar-button]");
    const money = new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" });
    const hasColor = !!picker.querySelector("[data-color]");
    const hasSize = !!picker.querySelector("[data-size]");

    const initial = variants.find(function (v) { return v.inStock; }) || variants[0];
    let color = hasColor ? initial.color : "";
    let size = hasSize ? initial.size : "";

    picker.hidden = false;
    if (list) list.hidden = true;

    function match(c, s) {
      return variants.find(function (v) {
        return (!hasColor || v.color === c) && (!hasSize || v.size === s);
      });
    }
    function setStock(text, state) {
      stockNote.textContent = text;
      stockNote.className = "stock-note " + state;
    }
    function setDisabled(disabled) {
      submit.disabled = disabled;
      if (buybarButton) buybarButton.disabled = disabled;
    }

    function render() {
      picker.querySelectorAll("[data-color]").forEach(function (btn) {
        btn.setAttribute("aria-pressed", String(btn.dataset.color === color));
        const available = variants.some(function (v) { return v.color === btn.dataset.color && v.inStock; });
        btn.classList.toggle("is-unavailable", !available);
      });
      picker.querySelectorAll("[data-size]").forEach(function (btn) {
        btn.setAttribute("aria-pressed", String(btn.dataset.size === size));
        const v = match(color, btn.dataset.size);
        btn.classList.toggle("is-unavailable", !v || !v.inStock);
      });
      if (colorLabel) colorLabel.textContent = color;

      const variant = match(color, size);
      if (list) {
        list.querySelectorAll('input[name="variant"]').forEach(function (input) {
          input.checked = !!variant && String(variant.id) === input.value;
        });
      }

      if (variant) {
        const price = money.format(parseFloat(variant.price));
        priceEl.textContent = price;
        if (buybarPrice) buybarPrice.textContent = price;
        compareEl.textContent = variant.compare ? money.format(parseFloat(variant.compare)) : "";
        if (!variant.inStock) setStock("Derzeit ausverkauft", "is-out");
        else if (variant.lowStock) setStock("Nur noch " + variant.lowStock + " Stück verfügbar", "is-low");
        else setStock("Auf Lager", "is-ok");
        setDisabled(!variant.inStock);
      } else {
        priceEl.textContent = "";
        compareEl.textContent = "";
        setStock("Diese Kombination ist nicht verfügbar", "is-out");
        setDisabled(true);
      }
    }

    picker.addEventListener("click", function (e) {
      const btn = e.target.closest("[data-color], [data-size]");
      if (!btn) return;
      if (btn.dataset.color !== undefined) {
        color = btn.dataset.color;
        const current = match(color, size);
        if (hasSize && (!current || !current.inStock)) {
          const alt = variants.find(function (v) { return v.color === color && v.inStock; })
            || variants.find(function (v) { return v.color === color; });
          if (alt) size = alt.size;
        }
      }
      if (btn.dataset.size !== undefined) size = btn.dataset.size;
      render();
    });

    render();
  }

  initTheme();
  initMenu();
  initDrawer();
  initGallery();
  initBuybar();
  initVariantPicker();
})();
