const expressionDisplay = document.getElementById("expressionDisplay");
const resultDisplay = document.getElementById("resultDisplay");
const modeToggle = document.getElementById("modeToggle");
const modeLabel = document.getElementById("modeLabel");
const historyList = document.getElementById("historyList");
const historyTemplate = document.getElementById("historyItemTemplate");

let expression = "";
let lastResult = 0;
let angleMode = "RAD";
let isEvaluating = false;

const functionMap = {
  RAD: {
    sin: "sin(",
    cos: "cos(",
    tan: "tan(",
    asin: "asin(",
    acos: "acos(",
    atan: "atan(",
  },
  DEG: {
    sin: "sin_deg(",
    cos: "cos_deg(",
    tan: "tan_deg(",
    asin: "asin_deg(",
    acos: "acos_deg(",
    atan: "atan_deg(",
  },
};

const neutralFunctions = {
  log: "log(",
  ln: "ln(",
  sqrt: "sqrt(",
  cbrt: "cbrt(",
  exp: "exp(",
  abs: "abs(",
  fact: "fact(",
  deg: "deg(",
  rad: "rad(",
};

function updateExpressionDisplay() {
  expressionDisplay.textContent = expression || " ";
}

function updateResultDisplay(value) {
  resultDisplay.textContent = value;
}

function appendValue(value) {
  expression += value;
  updateExpressionDisplay();
}

function appendFunction(fn) {
  if (functionMap[angleMode][fn]) {
    expression += functionMap[angleMode][fn];
  } else if (neutralFunctions[fn]) {
    expression += neutralFunctions[fn];
  }
  updateExpressionDisplay();
}

function clearExpression() {
  expression = "";
  updateExpressionDisplay();
  updateResultDisplay(0);
}

function deleteLast() {
  expression = expression.slice(0, -1);
  updateExpressionDisplay();
}

function toggleMode() {
  angleMode = angleMode === "RAD" ? "DEG" : "RAD";
  modeLabel.textContent = angleMode;
}

function addHistoryItem(expr, result) {
  const clone = historyTemplate.content.cloneNode(true);
  clone.querySelector(".history-expression").textContent = expr;
  clone.querySelector(".history-result").textContent = result;
  const item = clone.querySelector("li");
  item.addEventListener("click", () => {
    expression = expr;
    updateExpressionDisplay();
    updateResultDisplay(result);
  });
  historyList.prepend(clone);
  while (historyList.children.length > 10) {
    historyList.removeChild(historyList.lastChild);
  }
}

async function evaluateExpression() {
  if (!expression || isEvaluating) return;
  isEvaluating = true;
  updateResultDisplay("…");
  try {
    const response = await fetch("/api/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ expression }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Evaluation failed");
    }
    lastResult = data.result;
    const resultText = Number.isInteger(lastResult)
      ? lastResult.toString()
      : lastResult.toPrecision(12).replace(/\.?0+$/, "");
    updateResultDisplay(resultText);
    addHistoryItem(expression, resultText);
    expression = resultText;
    updateExpressionDisplay();
  } catch (error) {
    updateResultDisplay("Error");
  } finally {
    isEvaluating = false;
  }
}

function restoreLastAnswer() {
  appendValue(lastResult.toString());
}

document.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLButtonElement)) return;

  const { action, value, func } = target.dataset;
  if (action === "clear") {
    clearExpression();
  } else if (action === "delete") {
    deleteLast();
  } else if (action === "equals") {
    evaluateExpression();
  } else if (action === "ans") {
    restoreLastAnswer();
  } else if (value) {
    appendValue(value);
  } else if (func) {
    appendFunction(func);
  }
});

modeToggle.addEventListener("click", toggleMode);
modeToggle.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    toggleMode();
  }
});

updateExpressionDisplay();
