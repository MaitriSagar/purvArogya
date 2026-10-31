// All numbers come from the notebook, measured on the 30% of people the models never saw.
(function () {
  // test ROC-AUC: diabetes, heart disease, stroke
  const comparison = [
    ["Logistic regression, default settings", [0.811, 0.834, 0.802]],
    ["Logistic regression, tuned (used in this app)", [0.811, 0.834, 0.802]],
    ["Random forest", [0.817, 0.835, 0.802]],
    ["XGBoost, tuned", [0.817, 0.836, 0.803]],
  ];

  // people who really have the condition and get flagged, out of 100
  const caught = [
    ["Default settings", [18, 7, 0]],
    ["Class weights (used in this app)", [76, 79, 77]],
  ];

  // odds ratio per one standard deviation, above 1 raises the score
  const odds = [
    ["Age group", [1.71, 2.70, 2.22]],
    ["General health", [1.67, 1.71, 1.53]],
    ["Blood pressure", [1.44, 1.37, 1.37]],
    ["BMI", [1.52, 1.00, 0.96]],
    ["Cholesterol", [1.36, 1.33, 1.12]],
  ];

  const head = ["", "Diabetes", "Heart disease", "Stroke"];

  function table(rows, formatCell) {
    const header = head.map((h) => `<th>${h}</th>`).join("");
    const body = rows
      .map(([label, values]) =>
        `<tr><td>${label}</td>${values.map((v) => `<td>${formatCell(v)}</td>`).join("")}</tr>`)
      .join("");
    return `<table class="data-table"><tr>${header}</tr>${body}</table>`;
  }

  // a short bar plus the number; 2.70 (the biggest value) fills the bar
  function oddsCell(v) {
    const width = Math.max(0, Math.min(100, ((v - 1) / 1.7) * 100));
    return `<div class="bar"><i style="width:${width.toFixed(0)}%"></i></div>${v.toFixed(2)}`;
  }

  document.getElementById("compare-table").innerHTML = table(comparison, (v) => v.toFixed(3));
  document.getElementById("caught-table").innerHTML = table(caught, (v) => `${v} in 100`);
  document.getElementById("odds-table").innerHTML = table(odds, oddsCell);
})();