const form = document.querySelector("#study-form");
const task = document.querySelector("#task");
const levelContainer = document.querySelector("#level-container");
const input = document.querySelector("#study-input");
const inputLabel = document.querySelector("#input-label");
const inputHint = document.querySelector("#input-hint");
const runButton = document.querySelector("#run-button");
const copyButton = document.querySelector("#copy-button");
const result = document.querySelector("#result");
const serviceStatus = document.querySelector("#service-status");

const prompts = {
  qa: ["What are you curious about?", "Be specific or paste your study material.", "For example: Why does the moon appear to change shape?"],
  explain: ["What would you like explained?", "Name a concept and we’ll unpack it step by step.", "For example: How does a neural network learn?"],
  quiz: ["What should your quiz cover?", "Paste a passage or your study notes.", "Paste study material here to create three questions…"],
  summarize: ["What should we make sense of?", "Paste your notes or a longer passage.", "Paste text to turn it into a focused summary…"],
  learn: ["Where would you like to go deeper?", "Choose a topic and we’ll map a path forward.", "For example: Learning Python for data analysis"]
};

task.addEventListener("change", () => {
  const [label, hint, placeholder] = prompts[task.value];
  inputLabel.textContent = label;
  inputHint.textContent = hint;
  input.placeholder = placeholder;
  levelContainer.hidden = task.value !== "learn";
  input.maxLength = task.value === "quiz" ? 12000 : 20000;
});

function addText(parent, tag, text, className) {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  parent.append(element);
  return element;
}

function renderText(text) {
  result.replaceChildren();
  text.split("\n").forEach((line) => {
    const content = line.trim();
    if (!content) return;
    const labeledSection = content.match(/^(Short answer|Why it works|Example|Key takeaway):\s*(.*)$/i);
    if (labeledSection) {
      const paragraph = document.createElement("p");
      paragraph.className = "answer-section";
      addText(paragraph, "strong", `${labeledSection[1]}: `);
      paragraph.append(document.createTextNode(labeledSection[2]));
      result.append(paragraph);
    } else {
      addText(result, "p", content);
    }
  });
}

function animateResult() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  result.animate(
    [
      { opacity: 0, transform: "translateY(10px)" },
      { opacity: 1, transform: "translateY(0)" }
    ],
    { duration: 420, easing: "cubic-bezier(0.2, 0.7, 0.2, 1)" }
  );
}

function renderQuiz(data) {
  result.replaceChildren();
  data.questions.forEach((question, index) => {
    const block = document.createElement("section");
    block.className = "quiz-item";
    addText(block, "h3", `${String(index + 1).padStart(2, "0")}  ${question.question}`);
    const choices = document.createElement("div");
    choices.className = "choices";
    const feedback = document.createElement("p");
    feedback.className = "feedback";
    question.options.forEach((option, optionIndex) => {
      const button = document.createElement("button");
      button.className = "choice-button";
      button.type = "button";
      button.append(document.createTextNode(`${String.fromCharCode(65 + optionIndex)}  `));
      const label = document.createElement("span");
      label.textContent = option;
      button.append(label);
      button.addEventListener("click", () => {
        choices.querySelectorAll("button").forEach((choice) => { choice.disabled = true; });
        const correct = option === question.correct_answer;
        button.classList.add(correct ? "is-correct" : "is-wrong");
        feedback.textContent = `${correct ? "That’s it. " : `The answer is ${question.correct_answer}. `}${question.explanation}`;
        feedback.classList.add(correct ? "feedback-correct" : "feedback-wrong");
      });
      choices.append(button);
    });
    block.append(choices, feedback);
    result.append(block);
  });
}

function renderLearningPath(data) {
  result.replaceChildren();
  addText(result, "p", `${data.level} path for ${data.topic}`, "path-intro");
  data.steps.forEach((step, index) => {
    const block = document.createElement("article");
    block.className = "path-step";
    addText(block, "span", `STEP ${String(index + 1).padStart(2, "0")}`, "step-index");
    addText(block, "h3", step.stage);
    addText(block, "p", step.topics.join(" · "));
    addText(block, "p", `Estimated time: ${step.estimated_time}`, "step-time");
    addText(block, "p", `Resources: ${step.resources.join(" · ")}`, "step-time");
    result.append(block);
  });
  const tips = document.createElement("section");
  tips.className = "tips-block";
  addText(tips, "h3", "A few study habits to take along");
  const list = document.createElement("ul");
  data.study_tips.forEach((tip) => addText(list, "li", tip));
  tips.append(list);
  result.append(tips);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) {
    input.focus();
    return;
  }

  const endpoints = {
    qa: ["/qa", { question: text }],
    explain: ["/explain", { topic: text }],
    quiz: ["/quiz", { text }],
    summarize: ["/summarize", { text }],
    learn: ["/learn/recommendations", { topic: text, level: document.querySelector("#level").value }]
  };
  const [endpoint, body] = endpoints[task.value];
  runButton.disabled = true;
  copyButton.disabled = true;
  result.setAttribute("aria-busy", "true");
  result.replaceChildren();
  addText(result, "p", "Gathering a clearer picture…", "loading-message");
  serviceStatus.textContent = "Thinking through it";

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const responseText = await response.text();
    let data;
    try {
      data = responseText ? JSON.parse(responseText) : {};
    } catch {
      data = { detail: responseText || `Request failed with status ${response.status}.` };
    }
    if (!response.ok) throw new Error(data.detail || "The request could not be completed.");
    if (task.value === "quiz") renderQuiz(data);
    else if (task.value === "learn") renderLearningPath(data);
    else renderText(data.result);
    animateResult();
    serviceStatus.textContent = "Ready for your next question";
    copyButton.disabled = false;
  } catch (error) {
    result.replaceChildren();
    addText(result, "p", error.message || "Something went wrong. Please try again.", "error-message");
    serviceStatus.textContent = "Could not complete that request";
  } finally {
    runButton.disabled = false;
    result.setAttribute("aria-busy", "false");
  }
});

copyButton.addEventListener("click", async () => {
  await navigator.clipboard.writeText(result.innerText);
  copyButton.textContent = "Copied";
  window.setTimeout(() => { copyButton.textContent = "Copy"; }, 1200);
});