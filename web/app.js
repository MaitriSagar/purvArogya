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

function renderResults(data) {
  resultsBody.innerHTML = "";
  for (const [key, name] of Object.entries(diseaseNames)) {
    const r = data[key];
    const card = document.createElement("div");
    card.className = "result";
    card.innerHTML = `
      <h3>${name}</h3>
      <p><span class="level">${r.level}</span>, higher than about ${r.percentile} in 100 people in the survey.</p>
      <p>Pushing it up: ${r.pushing_up.join(", ") || "nothing stands out"}</p>
      <p>Pulling it down: ${r.pulling_down.join(", ") || "nothing stands out"}</p>`;
    resultsBody.appendChild(card);
  }
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

// one click handler for every button on the page
document.addEventListener("click", (event) => {
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

show(0);