(() => {
  const manualLabel = "Заполнить вручную";

  const labelFor = (item) => `${item.name} · ${item.domain}`;

  const matches = (item, query) => {
    if (!query) return true;
    const haystack = `${item.name} ${item.domain}`.toLowerCase();
    return haystack.includes(query);
  };

  window.initTemplatePicker = (root, templates, onSelect) => {
    if (!root || root.dataset.pickerReady === "1") return;
    root.dataset.pickerReady = "1";

    const input = root.querySelector(".template-picker-input");
    const menu = root.querySelector(".template-picker-menu");
    if (!input || !menu) return;

    let activeIndex = -1;
    let visibleItems = [];

    const closeMenu = () => {
      menu.hidden = true;
      activeIndex = -1;
    };

    const pick = (item, index) => {
      if (!item) {
        input.value = "";
        closeMenu();
        onSelect?.(null, -1);
        return;
      }
      input.value = labelFor(item);
      closeMenu();
      onSelect?.(item, index);
    };

    const renderMenu = () => {
      const query = input.value.trim().toLowerCase();
      visibleItems = templates
        .map((item, index) => ({ item, index }))
        .filter(({ item }) => matches(item, query));

      menu.innerHTML = "";

      const manual = document.createElement("li");
      manual.className = "template-picker-option muted";
      manual.setAttribute("role", "option");
      manual.dataset.index = "";
      manual.textContent = manualLabel;
      menu.appendChild(manual);

      visibleItems.forEach(({ item, index }, listIndex) => {
        const option = document.createElement("li");
        option.className = "template-picker-option";
        option.setAttribute("role", "option");
        option.dataset.index = String(index);
        option.dataset.listIndex = String(listIndex);
        option.textContent = labelFor(item);
        menu.appendChild(option);
      });

      menu.hidden = false;
      activeIndex = -1;
    };

    const options = () => Array.from(menu.querySelectorAll(".template-picker-option"));

    const setActive = (listIndex) => {
      const items = options();
      items.forEach((node) => node.classList.remove("active"));
      if (listIndex < 0 || listIndex >= items.length) {
        activeIndex = -1;
        return;
      }
      activeIndex = listIndex;
      items[listIndex].classList.add("active");
      items[listIndex].scrollIntoView({ block: "nearest" });
    };

    const pickActive = () => {
      const items = options();
      if (activeIndex < 0 || activeIndex >= items.length) return;
      const node = items[activeIndex];
      const index = node.dataset.index;
      if (!index) {
        pick(null, -1);
        return;
      }
      pick(templates[Number(index)], Number(index));
    };

    input.addEventListener("focus", renderMenu);
    input.addEventListener("input", renderMenu);
    input.addEventListener("keydown", (event) => {
      const items = options();
      if (event.key === "ArrowDown") {
        event.preventDefault();
        if (menu.hidden) renderMenu();
        setActive(Math.min(activeIndex + 1, items.length - 1));
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        setActive(Math.max(activeIndex - 1, 0));
      } else if (event.key === "Enter") {
        if (!menu.hidden) {
          event.preventDefault();
          pickActive();
        }
      } else if (event.key === "Escape") {
        closeMenu();
      }
    });

    menu.addEventListener("mousedown", (event) => {
      event.preventDefault();
    });

    menu.addEventListener("click", (event) => {
      const option = event.target.closest(".template-picker-option");
      if (!option) return;
      const index = option.dataset.index;
      if (!index) {
        pick(null, -1);
        return;
      }
      pick(templates[Number(index)], Number(index));
    });

    document.addEventListener("click", (event) => {
      if (!root.contains(event.target)) closeMenu();
    });
  };
})();
