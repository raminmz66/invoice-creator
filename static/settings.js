function computeRemaining(carriedOver, entitlement, used) {
  return carriedOver + entitlement - used;
}

function updateRemainingDisplay() {
  const entitlement = Number(document.getElementById("annual_vacation_entitlement")?.value || 0);
  const carriedOver = Number(document.getElementById("carried_over")?.value || 0);
  const used = Number(document.getElementById("used_this_year")?.value || 0);
  const remainingDisplay = document.getElementById("remaining-display");
  if (remainingDisplay) {
    remainingDisplay.textContent = String(computeRemaining(carriedOver, entitlement, used));
  }
}

document.addEventListener("DOMContentLoaded", () => {
  ["annual_vacation_entitlement", "carried_over", "used_this_year"].forEach((id) => {
    document.getElementById(id)?.addEventListener("input", updateRemainingDisplay);
  });
  updateRemainingDisplay();

  const toast = document.getElementById("toast");
  if (toast) {
    setTimeout(() => {
      toast.remove();
    }, 2000);
  }
});
