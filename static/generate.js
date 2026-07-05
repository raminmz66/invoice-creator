function computeRemaining(carriedOver, entitlement, used) {
  return carriedOver + entitlement - used;
}

function getSelectedMonthBounds() {
  const monthInput = document.getElementById("month");
  if (!monthInput || !monthInput.value) {
    return { min: "", max: "" };
  }
  const [year, month] = monthInput.value.split("-").map(Number);
  const lastDay = new Date(year, month, 0).getDate();
  const pad = (value) => String(value).padStart(2, "0");
  return {
    min: `${year}-${pad(month)}-01`,
    max: `${year}-${pad(month)}-${pad(lastDay)}`,
  };
}

function updateVacationSummary() {
  const config = window.invoiceCreator;
  if (!config) {
    return;
  }
  const offDayCount = document.querySelectorAll("#off-day-list .off-day-chip").length;
  const used = config.baseUsed + offDayCount;
  const remaining = computeRemaining(config.carriedOver, config.entitlement, used);
  const usedEl = document.getElementById("vacation-used");
  const remainingEl = document.getElementById("vacation-remaining");
  if (usedEl) {
    usedEl.textContent = String(used);
  }
  if (remainingEl) {
    remainingEl.textContent = String(remaining);
  }
}

function formatDisplayDate(isoDate) {
  const date = new Date(`${isoDate}T00:00:00`);
  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function addOffDayChip(isoDate) {
  const list = document.getElementById("off-day-list");
  if (!list || list.querySelector(`[data-date="${isoDate}"]`)) {
    return;
  }

  const chip = document.createElement("div");
  chip.className = "off-day-chip";
  chip.dataset.date = isoDate;

  const label = document.createElement("span");
  label.textContent = formatDisplayDate(isoDate);

  const removeButton = document.createElement("button");
  removeButton.type = "button";
  removeButton.className = "chip-remove";
  removeButton.setAttribute("aria-label", `Remove ${label.textContent}`);
  removeButton.textContent = "×";
  removeButton.addEventListener("click", () => {
    chip.remove();
    updateVacationSummary();
  });

  const hiddenInput = document.createElement("input");
  hiddenInput.type = "hidden";
  hiddenInput.name = "off_days";
  hiddenInput.value = isoDate;

  chip.append(label, removeButton, hiddenInput);
  list.appendChild(chip);
  updateVacationSummary();
}

document.addEventListener("DOMContentLoaded", () => {
  const monthInput = document.getElementById("month");
  const picker = document.getElementById("off-day-picker");
  const addButton = document.getElementById("add-off-day");

  if (monthInput) {
    monthInput.addEventListener("change", () => {
      const url = new URL(window.location.href);
      url.searchParams.set("month", monthInput.value);
      window.location.href = url.toString();
    });
  }

  function syncPickerBounds() {
    if (!picker) {
      return;
    }
    const bounds = getSelectedMonthBounds();
    picker.min = bounds.min;
    picker.max = bounds.max;
  }

  syncPickerBounds();
  updateVacationSummary();

  document.querySelectorAll(".chip-remove").forEach((button) => {
    button.addEventListener("click", () => {
      button.closest(".off-day-chip")?.remove();
      updateVacationSummary();
    });
  });

  addButton?.addEventListener("click", () => {
    if (!picker?.value) {
      return;
    }
    addOffDayChip(picker.value);
    picker.value = "";
  });
});
