(() => {
  const formatPlanPrice = (plan) => {
    if (plan.price_label) return plan.price_label;
    if (plan.price !== undefined && plan.currency) {
      return `${plan.price} ${plan.currency} / мес`;
    }
    return "тариф на сайте";
  };

  const formatPlanSpecs = (plan) => {
    const parts = [];
    if (plan.cpu) parts.push(`${plan.cpu} vCPU`);
    if (plan.ram_gb) parts.push(`${plan.ram_gb} GB RAM`);
    if (plan.storage_gb) parts.push(`${plan.storage_gb} GB`);
    return parts.join(" · ") || "конфигурация на сайте";
  };

  const escapeHtml = (value) =>
    String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");

  window.initProvidersMarket = (config) => {
    const providers = config.providers || [];
    const countries = config.countries || [];
    const promos = config.promos || [];
    const notice = config.notice || "";

    const countryScroll = document.querySelector("#market-countries");
    const searchInput = document.querySelector("#market-search");
    const grid = document.querySelector("#market-grid");
    const listView = document.querySelector("#market-list-view");
    const detailView = document.querySelector("#market-detail-view");
    const detailRoot = document.querySelector("#market-detail");
    const emptyState = document.querySelector("#market-empty");
    const promosRoot = document.querySelector("#market-promos");
    const backButton = document.querySelector("#market-back");

    if (!grid || !listView || !detailView || !detailRoot) return;

    let activeCountry = "";
    let activeDomain = "";

    const matchesSearch = (provider, query) => {
      if (!query) return true;
      const haystack = `${provider.name} ${provider.domain}`.toLowerCase();
      return haystack.includes(query);
    };

    const matchesCountry = (provider, countryCode) => {
      if (!countryCode) return true;
      return (provider.countries || []).includes(countryCode);
    };

    const filteredProviders = () => {
      const query = (searchInput?.value || "").trim().toLowerCase();
      return providers.filter(
        (provider) => matchesCountry(provider, activeCountry) && matchesSearch(provider, query),
      );
    };

    const renderPromos = () => {
      if (!promosRoot) return;
      if (!promos.length) {
        promosRoot.innerHTML =
          '<p class="market-promo-empty muted">Партнёрские предложения и промокоды появятся здесь.</p>';
        return;
      }
      promosRoot.innerHTML = promos
        .map((promo) => {
          const url = promo.referral_url || promo.website_url || "#";
          const sponsored = promo.sponsored ? '<span class="market-badge">Партнёр</span>' : "";
          const code = promo.promo_code
            ? `<span class="market-promo-code">${escapeHtml(promo.promo_code)}</span>`
            : "";
          return `
            <article class="market-promo-card">
              <div>
                ${sponsored}
                <strong>${escapeHtml(promo.title || promo.provider_domain || "Предложение")}</strong>
                <p>${escapeHtml(promo.text || "")}</p>
                ${code}
              </div>
              <a class="secondary" href="${escapeHtml(url)}" target="_blank" rel="noreferrer sponsored">Подробнее</a>
            </article>
          `;
        })
        .join("");
    };

    const renderBadges = (provider) => {
      const badges = [];
      if (provider.api_docs_url) badges.push('<span class="market-badge market-badge-api">API</span>');
      if (provider.integration_type === "billmanager") {
        badges.push('<span class="market-badge">BILLmanager</span>');
      }
      if (provider.sponsored) badges.push('<span class="market-badge market-badge-partner">Партнёр</span>');
      return badges.join("");
    };

    const renderGrid = () => {
      const items = filteredProviders();
      grid.innerHTML = items
        .map(
          (provider) => `
          <button type="button" class="market-card" data-domain="${escapeHtml(provider.domain)}">
            <span class="market-card-top">
              <span class="market-card-domain">${escapeHtml(provider.domain)}</span>
              <span class="market-card-badges">${renderBadges(provider)}</span>
            </span>
            <strong>${escapeHtml(provider.name)}</strong>
            <span class="market-card-price">${escapeHtml(provider.price_hint || "")}</span>
            <span class="market-card-flags">${(provider.country_labels || [])
              .slice(0, 4)
              .map((country) => country.flag)
              .join(" ")}</span>
          </button>
        `,
        )
        .join("");
      emptyState?.classList.toggle("hidden", items.length > 0);
    };

    const renderDetail = (provider) => {
      const promo = provider.promo_text
        ? `<p class="market-detail-promo">${escapeHtml(provider.promo_text)}</p>`
        : "";
      const api = provider.api_docs_url
        ? `<a class="secondary-link" href="${escapeHtml(provider.api_docs_url)}" target="_blank" rel="noreferrer">Документация API</a>`
        : "";
      const plans = (provider.plans || [])
        .map(
          (plan) => `
          <article class="market-plan">
            <strong>${escapeHtml(plan.name || "Тариф")}</strong>
            <span class="market-plan-price">${escapeHtml(formatPlanPrice(plan))}</span>
            <span class="market-plan-specs">${escapeHtml(formatPlanSpecs(plan))}</span>
          </article>
        `,
        )
        .join("");
      const visitRel = provider.sponsored ? "noreferrer sponsored" : "noreferrer";
      detailRoot.innerHTML = `
        <div class="market-detail-head">
          <div>
            <span class="market-card-domain">${escapeHtml(provider.domain)}</span>
            <h2>${escapeHtml(provider.name)}</h2>
            <p class="muted">${escapeHtml(provider.notes || "")}</p>
            ${promo}
          </div>
          <div class="market-detail-badges">${renderBadges(provider)}</div>
        </div>
        <div class="market-plans">${plans}</div>
        <div class="market-detail-actions">
          <a class="primary" href="/?add=server&template=${encodeURIComponent(provider.domain)}">Создать сервер</a>
          <a class="secondary" href="${escapeHtml(provider.visit_url || provider.website_url || "#")}" target="_blank" rel="${visitRel}">На сайт провайдера</a>
          ${api}
        </div>
      `;
    };

    const showList = () => {
      activeDomain = "";
      listView.hidden = false;
      detailView.hidden = true;
    };

    const showDetail = (domain) => {
      const provider = providers.find((item) => item.domain === domain);
      if (!provider) return;
      activeDomain = domain;
      renderDetail(provider);
      listView.hidden = true;
      detailView.hidden = false;
    };

    countryScroll.innerHTML = [
      `<button type="button" class="market-country active" data-country="">🌍 Все</button>`,
      ...countries.map(
        (country) =>
          `<button type="button" class="market-country" data-country="${escapeHtml(country.code)}">${country.flag} ${escapeHtml(country.name)}</button>`,
      ),
    ].join("");

    countryScroll.querySelectorAll("[data-country]").forEach((button) => {
      button.addEventListener("click", () => {
        activeCountry = button.dataset.country || "";
        countryScroll.querySelectorAll(".market-country").forEach((node) => {
          node.classList.toggle("active", node === button);
        });
        renderGrid();
        showList();
      });
    });

    searchInput?.addEventListener("input", () => {
      renderGrid();
      showList();
    });

    grid.addEventListener("click", (event) => {
      const card = event.target.closest(".market-card");
      if (!card) return;
      showDetail(card.dataset.domain || "");
    });

    backButton?.addEventListener("click", showList);

    if (notice && document.querySelector("#market-notice")) {
      document.querySelector("#market-notice").textContent = notice;
    }

    renderPromos();
    renderGrid();

    const requested = new URLSearchParams(window.location.search).get("provider");
    if (requested && providers.some((item) => item.domain === requested)) {
      showDetail(requested);
      history.replaceState({}, "", "/providers");
    }
  };
})();
