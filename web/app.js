// everything the person answers is stored here, then sent to /predict at the end
const answers = {};

const screens = document.querySelectorAll(".screen");
const progress = document.getElementById("progress");
const questionCount = screens.length - 1; // the welcome screen is not a question
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
  [...progress.children].forEach((bar, i) => bar.classList.toggle("done", i < index));
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
});

show(0);