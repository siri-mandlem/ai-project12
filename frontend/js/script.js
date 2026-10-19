"use strict";

const calculateFineButton = document.querySelector("[data-calculate-fine]");
if (calculateFineButton) {
    calculateFineButton.addEventListener("click", () => {
        const daysLate = Number.parseInt(
            document.querySelector("#days-late").value,
            10
        );
        const lateDays = Number.isFinite(daysLate) ? Math.max(0, daysLate) : 0;
        const fine = lateDays * 0.5;
        document.querySelector("#fine-amount").textContent =
            `Estimated fine: $${fine.toFixed(2)}`;
    });
}
