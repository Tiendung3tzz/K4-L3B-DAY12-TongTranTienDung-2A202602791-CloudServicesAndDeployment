const messageList = document.querySelector("#messageList");
const chatForm = document.querySelector("#chatForm");
const questionInput = document.querySelector("#question");
const sendButton = document.querySelector("#sendButton");
const serviceState = document.querySelector("#serviceState");
const serviceStateText = document.querySelector("#serviceStateText");
const settingsModal = document.querySelector("#settingsModal");
const settingsButton = document.querySelector("#settingsButton");
const closeSettingsButton = document.querySelector("#closeSettingsButton");
const saveSettingsButton = document.querySelector("#saveSettingsButton");
const clearSettingsButton = document.querySelector("#clearSettingsButton");
const apiKeyInput = document.querySelector("#apiKey");
const userIdInput = document.querySelector("#userId");

const STORAGE_KEYS = {
  apiKey: "day12-agent-api-key",
  userId: "day12-agent-user-id",
};

function loadSettings() {
  apiKeyInput.value = sessionStorage.getItem(STORAGE_KEYS.apiKey) || "";
  userIdInput.value = sessionStorage.getItem(STORAGE_KEYS.userId) || "web-user";
}

function setServiceState(state, text) {
  serviceState.classList.remove("online", "offline");
  if (state) serviceState.classList.add(state);
  serviceStateText.textContent = text;
}

function openSettings() {
  settingsModal.hidden = false;
  apiKeyInput.focus();
}

function closeSettings() {
  settingsModal.hidden = true;
}

function saveSettings() {
  if (apiKeyInput.value.trim()) {
    sessionStorage.setItem(STORAGE_KEYS.apiKey, apiKeyInput.value.trim());
  } else {
    sessionStorage.removeItem(STORAGE_KEYS.apiKey);
  }
  sessionStorage.setItem(STORAGE_KEYS.userId, userIdInput.value.trim() || "web-user");
  closeSettings();
  setServiceState("online", "Đã lưu cài đặt");
}

function clearSettings() {
  sessionStorage.removeItem(STORAGE_KEYS.apiKey);
  apiKeyInput.value = "";
  setServiceState("offline", "Thiếu API key");
}

function addMessage(text, role, extraClass = "") {
  const row = document.createElement("div");
  row.className = `message-row ${role}`;
  const bubble = document.createElement("div");
  bubble.className = `message ${extraClass}`.trim();
  bubble.textContent = text;
  row.appendChild(bubble);
  messageList.appendChild(row);
  messageList.scrollTop = messageList.scrollHeight;
  return row;
}

function addTypingMessage() {
  const row = document.createElement("div");
  row.className = "message-row assistant";
  row.innerHTML = '<div class="message"><span class="typing" aria-label="Đang trả lời"><span></span><span></span><span></span></span></div>';
  messageList.appendChild(row);
  messageList.scrollTop = messageList.scrollHeight;
  return row;
}

function getApiKey() {
  return sessionStorage.getItem(STORAGE_KEYS.apiKey) || "";
}

async function checkService() {
  try {
    const response = await fetch("/api/health");
    if (!response.ok) throw new Error("health check failed");
    setServiceState(getApiKey() ? "online" : "offline", getApiKey() ? "Online" : "Thiếu API key");
  } catch {
    setServiceState("offline", "Backend không phản hồi");
  }
}

async function sendQuestion(question) {
  const apiKey = getApiKey();
  if (!apiKey) {
    openSettings();
    setServiceState("offline", "Thiếu API key");
    return;
  }

  const userId = sessionStorage.getItem(STORAGE_KEYS.userId) || "web-user";
  addMessage(question, "user");
  questionInput.value = "";
  questionInput.style.height = "auto";
  sendButton.disabled = true;
  const typingRow = addTypingMessage();

  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
        "X-User-Id": userId,
      },
      body: JSON.stringify({ question }),
    });

    const raw = await response.text();
    let data;
    try {
      data = JSON.parse(raw);
    } catch {
      data = { detail: raw || "Backend trả về phản hồi không hợp lệ." };
    }

    if (!response.ok) {
      const detail = data.detail || `Request thất bại (${response.status})`;
      throw new Error(`${response.status}: ${detail}`);
    }

    typingRow.remove();
    addMessage(data.answer, "assistant");
    setServiceState("online", "Online");
  } catch (error) {
    typingRow.remove();
    addMessage(error.message || "Không thể kết nối tới backend.", "assistant", "error");
    setServiceState("offline", "Có lỗi kết nối");
  } finally {
    sendButton.disabled = false;
    questionInput.focus();
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (question) sendQuestion(question);
});

questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

questionInput.addEventListener("input", () => {
  questionInput.style.height = "auto";
  questionInput.style.height = `${Math.min(questionInput.scrollHeight, 130)}px`;
});

document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.textContent;
    questionInput.dispatchEvent(new Event("input"));
    questionInput.focus();
  });
});

settingsButton.addEventListener("click", openSettings);
closeSettingsButton.addEventListener("click", closeSettings);
saveSettingsButton.addEventListener("click", saveSettings);
clearSettingsButton.addEventListener("click", clearSettings);
settingsModal.addEventListener("click", (event) => {
  if (event.target === settingsModal) closeSettings();
});

loadSettings();
checkService();
