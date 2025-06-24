// frontend/script.js

// 重要：部署后需要将此URL替换为你的后端Worker的URL
const API_BASE_URL = 'https://backend.qu18354531302.workers.dev'; // 本地开发URL

// DOM元素
const loginView = document.getElementById('login-view');
const registerView = document.getElementById('register-view');
const dashboardView = document.getElementById('dashboard-view');
const errorMessage = document.getElementById('error-message');

// 表单
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');

// 切换视图链接
const showRegisterLink = document.getElementById('show-register');
const showLoginLink = document.getElementById('show-login');

// 仪表盘元素
const dashboardUsername = document.getElementById('dashboard-username');
const dashboardRole = document.getElementById('dashboard-role');
const logoutBtn = document.getElementById('logout-btn');

// 视图切换逻辑
showRegisterLink.addEventListener('click', (e) => {
    e.preventDefault();
    loginView.classList.add('hidden');
    registerView.classList.remove('hidden');
    errorMessage.textContent = '';
});

showLoginLink.addEventListener('click', (e) => {
    e.preventDefault();
    registerView.classList.add('hidden');
    loginView.classList.remove('hidden');
    errorMessage.textContent = '';
});

// 检查是否已登录
function checkLoginStatus() {
    const token = localStorage.getItem('authToken');
    const user = localStorage.getItem('user');
    if (token && user) {
        const userData = JSON.parse(user);
        showDashboard(userData);
    } else {
        showLogin();
    }
}

function showDashboard(user) {
    loginView.classList.add('hidden');
    registerView.classList.add('hidden');
    dashboardView.classList.remove('hidden');
    dashboardUsername.textContent = user.username;
    dashboardRole.textContent = user.role;
}

function showLogin() {
    loginView.classList.remove('hidden');
    registerView.classList.add('hidden');
    dashboardView.classList.add('hidden');
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
}

// 注册逻辑
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorMessage.textContent = '';
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;
    const inviteCode = document.getElementById('register-invitecode').value;

    const response = await fetch(`${API_BASE_URL}/api/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, inviteCode }),
    });

    const data = await response.json();

    if (response.ok) {
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        showDashboard(data.user);
    } else {
        errorMessage.textContent = `注册失败: ${data.error}`;
    }
});

// 登录逻辑
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorMessage.textContent = '';
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    const response = await fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
    });

    const data = await response.json();

    if (response.ok) {
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        showDashboard(data.user);
    } else {
        errorMessage.textContent = `登录失败: ${data.error}`;
    }
});

// 登出逻辑
logoutBtn.addEventListener('click', () => {
    showLogin();
});

// 页面加载时初始化
checkLoginStatus();