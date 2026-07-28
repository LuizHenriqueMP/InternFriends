const API_BASE_URL = "/api";

function token() {
    return localStorage.getItem("access_token");
}

function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
}

function showMessage(message, error = false) {
    const element = document.getElementById("admin-message");
    element.textContent = message || "";
    element.classList.toggle("error", error);
    element.classList.toggle("success", Boolean(message) && !error);
}

async function request(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token()}`,
            ...(options.headers || {})
        }
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.message || `Erro HTTP ${response.status}`);
    }
    return data;
}

async function verifyAdmin() {
    if (!token()) {
        window.location.href = "/";
        return false;
    }
    try {
        const data = await request("/auth/me");
        if (!data.is_admin) {
            showMessage("Esta conta não possui acesso administrativo.", true);
            return false;
        }
        document.getElementById("admin-email").textContent = data.email;
        return true;
    } catch (error) {
        localStorage.removeItem("access_token");
        window.location.href = "/";
        return false;
    }
}

function formatDate(value) {
    if (!value) return "";
    return new Intl.DateTimeFormat("pt-BR", {
        dateStyle: "short",
        timeStyle: "short"
    }).format(new Date(value));
}

async function loadUsers() {
    const container = document.getElementById("admin-users");
    container.innerHTML = "<p>Carregando...</p>";
    try {
        const data = await request("/admin/users");
        container.innerHTML = data.users.map((user) => `
            <article class="admin-item">
                <div class="admin-item-content">
                    <strong>${escapeHtml(user.email || "Conta anonimizada")}</strong>
                    <span>Status: ${escapeHtml(user.status)}</span>
                    <span>Criado em: ${escapeHtml(formatDate(user.created_at))}</span>
                    ${user.is_admin ? "<span class=\"admin-badge\">Administrador</span>" : ""}
                </div>
                <div class="admin-actions">
                    ${user.status !== "active" ? `
                        <button type="button" data-user-action="activate" data-user-id="${user.id}">
                            Liberar acesso
                        </button>
                    ` : `
                        <button type="button" data-user-action="block" data-user-id="${user.id}" ${user.is_admin ? "disabled" : ""}>
                            Bloquear acesso
                        </button>
                    `}
                </div>
            </article>
        `).join("") || "<p>Nenhum usuário encontrado.</p>";
    } catch (error) {
        container.innerHTML = "";
        showMessage(error.message, true);
    }
}

async function loadComments() {
    const container = document.getElementById("admin-comments");
    container.innerHTML = "<p>Carregando...</p>";
    try {
        const data = await request("/admin/comments");
        container.innerHTML = data.comments.map((comment) => `
            <article class="admin-item admin-comment-item">
                <div class="admin-item-content">
                    <strong>${escapeHtml(comment.author_email || "E-mail indisponível")}</strong>
                    <p>${escapeHtml(comment.content)}</p>
                    <span>${escapeHtml(formatDate(comment.created_at))}</span>
                </div>
                <div class="admin-actions">
                    <button class="danger-button" type="button" data-comment-id="${comment.id}">
                        Excluir comentário
                    </button>
                </div>
            </article>
        `).join("") || "<p>Nenhum comentário encontrado.</p>";
    } catch (error) {
        container.innerHTML = "";
        showMessage(error.message, true);
    }
}

async function handleUsers(event) {
    const button = event.target.closest("button[data-user-action]");
    if (!button) return;
    button.disabled = true;
    try {
        const action = button.dataset.userAction;
        const userId = button.dataset.userId;
        const data = await request(`/admin/users/${userId}/${action}`, { method: "PUT" });
        showMessage(data.message);
        await loadUsers();
    } catch (error) {
        showMessage(error.message, true);
        button.disabled = false;
    }
}

async function handleComments(event) {
    const button = event.target.closest("button[data-comment-id]");
    if (!button) return;
    if (!window.confirm("Excluir este comentário?")) return;
    button.disabled = true;
    try {
        const data = await request(`/admin/comments/${button.dataset.commentId}`, { method: "DELETE" });
        showMessage(data.message);
        await loadComments();
    } catch (error) {
        showMessage(error.message, true);
        button.disabled = false;
    }
}

async function initialize() {
    const valid = await verifyAdmin();
    if (!valid) return;
    document.getElementById("admin-users").addEventListener("click", handleUsers);
    document.getElementById("admin-comments").addEventListener("click", handleComments);
    document.getElementById("reload-users-button").addEventListener("click", loadUsers);
    document.getElementById("reload-admin-comments-button").addEventListener("click", loadComments);
    document.getElementById("admin-logout-button").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        window.location.href = "/";
    });
    await Promise.all([loadUsers(), loadComments()]);
}

document.addEventListener("DOMContentLoaded", initialize);
