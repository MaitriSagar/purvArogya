// everything the person answers is stored here, then sent to /predict at the end
const answers = {};

const screens = document.querySelectorAll(".screen");
const progress = document.getElementById("progress");
const questionCount = screens.length - 2; // welcome and results are not questions
let current = 0;

// one bar per question screen
for (let i = 0; i < questionCount; i++) {
  progress.appendChild(document.createElement("span"));
}

function show(index) {
  if (index >= screens.length) return; // no next screen yet
  current = index;
  screens.forEach((screen, i) => screen.classList.toggle("active", i === index));
  progress.classList.toggle("hidden", index === 0);
  [...progress.children].forEach((bar, i) => bar.classList.toggle("done", i < index - 1));
  window.scrollTo(0, 0);
  const first = screens[index].querySelector("input, select");
  if (first) first.focus({ preventScroll: true });
}

// age: only allow whole numbers from 18 to 99
const ageInput = document.getElementById("age");
const ageError = document.getElementById("age-error");
const ageNext = document.getElementById("age-next");

ageInput.addEventListener("input", () => {
  const age = Number(ageInput.value);
  const valid = Number.isInteger(age) && age >= 18 && age <= 99;
  ageNext.disabled = !valid;
  if (valid) {
    answers.age = age;
    ageError.textContent = "";
  } else if (ageInput.value !== "") {
    ageError.textContent = "This tool is for adults, ages 18 to 99.";
  } else {
    ageError.textContent = "";
  }
});

// height and weight: the same limits as the API, including the BMI check
const heightInput = document.getElementById("height");
const weightInput = document.getElementById("weight");
const bodyError = document.getElementById("body-error");
const bodyNext = document.getElementById("body-next");

function checkBody() {
  const height = Number(heightInput.value);
  const weight = Number(weightInput.value);
  bodyNext.disabled = true;
  bodyError.textContent = "";
  if (!heightInput.value || !weightInput.value) return;

  if (height < 120 || height > 220) {
    bodyError.textContent = "Height should be between 120 and 220 cm.";
    return;
  }
  if (weight < 30 || weight > 250) {
    bodyError.textContent = "Weight should be between 30 and 250 kg.";
    return;
  }
  const bmi = weight / (height / 100) ** 2;
  if (bmi < 12 || bmi > 100) {
    bodyError.textContent = "These two values don't look right together. Please check them.";
    return;
  }
  answers.height_cm = height;
  answers.weight_kg = weight;
  bodyNext.disabled = false;
}
heightInput.addEventListener("input", checkBody);
weightInput.addEventListener("input", checkBody);

// optional questions: a blank field means skipped, so we leave the key out
const optionalKinds = {
  smoking: "text", activity: "text",
  drinks: "number", physical_days: "number", mental_days: "number",
};
const optionalError = document.getElementById("optional-error");
const resultsBody = document.getElementById("results-body");

const diseaseNames = { diabetes: "Diabetes", cvd: "Heart disease", stroke: "Stroke" };

function readOptional() {
  optionalError.textContent = "";
  for (const [key, kind] of Object.entries(optionalKinds)) {
    const input = document.getElementById(key);
    delete answers[key];
    if (input.value === "") continue;
    if (kind === "number") {
      const value = Number(input.value);
      const max = Number(input.max);
      const wholeDays = key !== "drinks";
      if (value < 0 || value > max || (wholeDays && !Number.isInteger(value))) {
        optionalError.textContent = "Please check the numbers. Drinks go up to 50, days up to 30.";
        return false;
      }
      answers[key] = value;
    } else {
      answers[key] = input.value;
    }
  }
  return true;
}

const levelSentence = {
  Lower: "Your score is well below the line where this tool raises a flag.",
  Moderate: "Your score is below the line where this tool raises a flag, but not low.",
  Higher: "Your score is above the line where this tool raises a flag. It is a reason to talk to a doctor, not a diagnosis.",
};

function capitalise(text) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function buildGauge(percentile, flagLine) {
  // zones are cut at 0, flag_line / 2, flag_line and 100
  const half = flagLine / 2;
  const widths = [half, flagLine - half, 100 - flagLine];
  const names = ["Lower", "Moderate", "Higher"];
  const at = Math.min(99, Math.max(1, percentile)); // keep the marker inside the bar

  const zones = names.map((n, i) => `<span class="zone ${n}" style="flex:${widths[i]}"></span>`).join("");
  const labels = names.map((n, i) => `<span style="flex:${widths[i]}">${n}</span>`).join("");
  return `
    <div class="gauge">
      <div class="gauge-bar">${zones}<i class="marker" style="left:${at}%"></i></div>
      <div class="gauge-labels">${labels}</div>
    </div>`;
}

function renderResults(data) {
  resultsBody.innerHTML = "";
  for (const [key, name] of Object.entries(diseaseNames)) {
    const r = data[key];
    const up = r.pushing_up.map(capitalise).join(", ");
    const down = r.pulling_down.map(capitalise).join(", ");
    const card = document.createElement("div");
    card.className = "result";
    card.innerHTML = `
      <h3>${name}</h3>
      <div class="level"><span class="dot ${r.level}"></span>${r.level}</div>
      ${buildGauge(r.percentile, r.flag_line)}
      <p>${levelSentence[r.level]}</p>
      <p class="small">${up ? "Raising your score: " + up + "." : ""} ${down ? "Lowering it: " + down + "." : ""}</p>`;
    resultsBody.appendChild(card);
  }

        const skipped = Object.keys(optionalKinds).some((k) => !(k in answers));
  const anyFlagged = Object.keys(diseaseNames).some((k) => data[k].flagged);

  const advice = anyFlagged
    ? "Something here is worth a conversation with your doctor. This is not a diagnosis, and many people with a flag turn out to be fine, but a routine check-up is a kind thing to do for yourself."
    : "Nothing is flagged right now, which is good news. This is a screening and not a promise, so keep up your regular check-ups and listen to your body.";
  const skippedNote = skipped
    ? " You skipped a few questions, so we used typical answers for those."
    : "";

  document.getElementById("results-note").innerHTML = `<p>${advice}${skippedNote}</p>`;
}

document.getElementById("see-results").addEventListener("click", async () => {
  if (!readOptional()) return;
  show(current + 1);
  resultsBody.textContent = "Working it out...";
  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(answers),
    });
    if (!response.ok) throw new Error("server said " + response.status);
    renderResults(await response.json());
  } catch (error) {
    resultsBody.textContent = "Something went wrong. Please try again.";
    console.error(error);
  }
});

// switch between the wizard and the "How it was built" page
const aboutPage = document.getElementById("about");
const tabs = document.querySelectorAll(".tab");

function showView(view) {
  tabs.forEach((t) => t.classList.toggle("active", t.dataset.view === view));
  aboutPage.classList.toggle("active", view === "about");
  screens.forEach((s, i) => s.classList.toggle("active", view === "check" && i === current));
  progress.classList.toggle("hidden", view === "about" || current === 0);
  window.scrollTo(0, 0);
}

// one click handler for every button on the page
document.addEventListener("click", (event) => {
      const tab = event.target.closest(".tab");
  if (tab) { 
    showView(tab.dataset.view); return; 
    }
  const choice = event.target.closest(".choice");
  if (choice) {
    answers[choice.dataset.field] = choice.dataset.value;
    choice.parentElement.querySelectorAll(".choice")
      .forEach((c) => c.classList.toggle("selected", c === choice));
    setTimeout(() => show(current + 1), 250); // short pause so the selection is visible
    return;
  }
  if (event.target.closest("[data-next]")) show(current + 1);
  if (event.target.closest("[data-back]")) show(current - 1);
    if (event.target.closest("[data-restart]")) location.reload();
});

// Enter presses the main button of the current screen, if it is enabled
document.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" || aboutPage.classList.contains("active")) return;
  if (event.target.tagName === "BUTTON" || event.target.tagName === "SELECT") return; // let those behave normally
  const primary = screens[current].querySelector(".pill:not([disabled])");
  if (primary) {
    event.preventDefault();
    primary.click();
  }
});
show(0);