(() => {
  const fileInput = document.querySelector("[data-file-input]");
  const fileLabel = document.querySelector("[data-file-label]");
  const fileDrop = document.querySelector("[data-file-drop]");
  const uploadSubmit = document.querySelector("[data-upload-submit]");

  if (fileInput && fileLabel) {
    const defaultFileLabel = fileLabel.textContent;

    function setPickedFile(file) {
      fileLabel.textContent = file?.name || defaultFileLabel;
      if (uploadSubmit) {
        uploadSubmit.disabled = !file;
        uploadSubmit.textContent = file ? "편집 시작" : "파일을 선택해요";
      }
    }

    fileInput.addEventListener("change", () => {
      setPickedFile(fileInput.files?.[0]);
    });

    if (fileDrop) {
      ["dragenter", "dragover"].forEach((eventName) => {
        fileDrop.addEventListener(eventName, (event) => {
          event.preventDefault();
          fileDrop.classList.add("is-dragging");
          fileDrop.setAttribute("aria-label", "파일을 놓으면 준비돼요");
        });
      });

      ["dragleave", "drop"].forEach((eventName) => {
        fileDrop.addEventListener(eventName, () => {
          fileDrop.classList.remove("is-dragging");
          fileDrop.removeAttribute("aria-label");
        });
      });

      fileDrop.addEventListener("drop", (event) => {
        event.preventDefault();
        const file = event.dataTransfer?.files?.[0];
        if (!file) return;
        fileInput.files = event.dataTransfer.files;
        setPickedFile(file);
      });
    }
  }

  const editor = document.querySelector("[data-editor]");
  if (!editor) return;

  const form = document.querySelector("[data-process-form]");
  const pages = document.querySelector("[data-pages]");
  const regionsInput = document.querySelector("[data-regions-input]");
  const countNode = document.querySelector("[data-region-count]");
  const submitButton = document.querySelector("[data-submit]");
  const undoButton = document.querySelector("[data-undo]");
  const clearButton = document.querySelector("[data-clear]");
  const blurRange = document.querySelector("[data-blur-range]");
  const blurValue = document.querySelector("[data-blur-value]");
  const zoomRange = document.querySelector("[data-zoom-range]");
  const zoomValue = document.querySelector("[data-zoom-value]");
  const zoomInButton = document.querySelector("[data-zoom-in]");
  const zoomOutButton = document.querySelector("[data-zoom-out]");
  const modeButtons = [...document.querySelectorAll("[data-mode-button]")];
  const viewModeButtons = [...document.querySelectorAll("[data-view-mode-button]")];
  const pageCards = [...document.querySelectorAll("[data-page-card]")];
  const pagerControls = document.querySelector("[data-pager-controls]");
  const pagePrevButton = document.querySelector("[data-page-prev]");
  const pageNextButton = document.querySelector("[data-page-next]");
  const pageStatus = document.querySelector("[data-page-status]");
  const helpModal = document.querySelector("[data-help-modal]");
  const helpOpen = document.querySelector("[data-help-open]");
  const helpCloseButtons = [...document.querySelectorAll("[data-help-close]")];

  const VIEW_MODE_STORAGE_KEY = "pdfBlurViewMode";
  const regions = [];
  const history = [];
  let drawing = null;
  let selectedRegion = null;
  let mode = editor.dataset.mode || "draw";
  let viewMode = readStoredViewMode() || editor.dataset.viewMode || "scroll";
  let activePageIndex = 0;

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function regionData(region) {
    return {
      page: region.page,
      x: region.x,
      y: region.y,
      width: region.width,
      height: region.height,
    };
  }

  function snapshot() {
    return regions.map(regionData);
  }

  function pushHistory() {
    history.push(snapshot());
    undoButton.disabled = false;
  }

  function canvasForPage(page) {
    return document.querySelector(`.page-canvas[data-page="${page}"]`);
  }

  function syncElement(region) {
    region.element.style.left = `${region.x * 100}%`;
    region.element.style.top = `${region.y * 100}%`;
    region.element.style.width = `${region.width * 100}%`;
    region.element.style.height = `${region.height * 100}%`;
  }

  function selectRegion(region) {
    if (selectedRegion) {
      selectedRegion.element.classList.remove("is-selected");
    }
    selectedRegion = region;
    if (selectedRegion) {
      selectedRegion.element.classList.add("is-selected");
      selectedRegion.canvas.focus({ preventScroll: true });
    }
  }

  function createRegion(canvas, values, shouldRecord = true) {
    if (shouldRecord) pushHistory();

    const layer = canvas.querySelector(".region-layer");
    const element = document.createElement("div");
    element.className = "region-box";
    element.tabIndex = -1;
    layer.appendChild(element);

    const region = {
      page: Number(canvas.dataset.page),
      x: clamp(values.x, 0, 1),
      y: clamp(values.y, 0, 1),
      width: clamp(values.width, 0.004, 1),
      height: clamp(values.height, 0.004, 1),
      element,
      canvas,
    };

    region.width = Math.min(region.width, 1 - region.x);
    region.height = Math.min(region.height, 1 - region.y);
    element.addEventListener("pointerdown", (event) => {
      selectRegion(region);
      if (mode === "select") {
        event.stopPropagation();
      }
    });

    syncElement(region);
    regions.push(region);
    selectRegion(region);
    updateControls();
    return region;
  }

  function removeRegion(region, shouldRecord = true) {
    if (!region) return;
    if (shouldRecord) pushHistory();

    const index = regions.indexOf(region);
    if (index >= 0) regions.splice(index, 1);
    region.element.remove();
    if (selectedRegion === region) {
      selectRegion(regions[regions.length - 1] || null);
    }
    updateControls();
  }

  function clearRegions() {
    if (!regions.length) return;
    pushHistory();
    while (regions.length) {
      const region = regions.pop();
      region.element.remove();
    }
    selectRegion(null);
    updateControls();
  }

  function restoreSnapshot(items) {
    while (regions.length) {
      const region = regions.pop();
      region.element.remove();
    }
    selectRegion(null);
    items.forEach((item) => {
      const canvas = canvasForPage(item.page);
      if (canvas) createRegion(canvas, item, false);
    });
    updateControls();
  }

  function undo() {
    if (!history.length) return;
    restoreSnapshot(history.pop());
    undoButton.disabled = history.length === 0;
  }

  function updateControls() {
    const hasRegions = regions.length > 0;
    countNode.textContent = String(regions.length);
    submitButton.disabled = !hasRegions;
    clearButton.disabled = !hasRegions;
    undoButton.disabled = history.length === 0;
    regionsInput.value = JSON.stringify(regions.map(regionData));
  }

  function setMode(nextMode) {
    mode = nextMode;
    editor.dataset.mode = mode;
    modeButtons.forEach((button) => {
      const isActive = button.dataset.modeButton === mode;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", String(isActive));
    });
  }

  function canvasPoint(event, canvas) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: clamp(event.clientX - rect.left, 0, rect.width),
      y: clamp(event.clientY - rect.top, 0, rect.height),
      width: rect.width,
      height: rect.height,
    };
  }

  function pointerRegion(start, current) {
    const left = Math.min(start.x, current.x);
    const top = Math.min(start.y, current.y);
    const width = Math.abs(current.x - start.x);
    const height = Math.abs(current.y - start.y);

    return {
      x: left / start.width,
      y: top / start.height,
      width: width / start.width,
      height: height / start.height,
    };
  }

  function updateDraft(element, start, current) {
    const draft = pointerRegion(start, current);
    element.style.left = `${draft.x * 100}%`;
    element.style.top = `${draft.y * 100}%`;
    element.style.width = `${draft.width * 100}%`;
    element.style.height = `${draft.height * 100}%`;
    return draft;
  }

  function moveRegion(region, dx, dy) {
    pushHistory();
    region.x = clamp(region.x + dx, 0, 1 - region.width);
    region.y = clamp(region.y + dy, 0, 1 - region.height);
    syncElement(region);
    updateControls();
  }

  function resizeRegion(region, dw, dh) {
    pushHistory();
    region.width = clamp(region.width + dw, 0.004, 1 - region.x);
    region.height = clamp(region.height + dh, 0.004, 1 - region.y);
    syncElement(region);
    updateControls();
  }

  function updateZoom(value) {
    const zoom = clamp(Number(value), Number(zoomRange.min), Number(zoomRange.max));
    zoomRange.value = String(zoom);
    pages.style.setProperty("--zoom", String(zoom / 100));
    zoomValue.textContent = `${zoom}%`;
  }

  function readStoredViewMode() {
    try {
      const storedValue = window.localStorage?.getItem(VIEW_MODE_STORAGE_KEY);
      return storedValue === "page" || storedValue === "scroll" ? storedValue : null;
    } catch {
      return null;
    }
  }

  function storeViewMode(nextMode) {
    try {
      window.localStorage?.setItem(VIEW_MODE_STORAGE_KEY, nextMode);
    } catch {
      // localStorage can be unavailable in restricted browser contexts.
    }
  }

  function pageIndexForCanvas(canvas) {
    const card = canvas?.closest("[data-page-card]");
    return card ? pageCards.indexOf(card) : -1;
  }

  function pageIndexForSelection() {
    return selectedRegion ? pageIndexForCanvas(selectedRegion.canvas) : -1;
  }

  function updatePageView(shouldResetScroll = false) {
    const isPageMode = viewMode === "page";
    editor.dataset.viewMode = viewMode;
    pages.dataset.viewMode = viewMode;

    pageCards.forEach((card, index) => {
      const isVisible = !isPageMode || index === activePageIndex;
      card.hidden = !isVisible;
      card.classList.toggle("is-active-page", isPageMode && isVisible);
      card.setAttribute("aria-hidden", String(!isVisible));
    });

    if (pagerControls) pagerControls.hidden = !isPageMode;
    if (pageStatus) pageStatus.textContent = `${Math.min(activePageIndex + 1, pageCards.length)} / ${pageCards.length}`;
    if (pagePrevButton) pagePrevButton.disabled = !isPageMode || activePageIndex <= 0;
    if (pageNextButton) pageNextButton.disabled = !isPageMode || activePageIndex >= pageCards.length - 1;

    if (isPageMode && selectedRegion && pageIndexForSelection() !== activePageIndex) {
      selectRegion(null);
    }

    if (shouldResetScroll) {
      pages.scrollTo({ left: 0, top: 0, behavior: "auto" });
    }
  }

  function setActivePage(index, shouldFocus = false) {
    if (!pageCards.length) return;
    activePageIndex = clamp(index, 0, pageCards.length - 1);
    updatePageView(true);

    if (shouldFocus) {
      pageCards[activePageIndex]?.querySelector(".page-canvas")?.focus({ preventScroll: true });
    }
  }

  function setViewMode(nextMode) {
    if (nextMode !== "page" && nextMode !== "scroll") return;

    const selectedPageIndex = pageIndexForSelection();
    if (nextMode === "page" && selectedPageIndex >= 0) {
      activePageIndex = selectedPageIndex;
    }

    viewMode = nextMode;
    storeViewMode(viewMode);
    viewModeButtons.forEach((button) => {
      const isActive = button.dataset.viewModeButton === viewMode;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", String(isActive));
    });
    updatePageView(nextMode === "page");
  }

  function openHelpModal() {
    if (!helpModal) return;
    helpModal.hidden = false;
    document.body.classList.add("has-modal");
    helpModal.querySelector(".help-modal-close")?.focus();
  }

  function closeHelpModal() {
    if (!helpModal || helpModal.hidden) return;
    helpModal.hidden = true;
    document.body.classList.remove("has-modal");
    helpOpen?.focus();
  }

  document.querySelectorAll(".page-canvas").forEach((canvas) => {
    const layer = canvas.querySelector(".region-layer");

    canvas.addEventListener("pointerdown", (event) => {
      if (event.button !== 0) return;
      if (mode === "select") {
        if (!event.target.classList.contains("region-box")) selectRegion(null);
        return;
      }

      canvas.setPointerCapture(event.pointerId);
      const start = canvasPoint(event, canvas);
      const element = document.createElement("div");
      element.className = "region-box is-drawing";
      layer.appendChild(element);
      drawing = { canvas, element, start };
      updateDraft(element, start, start);
    });

    canvas.addEventListener("pointermove", (event) => {
      if (!drawing || drawing.canvas !== canvas) return;
      updateDraft(drawing.element, drawing.start, canvasPoint(event, canvas));
    });

    canvas.addEventListener("pointerup", (event) => {
      if (!drawing || drawing.canvas !== canvas) return;
      canvas.releasePointerCapture(event.pointerId);
      const draft = updateDraft(drawing.element, drawing.start, canvasPoint(event, canvas));
      drawing.element.remove();
      drawing = null;

      if (draft.width >= 0.004 && draft.height >= 0.004) {
        createRegion(canvas, draft);
      } else {
        updateControls();
      }
    });

    canvas.addEventListener("pointercancel", () => {
      if (!drawing || drawing.canvas !== canvas) return;
      drawing.element.remove();
      drawing = null;
      updateControls();
    });

    canvas.addEventListener("keydown", (event) => {
      const key = event.key;
      const step = event.altKey ? 0.0025 : 0.015;

      if ((event.ctrlKey || event.metaKey) && key.toLowerCase() === "z") {
        event.preventDefault();
        undo();
        return;
      }

      if (key === "Enter" || key === " ") {
        event.preventDefault();
        createRegion(canvas, { x: 0.35, y: 0.35, width: 0.3, height: 0.18 });
        return;
      }

      if (key === "Delete" || key === "Backspace") {
        if (!selectedRegion) return;
        event.preventDefault();
        removeRegion(selectedRegion);
        return;
      }

      if (!selectedRegion) return;

      const arrowMap = {
        ArrowLeft: [-step, 0],
        ArrowRight: [step, 0],
        ArrowUp: [0, -step],
        ArrowDown: [0, step],
      };

      if (!arrowMap[key]) return;
      event.preventDefault();
      const [xDelta, yDelta] = arrowMap[key];
      if (event.shiftKey) {
        resizeRegion(selectedRegion, xDelta, yDelta);
      } else {
        moveRegion(selectedRegion, xDelta, yDelta);
      }
    });
  });

  document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "z") {
      event.preventDefault();
      undo();
      return;
    }

    const target = event.target;
    const isControl = target instanceof Element && target.matches("input, button, textarea, select");
    if (isControl || viewMode !== "page" || pageCards.length <= 1) {
      return;
    }

    if (event.key === "PageUp") {
      event.preventDefault();
      setActivePage(activePageIndex - 1, true);
    }

    if (event.key === "PageDown") {
      event.preventDefault();
      setActivePage(activePageIndex + 1, true);
    }
  });

  modeButtons.forEach((button) => {
    button.addEventListener("click", () => setMode(button.dataset.modeButton));
  });

  viewModeButtons.forEach((button) => {
    button.addEventListener("click", () => setViewMode(button.dataset.viewModeButton));
  });

  pagePrevButton?.addEventListener("click", () => setActivePage(activePageIndex - 1, true));
  pageNextButton?.addEventListener("click", () => setActivePage(activePageIndex + 1, true));

  helpOpen?.addEventListener("click", openHelpModal);
  helpCloseButtons.forEach((button) => {
    button.addEventListener("click", closeHelpModal);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeHelpModal();
  });

  undoButton.addEventListener("click", undo);
  clearButton.addEventListener("click", clearRegions);

  blurRange.addEventListener("input", () => {
    blurValue.textContent = blurRange.value;
  });

  zoomRange.addEventListener("input", () => updateZoom(zoomRange.value));
  zoomInButton.addEventListener("click", () => updateZoom(Number(zoomRange.value) + 10));
  zoomOutButton.addEventListener("click", () => updateZoom(Number(zoomRange.value) - 10));

  form.addEventListener("submit", (event) => {
    updateControls();
    if (regions.length === 0) {
      event.preventDefault();
    }
  });

  setMode(mode);
  setViewMode(viewMode);
  updateZoom(zoomRange.value);
  updateControls();
})();
