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
  });
}

function getSelectedOffDays() {
  return Array.from(document.querySelectorAll("#off-day-list .off-day-chip")).map(
    (chip) => chip.dataset.date,
  );
}

function isOffDay(isoDate) {
  return Boolean(document.querySelector(`#off-day-list .off-day-chip[data-date="${isoDate}"]`));
}

function setCalendarDaySelected(isoDate, selected) {
  const button = document.querySelector(
    `#off-day-calendar .off-day-calendar-day[data-date="${isoDate}"]`,
  );
  if (!button) {
    return;
  }
  button.classList.toggle("is-selected", selected);
  button.setAttribute("aria-pressed", selected ? "true" : "false");
  const label = formatDisplayDate(isoDate);
  button.setAttribute("aria-label", selected ? `${label}, off day` : `${label}, not selected`);
}

function removeOffDayChip(isoDate) {
  document.querySelector(`#off-day-list .off-day-chip[data-date="${isoDate}"]`)?.remove();
  setCalendarDaySelected(isoDate, false);
  updateVacationSummary();
}

function toggleOffDay(isoDate) {
  if (isOffDay(isoDate)) {
    removeOffDayChip(isoDate);
  } else {
    addOffDayChip(isoDate);
    setCalendarDaySelected(isoDate, true);
  }
}

function buildMonthGrid(year, month) {
  const firstOfMonth = new Date(year, month - 1, 1);
  const lastDay = new Date(year, month, 0).getDate();
  // Monday = 0 … Sunday = 6
  const startOffset = (firstOfMonth.getDay() + 6) % 7;
  const pad = (value) => String(value).padStart(2, "0");
  const cells = [];

  for (let i = 0; i < startOffset; i += 1) {
    cells.push({ type: "pad" });
  }
  for (let day = 1; day <= lastDay; day += 1) {
    cells.push({ type: "day", isoDate: `${year}-${pad(month)}-${pad(day)}`, day });
  }
  while (cells.length % 7 !== 0) {
    cells.push({ type: "pad" });
  }
  return cells;
}

function renderOffDayCalendar() {
  const calendar = document.getElementById("off-day-calendar");
  const monthInput = document.getElementById("month");
  if (!calendar || !monthInput?.value) {
    return;
  }

  const [year, month] = monthInput.value.split("-").map(Number);
  const selected = new Set(getSelectedOffDays());
  const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const grid = document.createElement("div");
  grid.className = "off-day-calendar-grid";
  grid.setAttribute("role", "grid");

  const header = document.createElement("div");
  header.className = "off-day-calendar-row off-day-calendar-header";
  weekdays.forEach((name) => {
    const cell = document.createElement("div");
    cell.className = "off-day-calendar-head";
    cell.setAttribute("role", "columnheader");
    cell.textContent = name;
    header.appendChild(cell);
  });
  grid.appendChild(header);

  const body = document.createElement("div");
  body.className = "off-day-calendar-body";
  body.setAttribute("role", "rowgroup");

  const row = document.createElement("div");
  row.className = "off-day-calendar-row";
  row.setAttribute("role", "row");

  buildMonthGrid(year, month).forEach((cell) => {
    if (cell.type === "pad") {
      const pad = document.createElement("div");
      pad.className = "off-day-calendar-pad";
      pad.setAttribute("role", "gridcell");
      row.appendChild(pad);
      return;
    }

    const button = document.createElement("button");
    button.type = "button";
    button.className = "off-day-calendar-day";
    button.dataset.date = cell.isoDate;
    button.setAttribute("role", "gridcell");
    button.textContent = String(cell.day);
    const isSelected = selected.has(cell.isoDate);
    button.classList.toggle("is-selected", isSelected);
    button.setAttribute("aria-pressed", isSelected ? "true" : "false");
    const label = formatDisplayDate(cell.isoDate);
    button.setAttribute("aria-label", isSelected ? `${label}, off day` : `${label}, not selected`);
    button.addEventListener("click", () => toggleOffDay(cell.isoDate));
    row.appendChild(button);
  });

  body.appendChild(row);
  grid.appendChild(body);
  calendar.replaceChildren(grid);
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
    removeOffDayChip(isoDate);
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

  if (monthInput) {
    monthInput.addEventListener("change", () => {
      const url = new URL(window.location.href);
      url.searchParams.set("month", monthInput.value);
      window.location.href = url.toString();
    });
  }

  renderOffDayCalendar();
  updateVacationSummary();

  document.querySelectorAll(".chip-remove").forEach((button) => {
    button.addEventListener("click", () => {
      const chip = button.closest(".off-day-chip");
      if (chip?.dataset.date) {
        removeOffDayChip(chip.dataset.date);
      }
    });
  });
});
