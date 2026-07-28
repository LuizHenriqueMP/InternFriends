const API_BASE_URL = "/api";
const TOKEN_KEY = "access_token";

const elements = {};

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function setMessage(element, message, isError = false) {
  if (!element) return;
  element.textContent = message || "";
  element.classList.toggle("error", Boolean(message) && isError);
  element.classList.toggle("success", Boolean(message) && !isError);
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(data.message || `Erro na requisição (${response.status})`);
    error.status = response.status;
    throw error;
  }

  return data;
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString("pt-BR");
}

function updateAuthState() {
  const loggedIn = Boolean(getToken());

  elements.authSection.hidden = loggedIn;
  elements.commentSection.hidden = !loggedIn;
  elements.commentsSection.hidden = !loggedIn;
  elements.logoutButton.hidden = !loggedIn;
  elements.currentUser.hidden = !loggedIn;
  elements.adminButton.hidden = true;

  if (!loggedIn) {
    elements.comments.innerHTML = "";
    elements.currentUser.textContent = "";
  }
}

async function loadSessionUser() {
  if (!getToken()) return;

  try {
    const user = await api("/auth/me", { method: "GET" });
    elements.currentUser.textContent = user.email || "Conta ativa";
    elements.currentUser.hidden = false;
    elements.adminButton.hidden = !user.is_admin;
  } catch (error) {
    if (error.status === 401 || error.status === 422) {
      clearToken();
      updateAuthState();
      setMessage(elements.authMessage, "Sua sessão expirou. Entre novamente.", true);
    }
  }
}

async function registerUser() {
  const email = elements.email.value.trim();
  const password = elements.password.value;

  if (!email || !password) {
    setMessage(elements.authMessage, "Informe o e-mail e a senha.", true);
    return;
  }

  try {
    elements.registerButton.disabled = true;
    const data = await api("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setMessage(elements.authMessage, data.message);
  } catch (error) {
    setMessage(elements.authMessage, error.message, true);
  } finally {
    elements.registerButton.disabled = false;
  }
}

async function loginUser() {
  const email = elements.email.value.trim();
  const password = elements.password.value;

  if (!email || !password) {
    setMessage(elements.authMessage, "Informe o e-mail e a senha.", true);
    return;
  }

  try {
    elements.loginButton.disabled = true;
    const data = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    setToken(data.access_token);
    elements.password.value = "";
    setMessage(elements.authMessage, "");
    updateAuthState();
    await loadSessionUser();
    await loadComments();
  } catch (error) {
    setMessage(elements.authMessage, error.message, true);
  } finally {
    elements.loginButton.disabled = false;
  }
}

function logoutUser() {
  clearToken();
  updateAuthState();
  setMessage(elements.authMessage, "Você saiu da conta.");
}

async function resendVerification() {
  const email = elements.email.value.trim();

  if (!email) {
    setMessage(elements.authMessage, "Informe o e-mail cadastrado.", true);
    return;
  }

  try {
    elements.resendVerificationButton.disabled = true;
    const data = await api("/auth/resend-verification", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
    setMessage(elements.authMessage, data.message);
  } catch (error) {
    setMessage(elements.authMessage, error.message, true);
  } finally {
    elements.resendVerificationButton.disabled = false;
  }
}

async function publishComment() {
  const content = elements.content.value.trim();

  if (!getToken()) {
    setMessage(elements.commentMessage, "Faça login antes de comentar.", true);
    return;
  }

  if (!content) {
    setMessage(elements.commentMessage, "Digite um comentário antes de publicar.", true);
    return;
  }

  try {
    elements.publishButton.disabled = true;
    elements.publishButton.textContent = "Publicando...";

    const data = await api("/comments", {
      method: "POST",
      body: JSON.stringify({ content }),
    });

    elements.content.value = "";
    setMessage(elements.commentMessage, data.message);
    await loadComments();
  } catch (error) {
    if (error.status === 401 || error.status === 422) {
      clearToken();
      updateAuthState();
    }
    setMessage(elements.commentMessage, error.message, true);
  } finally {
    elements.publishButton.disabled = false;
    elements.publishButton.textContent = "Publicar";
  }
}

async function voteComment(commentId, value) {
  try {
    await api(`/comments/${commentId}/vote`, {
      method: "PUT",
      body: JSON.stringify({ value }),
    });
    await loadComments();
  } catch (error) {
    setMessage(elements.commentsMessage, error.message, true);
  }
}

async function removeVote(commentId) {
  try {
    await api(`/comments/${commentId}/vote`, { method: "DELETE" });
    await loadComments();
  } catch (error) {
    setMessage(elements.commentsMessage, error.message, true);
  }
}

async function deleteComment(commentId) {
  if (!window.confirm("Deseja excluir este comentário?")) return;

  try {
    const data = await api(`/comments/${commentId}`, { method: "DELETE" });
    setMessage(elements.commentsMessage, data.message);
    await loadComments();
  } catch (error) {
    setMessage(elements.commentsMessage, error.message, true);
  }
}

function renderComments(comments) {
  if (!comments.length) {
    elements.comments.innerHTML = "<p>Ainda não há comentários.</p>";
    return;
  }

  elements.comments.innerHTML = comments.map((item) => {
    const likeActive = item.my_vote === 1;
    const dislikeActive = item.my_vote === -1;
    const author = item.author_email
      ? `<div class="admin-author">Autor: ${escapeHtml(item.author_email)}</div>`
      : "";
    const deleteButton = item.can_delete
      ? `<button type="button" data-action="delete" data-comment-id="${item.id}">Excluir</button>`
      : "";

    return `
      <article class="comment">
        <p>${escapeHtml(item.content)}</p>
        <div class="meta">${escapeHtml(formatDate(item.created_at))}</div>
        ${author}
        <div class="comment-actions">
          <button type="button" data-action="${likeActive ? "remove-vote" : "like"}" data-comment-id="${item.id}" class="${likeActive ? "active" : ""}">👍 ${item.likes}</button>
          <button type="button" data-action="${dislikeActive ? "remove-vote" : "dislike"}" data-comment-id="${item.id}" class="${dislikeActive ? "active" : ""}">👎 ${item.dislikes}</button>
          ${deleteButton}
        </div>
      </article>
    `;
  }).join("");
}

async function loadComments() {
  if (!getToken()) return;

  setMessage(elements.commentsMessage, "Carregando comentários...");

  try {
    const data = await api("/comments", { method: "GET" });
    setMessage(elements.commentsMessage, "");
    renderComments(data.comments || []);
  } catch (error) {
    elements.comments.innerHTML = "";
    setMessage(elements.commentsMessage, error.message, true);
  }
}

async function requestPasswordReset() {
  const email = elements.email.value.trim();

  if (!email) {
    setMessage(elements.authMessage, "Informe o e-mail da conta.", true);
    return;
  }

  try {
    const data = await api("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
    setMessage(elements.authMessage, data.message);
  } catch (error) {
    setMessage(elements.authMessage, error.message, true);
  }
}

async function resetPassword() {
  const resetToken = new URLSearchParams(window.location.search).get("token") || "";
  const password = elements.newPassword.value;

  if (!password) {
    setMessage(elements.resetMessage, "Informe a nova senha.", true);
    return;
  }

  try {
    elements.resetPasswordButton.disabled = true;
    const data = await api("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token: resetToken, password }),
    });
    setMessage(elements.resetMessage, data.message);
  } catch (error) {
    setMessage(elements.resetMessage, error.message, true);
  } finally {
    elements.resetPasswordButton.disabled = false;
  }
}

async function handleCommentAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;

  const commentId = Number(button.dataset.commentId);
  const action = button.dataset.action;
  if (!commentId) return;

  button.disabled = true;
  try {
    if (action === "like") await voteComment(commentId, 1);
    if (action === "dislike") await voteComment(commentId, -1);
    if (action === "remove-vote") await removeVote(commentId);
    if (action === "delete") await deleteComment(commentId);
  } finally {
    button.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  Object.assign(elements, {
    authSection: document.getElementById("authSection"),
    email: document.getElementById("email"),
    password: document.getElementById("password"),
    authMessage: document.getElementById("authMessage"),
    loginButton: document.getElementById("loginButton"),
    registerButton: document.getElementById("registerButton"),
    resendVerificationButton: document.getElementById("resendVerificationButton"),
    forgotPasswordButton: document.getElementById("forgotPasswordButton"),
    logoutButton: document.getElementById("logoutButton"),
    adminButton: document.getElementById("adminButton"),
    currentUser: document.getElementById("currentUser"),
    commentSection: document.getElementById("commentSection"),
    commentsSection: document.getElementById("commentsSection"),
    content: document.getElementById("content"),
    publishButton: document.getElementById("publishButton"),
    commentMessage: document.getElementById("commentMessage"),
    comments: document.getElementById("comments"),
    commentsMessage: document.getElementById("commentsMessage"),
    reloadCommentsButton: document.getElementById("reloadCommentsButton"),
    resetSection: document.getElementById("resetSection"),
    newPassword: document.getElementById("newPassword"),
    resetPasswordButton: document.getElementById("resetPasswordButton"),
    resetMessage: document.getElementById("resetMessage"),
  });

  elements.registerButton.addEventListener("click", registerUser);
  elements.loginButton.addEventListener("click", loginUser);
  elements.logoutButton.addEventListener("click", logoutUser);
  elements.resendVerificationButton.addEventListener("click", resendVerification);
  elements.forgotPasswordButton.addEventListener("click", requestPasswordReset);
  elements.publishButton.addEventListener("click", publishComment);
  elements.reloadCommentsButton.addEventListener("click", loadComments);
  elements.resetPasswordButton.addEventListener("click", resetPassword);
  elements.comments.addEventListener("click", handleCommentAction);

  const isResetPage = window.location.pathname === "/reset-password";
  elements.resetSection.hidden = !isResetPage;
  elements.authSection.hidden = isResetPage;
  elements.commentSection.hidden = true;
  elements.commentsSection.hidden = true;

  if (isResetPage) return;

  updateAuthState();

  if (getToken()) {
    await loadSessionUser();
    await loadComments();
  }
});
