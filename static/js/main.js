const API_BASE = '/api';
let currentToken = localStorage.getItem('token') || '';
let currentMaterial = null;
let capturedImageBlob = null;
let currentStream = null;

let lastScrollY = 0;

// 页面加载时自动登录并等待完成
const loginPromise = !currentToken ? (async () => {
    const formData = new FormData();
    formData.append('username', 'admin');
    formData.append('password', 'admin123');
    const res = await fetch(`${API_BASE}/auth/token`, { method: 'POST', body: formData });
    const data = await res.json();
    currentToken = data.access_token;
    localStorage.setItem('token', currentToken);
})() : Promise.resolve();

async function ensureLogin() {
    await loginPromise;
    if (!currentToken) {
        await login();
    }
}

function saveScrollPosition() {
    lastScrollY = window.scrollY;
}

function restoreScrollPosition() {
    window.scrollTo(0, lastScrollY);
}

function formatPrice(value) {
    if (value === null || value === undefined || value === '无') {
        return '无';
    }
    const num = parseFloat(value);
    if (isNaN(num)) {
        return value;
    }
    return num.toFixed(1);
}

async function login(username = 'admin', password = 'admin123') {
    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            currentToken = data.access_token;
            localStorage.setItem('token', currentToken);
            document.getElementById('currentUser').textContent = username;
            return true;
        }
        return false;
    } catch (error) {
        console.error('登录失败:', error);
        return false;
    }
}

async function apiRequest(endpoint, options = {}) {
    // 确保已登录
    await ensureLogin();

    const headers = {
        'Authorization': `Bearer ${currentToken}`,
        ...options.headers
    };

    if (options.body && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });

        if (response.status === 401) {
            await login();
            return apiRequest(endpoint, options);
        }

        return response;
    } catch (error) {
        console.error('请求失败:', error);
        throw error;
    }
}

let searchTimeout = null;
let hideInventoried = document.getElementById('hideInventoried')?.checked ?? true;

function onHideInventoriedChange() {
    hideInventoried = document.getElementById('hideInventoried').checked;
    const keyword = document.getElementById('searchInput').value.trim();
    if (keyword) {
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        searchTimeout = setTimeout(() => {
            getSuggestions(keyword);
        }, 100);
    }
}

async function getSuggestions(keyword) {
    if (!keyword || keyword.length < 1) {
        hideSuggestions();
        return;
    }
    
    try {
        const params = new URLSearchParams({
            keyword: keyword,
            limit: 20,
            hide_inventoried: hideInventoried
        });
        const response = await fetch(`${API_BASE}/materials/suggestions?${params}`);
        if (!response.ok) throw new Error('获取建议失败');
        
        const suggestions = await response.json();
        displaySuggestions(suggestions);
    } catch (error) {
        console.error('获取搜索建议失败:', error);
        hideSuggestions();
    }
}

function displaySuggestions(suggestions) {
    const box = document.getElementById('suggestionsBox');
    if (!suggestions || suggestions.length === 0) {
        hideSuggestions();
        return;
    }
    
    box.innerHTML = suggestions.map((s, index) => {
        const highlightCode = highlightMatch(s.code, document.getElementById('searchInput').value);
        const highlightName = highlightMatch(s.name, document.getElementById('searchInput').value);
        const highlightSpec = highlightMatch(s.spec, document.getElementById('searchInput').value);
        const inventoryClass = s.has_inventory ? 'inventoried' : 'not-inventoried';
        const inventoryBadge = s.has_inventory ? '<span class="inventory-badge">已盘库</span>' : '';
        
        return `
            <div class="suggestion-item ${inventoryClass}" data-code="${s.code}" onclick="selectFromSuggestion('${s.code}')">
                <div class="suggestion-main">
                    <span class="suggestion-code">${highlightCode}</span>
                    <span class="suggestion-name">${highlightName}</span>
                    ${inventoryBadge}
                </div>
                ${s.spec ? `<div class="suggestion-spec">${highlightSpec}</div>` : ''}
            </div>
        `;
    }).join('');
    
    box.classList.remove('hidden');
}

function highlightMatch(text, keyword) {
    if (!text || !keyword) return text;
    
    const keywords = keyword.split();
    let result = text;
    
    keywords.forEach(kw => {
        if (kw.trim()) {
            const regex = new RegExp(`(${kw})`, 'gi');
            result = result.replace(regex, '<em>$1</em>');
        }
    });
    
    return result;
}

function hideSuggestions() {
    const box = document.getElementById('suggestionsBox');
    if (box) {
        box.classList.add('hidden');
        box.innerHTML = '';
    }
    
    const footer = document.querySelector('footer');
    if (footer) {
        footer.style.marginTop = '0';
    }
}

function selectFromSuggestion(code) {
    document.getElementById('searchInput').value = code;
    hideSuggestions();
    selectMaterial(code);
}

document.addEventListener('DOMContentLoaded', async function() {
    // 检查 URL 参数是否有 material_code
    const urlParams = new URLSearchParams(window.location.search);
    const materialCode = urlParams.get('material_code');
    if (materialCode) {
        await ensureLogin();
        await selectMaterial(materialCode);
    }

    const searchInput = document.getElementById('searchInput');

    searchInput.addEventListener('input', function(e) {
        const keyword = e.target.value.trim();
        
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        
        if (keyword.length === 0) {
            hideSuggestions();
            return;
        }
        
        searchTimeout = setTimeout(() => {
            getSuggestions(keyword);
        }, 300);
    });
    
    searchInput.addEventListener('focus', function() {
        const keyword = this.value.trim();
        if (keyword.length > 0) {
            getSuggestions(keyword);
        }
    });
    
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-wrapper')) {
            hideSuggestions();
        }
    });
    
    window.addEventListener('resize', function() {
    });
    
    window.addEventListener('scroll', function() {
    });
    
    searchInput.addEventListener('keydown', function(e) {
        const box = document.getElementById('suggestionsBox');
        const items = box.querySelectorAll('.suggestion-item');
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const current = box.querySelector('.suggestion-item:hover');
            let next;
            if (current) {
                next = current.nextElementSibling;
                if (!next) next = items[0];
                current.classList.remove('hovered');
            } else {
                next = items[0];
            }
            if (next) {
                next.classList.add('hovered');
                next.scrollIntoView({ block: 'nearest' });
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            const current = box.querySelector('.suggestion-item:hover');
            let prev;
            if (current) {
                prev = current.previousElementSibling;
                if (!prev) prev = items[items.length - 1];
                current.classList.remove('hovered');
            } else {
                prev = items[items.length - 1];
            }
            if (prev) {
                prev.classList.add('hovered');
                prev.scrollIntoView({ block: 'nearest' });
            }
        } else if (e.key === 'Enter') {
            const hovered = box.querySelector('.suggestion-item.hovered');
            if (hovered) {
                e.preventDefault();
                const code = hovered.dataset.code;
                selectFromSuggestion(code);
            } else {
                searchMaterials();
            }
        } else if (e.key === 'Escape') {
            hideSuggestions();
        }
    });
});

async function searchMaterials() {
    const keyword = document.getElementById('searchInput').value.trim();
    if (!keyword) return;
    
    hideSuggestions();
    
    const listEl = document.getElementById('materialList');
    listEl.innerHTML = '<div class="loading">搜索中...</div>';
    listEl.classList.remove('hidden');
    
    try {
        const response = await apiRequest(`/materials/?keyword=${encodeURIComponent(keyword)}&limit=50`);
        const materials = await response.json();
        
        if (materials.length === 0) {
            listEl.innerHTML = '<div class="message error">未找到匹配的物料</div>';
            return;
        }
        
        listEl.innerHTML = materials.map(m => `
            <div class="material-item" onclick="selectMaterial('${m.code}')">
                <strong>[${m.code}]</strong> ${m.name || '无名称'} | ${m.spec || '无规格'}
            </div>
        `).join('');
    } catch (error) {
        listEl.innerHTML = '<div class="message error">搜索失败</div>';
    }
}

async function selectMaterial(code, evt) {
    try {
        const response = await apiRequest(`/materials/${code}`);
        const data = await response.json();
        currentMaterial = data;

        document.querySelectorAll('.material-item').forEach(el => el.classList.remove('selected'));
        if (evt && evt.target) {
            evt.target.closest('.material-item').classList.add('selected');
        }

        showMaterialDetail(data);
    } catch (error) {
        showMessage('获取物料详情失败', 'error');
    }
}

function showMaterialDetail(m) {
    const detailEl = document.getElementById('materialDetail');
    
    detailEl.innerHTML = `
        <h2 class="section-title">📦 物料基本信息</h2>
        <div class="material-info-card">
            <div class="info-main">
                <div class="info-row">
                    <span class="info-label">编码：</span>
                    <span class="info-value code">${m.code}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">名称：</span>
                    <span class="info-value">${m.name || '无'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">规格：</span>
                    <span class="info-value">${m.spec || '无'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">型号：</span>
                    <span class="info-value">${m.model || '无'}</span>
                </div>
            </div>
            <div class="info-divider"></div>
            <div class="info-extra">
                <div class="info-row">
                    <span class="info-label">单位：</span>
                    <span class="info-value">${m.unit || '无'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">数量：</span>
                    <span class="info-value highlight">${m.quantity || '无'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">单价：</span>
                    <span class="info-value">${formatPrice(m.unit_price)}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">总金额：</span>
                    <span class="info-value highlight">${formatPrice(m.total_amount)}</span>
                </div>
            </div>
        </div>
        
        <div class="inventory-section">
            <h2 class="section-title">📋 盘库状态</h2>
            <div class="status-badges">
                <span class="status-badge">当前评分：<strong>${getScoreLabel(m.inventory_records?.[0]?.score)}</strong></span>
                <span class="status-badge">已上传照片：<strong>${m.photos?.length || 0}/10 张</strong></span>
            </div>
            
            <h2 class="section-title">🔧 盘库操作</h2>
            
            <div class="score-section">
                <h3>状态评分</h3>
                <div class="score-slider">
                    ${[1,2,3,4,5].map(s => `
                        <button class="score-btn ${m.inventory_records?.[0]?.score === s ? 'active' : ''}" 
                                onclick="setScore(${s})">${s}分</button>
                    `).join('')}
                </div>
                <div class="score-labels">
                    <span>1分: 建议报废</span>
                    <span>3分: 外观性能尚可</span>
                    <span>5分: 全新可使用</span>
                </div>
                <button class="btn ${m.inventory_records?.[0]?.score ? 'btn-warning' : 'btn-primary'}" 
                        onclick="${m.inventory_records?.[0]?.score ? 'submitScoreWithConfirm' : 'submitScore'}()">
                    💾 ${m.inventory_records?.[0]?.score ? '修改评分' : '提交评分'}
                </button>
            </div>
            
            <div class="photo-section">
                <h3>📷 现场拍照</h3>
                <div class="camera-container">
                    <video id="cameraVideo" autoplay playsinline style="display: none;"></video>
                    <canvas id="cameraCanvas" style="display: none;"></canvas>
                    <img id="photoPreview" style="display: none;">
                    <div id="cameraPlaceholder" class="camera-placeholder">
                        <span>📷 点击拍照按钮启动摄像头</span>
                    </div>
                </div>
                <div class="camera-controls">
                    <button id="startCameraBtn" class="btn btn-primary" onclick="startCamera()">📷 拍照</button>
                    <button id="captureBtn" class="btn btn-warning" onclick="capturePhoto()" style="display: none;">🔘 拍摄</button>
                    <button id="retakeBtn" class="btn btn-secondary" onclick="retakePhoto()" style="display: none;">🔄 重拍</button>
                    <button id="uploadBtn" class="btn btn-primary" onclick="uploadCapturedPhoto()" style="display: none;">⬆️ 上传</button>
                    <button id="stopCameraBtn" class="btn btn-secondary" onclick="stopCamera()" style="display: none;">⏹ 关闭</button>
                </div>
                
                ${m.photos?.length ? `
                    <div class="photo-gallery">
                        ${m.photos.map(p => {
                            const photoPath = p.file_path.replace(/\\/g, '/');
                            const fullPath = photoPath.startsWith('photos/') ? '/' + photoPath : '/photos/' + photoPath;
                            return `
                            <div class="photo-item">
                                <img src="${fullPath}" alt="照片" onclick="openPhotoModal('${fullPath}', '${p.filename || ''}')" onerror="this.onerror=null;this.style.backgroundColor='#f8f9fa';this.style.display='flex';this.style.alignItems='center';this.style.justifyContent='center';this.style.color='#666';this.src='data:image/svg+xml;charset=utf-8,' + encodeURIComponent('\\u6587\\u4EF6\\u4E22\\u5931')">
                                <button class="delete-btn" onclick="deletePhoto(${p.id})">×</button>
                            </div>
                        `}).join('')}
                    </div>
                ` : ''}
            </div>
        </div>
        
        <button class="btn btn-secondary" onclick="cancelSelect()" style="margin-top: 20px;">
            🔄 取消选择
        </button>
    `;
    
    detailEl.classList.add('active');
    document.getElementById('materialList').classList.add('hidden');
}

function getScoreLabel(score) {
    const labels = {
        5: '5分 - 全新可使用',
        4: '4分 - 99新，需要翻新',
        3: '3分 - 外观性能尚可',
        2: '2分 - 仅作为备件或拆机件使用',
        1: '1分 - 建议报废'
    };
    return labels[score] || '未评分';
}

let selectedScore = null;

function setScore(score) {
    selectedScore = score;
    document.querySelectorAll('.score-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

async function submitScore() {
    if (!currentMaterial || selectedScore === null) {
        showMessage('请先选择评分', 'error');
        return;
    }
    
    try {
        const response = await apiRequest('/inventory/records', {
            method: 'POST',
            body: JSON.stringify({
                material_code: currentMaterial.code,
                score: selectedScore
            })
        });
        
        if (response.ok) {
            showMessage('评分已保存!', 'success');
            await refreshMaterial();
        } else {
            showMessage('保存失败', 'error');
        }
    } catch (error) {
        showMessage('提交失败', 'error');
    }
}

function submitScoreWithConfirm() {
    if (!currentMaterial || selectedScore === null) {
        showMessage('请先选择评分', 'error');
        return;
    }
    
    const currentScore = currentMaterial.inventory_records?.[0]?.score;
    const newScoreText = getScoreLabel(selectedScore);
    
    const confirmed = confirm(`当前物料已评分 [${getScoreLabel(currentScore)}]\n\n确定要修改为 [${newScoreText}] 吗？`);
    
    if (confirmed) {
        submitScore();
    }
}

async function uploadPhotos() {
    const input = document.getElementById('photoInput');
    const files = input.files;
    
    if (files.length === 0) {
        showMessage('请选择照片', 'error');
        return;
    }
    
    if (currentMaterial.photos?.length >= 10) {
        showMessage('照片数量已达上限', 'error');
        return;
    }
    
    for (let file of files) {
        if (currentMaterial.photos?.length >= 10) break;
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            await apiRequest(`/inventory/photos/${currentMaterial.code}`, {
                method: 'POST',
                body: formData
            });
        } catch (error) {
            console.error('上传失败:', error);
        }
    }
    
    showMessage('照片上传完成', 'success');
    await refreshMaterial();
}

async function startCamera() {
    const video = document.getElementById('cameraVideo');
    const placeholder = document.getElementById('cameraPlaceholder');
    const startBtn = document.getElementById('startCameraBtn');
    const captureBtn = document.getElementById('captureBtn');
    const stopBtn = document.getElementById('stopCameraBtn');
    
    try {
        currentStream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment' }, 
            audio: false 
        });
        
        video.srcObject = currentStream;
        video.style.display = 'block';
        placeholder.style.display = 'none';
        
        startBtn.style.display = 'none';
        captureBtn.style.display = 'inline-block';
        stopBtn.style.display = 'inline-block';
    } catch (err) {
        showMessage('无法访问摄像头，请检查权限设置', 'error');
        console.error('摄像头错误:', err);
    }
}

function capturePhoto() {
    const video = document.getElementById('cameraVideo');
    const canvas = document.getElementById('cameraCanvas');
    const preview = document.getElementById('photoPreview');
    const captureBtn = document.getElementById('captureBtn');
    const retakeBtn = document.getElementById('retakeBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob((blob) => {
        capturedImageBlob = blob;
        
        preview.src = URL.createObjectURL(blob);
        preview.style.display = 'block';
        video.style.display = 'none';
        
        captureBtn.style.display = 'none';
        retakeBtn.style.display = 'inline-block';
        uploadBtn.style.display = 'inline-block';
    }, 'image/jpeg', 0.85);
}

function retakePhoto() {
    const video = document.getElementById('cameraVideo');
    const preview = document.getElementById('photoPreview');
    const captureBtn = document.getElementById('captureBtn');
    const retakeBtn = document.getElementById('retakeBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    
    capturedImageBlob = null;
    preview.src = '';
    preview.style.display = 'none';
    video.style.display = 'block';
    
    captureBtn.style.display = 'inline-block';
    retakeBtn.style.display = 'none';
    uploadBtn.style.display = 'none';
}

function stopCamera() {
    const video = document.getElementById('cameraVideo');
    const preview = document.getElementById('photoPreview');
    const placeholder = document.getElementById('cameraPlaceholder');
    const startBtn = document.getElementById('startCameraBtn');
    const captureBtn = document.getElementById('captureBtn');
    const retakeBtn = document.getElementById('retakeBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    const stopBtn = document.getElementById('stopCameraBtn');
    
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
    
    video.srcObject = null;
    video.style.display = 'none';
    preview.style.display = 'none';
    placeholder.style.display = 'flex';
    
    capturedImageBlob = null;
    
    startBtn.style.display = 'inline-block';
    captureBtn.style.display = 'none';
    retakeBtn.style.display = 'none';
    uploadBtn.style.display = 'none';
    stopBtn.style.display = 'none';
}

async function uploadCapturedPhoto() {
    if (!capturedImageBlob) {
        showMessage('没有可上传的照片', 'error');
        return;
    }
    
    if (!currentMaterial) {
        showMessage('请先选择一个物料', 'error');
        return;
    }
    
    if (currentMaterial.photos?.length >= 10) {
        showMessage('照片数量已达上限', 'error');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('file', capturedImageBlob, 'camera_photo.jpg');
        
        const response = await apiRequest(`/inventory/photos/${currentMaterial.code}`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            showMessage('拍照上传成功', 'success');
            stopCamera();
            await refreshMaterial();
        } else {
            throw new Error('上传失败');
        }
    } catch (error) {
        showMessage('上传失败', 'error');
        console.error('上传错误:', error);
    }
}

function openPhotoModal(src, caption) {
    const modal = document.getElementById('photoModal');
    const modalImg = document.getElementById('modalImage');
    const modalCaption = document.getElementById('modalCaption');
    
    if (modal && modalImg) {
        modalImg.src = src;
        if (modalCaption) {
            modalCaption.textContent = caption || '照片预览';
        }
        modal.style.display = 'flex';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';
    }
}

function closePhotoModal(event) {
    if (event && event.stopPropagation) {
        event.stopPropagation();
    }
    
    const modal = document.getElementById('photoModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closePhotoModal();
    }
});

async function deletePhoto(id) {
    if (!confirm('确定要删除这张照片吗？')) return;
    
    try {
        const response = await apiRequest(`/inventory/photos/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showMessage('照片已删除', 'success');
            await refreshMaterial();
        }
    } catch (error) {
        showMessage('删除失败', 'error');
    }
}

async function refreshMaterial() {
    if (!currentMaterial) return;
    
    try {
        const response = await apiRequest(`/materials/${currentMaterial.code}`);
        const data = await response.json();
        currentMaterial = data;
        showMaterialDetail(data);
    } catch (error) {
        console.error('刷新失败:', error);
    }
}

function cancelSelect() {
    currentMaterial = null;
    selectedScore = null;
    document.getElementById('materialDetail').classList.remove('active');
    document.getElementById('materialList').classList.remove('hidden');
    document.getElementById('materialList').innerHTML = '';
    document.getElementById('searchInput').value = '';
}

function showMessage(text, type) {
    const msg = document.createElement('div');
    msg.className = `message ${type}`;
    msg.textContent = text;
    
    const main = document.querySelector('main');
    main.insertBefore(msg, main.firstChild);
    
    setTimeout(() => msg.remove(), 3000);
}

document.addEventListener('DOMContentLoaded', async () => {
    await login();
    
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchMaterials();
        }
    });
});
