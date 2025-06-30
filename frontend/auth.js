// API基础URL，根据实际部署环境修改
const AUTH_API_BASE_URL = 'https://my-auth-worker.qu18354531302.workers.dev';

// 开发模式：跳过认证（用于测试）
const DEVELOPMENT_MODE = false;

// 切换登录/注册选项卡
function switchAuthTab(tab) {
    const loginTab = document.querySelector('.auth-tab:nth-child(1)');
    const registerTab = document.querySelector('.auth-tab:nth-child(2)');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('register-form');
    
    if (tab === 'login') {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        loginForm.classList.add('active');
        registerForm.classList.remove('active');
    } else {
        loginTab.classList.remove('active');
        registerTab.classList.add('active');
        loginForm.classList.remove('active');
        registerForm.classList.add('active');
    }
}

// 显示错误信息
function showError(inputId, errorId, isError, message = null) {
    const input = document.getElementById(inputId);
    const errorElement = document.getElementById(errorId);
    
    if (isError) {
        input.classList.add('error');
        errorElement.classList.add('show');
        if (message) {
            errorElement.textContent = message;
        }
    } else {
        input.classList.remove('error');
        errorElement.classList.remove('show');
    }
}

// 显示全局消息提示
function showMessage(message, type = 'error') {
    alert(message); // 简单实现，可以改为更友好的UI提示
}

// 保存token和用户信息到本地存储
function saveAuthData(token, user) {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
}

// 清除本地存储中的认证数据
function clearAuthData() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
}

// 获取本地存储的token
function getToken() {
    return localStorage.getItem('token');
}

// 获取本地存储的用户信息
function getUser() {
    const userJson = localStorage.getItem('user');
    return userJson ? JSON.parse(userJson) : null;
}



// 处理登录表单提交
async function handleLoginSubmit(event) {
    event.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    let isValid = true;
    
    // 验证用户名
    if (!username) {
        showError('loginUsername', 'loginUsernameError', true);
        isValid = false;
    } else {
        showError('loginUsername', 'loginUsernameError', false);
    }
    
    // 验证密码
    if (!password) {
        showError('loginPassword', 'loginPasswordError', true);
        isValid = false;
    } else {
        showError('loginPassword', 'loginPasswordError', false);
    }
    
    if (isValid) {
        try {
            const response = await fetch(`${AUTH_API_BASE_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // 登录成功，保存token和用户信息
                saveAuthData(result.token, result.user);
                
                // 设置用户信息显示
                document.getElementById('userAvatar').textContent = result.user.avatar;
                document.getElementById('userInfo').textContent = result.user.username;
                
                // 显示主内容
                document.getElementById('authOverlay').style.display = 'none';
                document.getElementById('mainContent').classList.remove('blurred');
                document.getElementById('userBar').classList.add('show');
                
                // 加载所有数据（摘要 + 图表）
                console.log('🔄 Login successful, loading data...');
                setTimeout(async () => {
                    if (typeof window.loadAllData === 'function') {
                        console.log('📊 Calling loadAllData...');
                        await window.loadAllData();
                    } else if (typeof window.loadSummaryData === 'function') {
                        console.log('📊 Calling loadSummaryData...');
                        await window.loadSummaryData();
                    } else {
                        console.warn('⚠️ No data loading functions available');
                    }
                }, 100);
            } else {
                // 登录失败，显示错误信息
                showMessage(result.message || '用户名或密码错误');
            }
        } catch (error) {
            showMessage('登录请求失败，请稍后重试');
        }
    }
}

// 处理注册表单提交
async function handleRegisterSubmit(event) {
    event.preventDefault();
    
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const inviteCode = document.getElementById('inviteCode').value;
    let isValid = true;
    
    // 验证用户名
    if (username.length < 3 || username.length > 20) {
        showError('registerUsername', 'registerUsernameError', true);
        isValid = false;
    } else {
        showError('registerUsername', 'registerUsernameError', false);
    }
    
    // 验证密码
    if (password.length < 6) {
        showError('registerPassword', 'registerPasswordError', true);
        isValid = false;
    } else {
        showError('registerPassword', 'registerPasswordError', false);
    }
    
    // 验证确认密码
    if (password !== confirmPassword) {
        showError('confirmPassword', 'confirmPasswordError', true);
        isValid = false;
    } else {
        showError('confirmPassword', 'confirmPasswordError', false);
    }
    
    // 验证邀请码
    if (!inviteCode) {
        showError('inviteCode', 'inviteCodeError', true, '请输入邀请码');
        isValid = false;
    } else {
        showError('inviteCode', 'inviteCodeError', false);
    }
    
    if (isValid) {
        try {
            const response = await fetch(`${AUTH_API_BASE_URL}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password, inviteCode })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // 注册成功，保存token和用户信息
                saveAuthData(result.token, result.user);
                
                // 设置用户信息显示
                document.getElementById('userAvatar').textContent = result.user.avatar;
                document.getElementById('userInfo').textContent = result.user.username;
                
                // 显示主内容
                document.getElementById('authOverlay').style.display = 'none';
                document.getElementById('mainContent').classList.remove('blurred');
                document.getElementById('userBar').classList.add('show');
                
                showMessage('注册成功！', 'success');
                
                // 加载所有数据（摘要 + 图表）
                console.log('🔄 Registration successful, loading data...');
                setTimeout(async () => {
                    if (typeof window.loadAllData === 'function') {
                        console.log('📊 Calling loadAllData...');
                        await window.loadAllData();
                    } else if (typeof window.loadSummaryData === 'function') {
                        console.log('📊 Calling loadSummaryData...');
                        await window.loadSummaryData();
                    } else {
                        console.warn('⚠️ No data loading functions available');
                    }
                }, 100);
            } else {
                // 注册失败，显示错误信息
                showMessage(result.message);
                
                // 特定错误处理
                if (result.message && result.message.includes('邀请码')) {
                    showError('inviteCode', 'inviteCodeError', true, result.message);
                }
            }
        } catch (error) {
            showMessage('注册请求失败，请稍后重试');
        }
    }
}

// 退出登录
function logout() {
    clearAuthData();
    document.getElementById('authOverlay').style.display = 'flex';
    document.getElementById('mainContent').classList.add('blurred');
    document.getElementById('userBar').classList.remove('show');
    
    // 重置表单
    document.getElementById('loginForm').reset();
    document.getElementById('register-form').reset();
    switchAuthTab('login');
}

// 检查用户是否已登录
function checkUserAuth() {
    const token = getToken();
    const user = getUser();
    
    if (token && user) {
        // 用户已登录
        document.getElementById('userAvatar').textContent = user.avatar || user.username.charAt(0).toUpperCase();
        document.getElementById('userInfo').textContent = user.username;
        return true;
    }
    
    return false;
}

// 切换内容标签
function showTab(tabId) {
    console.log(`🔄 Switching to tab: ${tabId}`);

    const tabs = document.querySelectorAll('.tab-content');
    const navTabs = document.querySelectorAll('.nav-tab');

    tabs.forEach(tab => tab.classList.remove('active'));
    navTabs.forEach(tab => tab.classList.remove('active'));

    const targetTab = document.getElementById(tabId);
    const targetNavTab = document.querySelector(`.nav-tab[onclick="showTab('${tabId}')"]`);

    if (targetTab) {
        targetTab.classList.add('active');
    }
    if (targetNavTab) {
        targetNavTab.classList.add('active');
    }

    // 根据标签页加载相应数据
    if (tabId === 'realtime') {
        console.log('📊 Realtime tab activated, initializing charts...');
        // 重新初始化图表并加载数据
        setTimeout(async () => {
            if (typeof window.initializeCharts === 'function') {
                const success = window.initializeCharts();
                if (success) {
                    console.log('✅ Charts reinitialized for realtime tab');
                    // Load data using the global function
                    if (typeof window.loadAllData === 'function') {
                        await window.loadAllData();
                    } else if (typeof window.loadData === 'function') {
                        await window.loadData();
                    }
                }
            }
        }, 150);
    }
}

function initializeAuth() {
    // 开发模式：直接跳过认证
    if (DEVELOPMENT_MODE) {
        console.log('🚀 Development mode: bypassing authentication...');
        autoLoginDemo();
        return;
    }

    // 添加表单提交事件监听
    document.getElementById('register-form').addEventListener('submit', handleRegisterSubmit);
    document.getElementById('loginForm').addEventListener('submit', handleLoginSubmit);

    // 检查用户是否已登录
    const isLoggedIn = checkUserAuth();
    if (isLoggedIn) {
        // 用户已登录，显示主内容
        document.getElementById('authOverlay').style.display = 'none';
        document.getElementById('mainContent').classList.remove('blurred');
        document.getElementById('userBar').classList.add('show');

        // 加载所有数据（摘要 + 图表）
        console.log('🔄 User already logged in, loading data...');
        setTimeout(async () => {
            if (typeof window.loadAllData === 'function') {
                console.log('📊 Calling loadAllData...');
                await window.loadAllData();
            } else if (typeof window.loadSummaryData === 'function') {
                console.log('📊 Calling loadSummaryData...');
                await window.loadSummaryData();
            } else {
                console.warn('⚠️ No data loading functions available');
            }
        }, 100);
    } else {
        // 用户未登录，显示登录界面
        document.getElementById('authOverlay').style.display = 'flex';
        document.getElementById('mainContent').classList.add('blurred');
        document.getElementById('userBar').classList.remove('show');
    }
}



// 页面加载完成后初始化认证系统
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔐 Initializing authentication system...');
    initializeAuth();
});
