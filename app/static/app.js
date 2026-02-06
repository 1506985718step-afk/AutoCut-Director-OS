// 全局状态
let currentStep = 1;
let selectedFile = null;
let localFilePath = null;
let currentWorkflow = 'single_video';  // 'single_video' 或 'script_assembly'
let videoSource = 'local';  // 'local' 或 'upload'
let manifestFile = null;
let scriptFile = null;
let currentJobId = null;
let processingInterval = null;
let startTime = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initUpload();
    initWorkflowSwitch();
});

// 初始化上传
function initUpload() {
    const uploadZone = document.getElementById('uploadZone');
    const videoInput = document.getElementById('videoInput');
    
    uploadZone.onclick = () => videoInput.click();
    
    uploadZone.ondragover = (e) => {
        e.preventDefault();
        uploadZone.style.background = '#e8ebff';
    };
    
    uploadZone.ondragleave = () => {
        uploadZone.style.background = '#f8f9ff';
    };
    
    uploadZone.ondrop = (e) => {
        e.preventDefault();
        uploadZone.style.background = '#f8f9ff';
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    };
    
    videoInput.onchange = (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    };
}

// 处理文件选择
function handleFileSelect(file) {
    selectedFile = file;
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSelected').style.display = 'flex';
    document.getElementById('uploadZone').style.display = 'none';
    document.getElementById('startBtn').disabled = false;
}

// 移除文件
function removeFile() {
    selectedFile = null;
    document.getElementById('fileSelected').style.display = 'none';
    document.getElementById('uploadZone').style.display = 'block';
    document.getElementById('startBtn').disabled = true;
}

// 开始剪辑
async function startEditing() {
    if (!selectedFile) return;
    
    // 切换到处理步骤
    showStep(2);
    startTime = Date.now();
    
    // 开始计时
    startTimer();
    
    // 创建项目
    await createProject();
}

// 创建项目（使用新的产品级 API）
async function createProject() {
    addLog('开始创建项目...');
    
    const formData = new FormData();
    
    if (currentWorkflow === 'single_video') {
        // 单视频模式
        if (videoSource === 'local') {
            // 本地文件模式
            if (selectedFile) {
                formData.append('video', selectedFile);
            } else {
                throw new Error('请选择视频文件');
            }
        } else {
            // 上传模式
            if (!selectedFile) {
                throw new Error('请选择要上传的视频文件');
            }
            formData.append('video', selectedFile);
        }
        
        formData.append('platform', document.getElementById('platform').value);
        formData.append('style', document.getElementById('style').value);
        formData.append('pace', 'medium');
        formData.append('subtitle_density', 'standard');
        formData.append('music_preference', 'emotional');
        
        try {
            const response = await fetch('/api/projects/create', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                currentJobId = result.project_id;
                addLog(`项目创建成功 (ID: ${result.project_id})`);
                
                // 开始轮询进度
                await pollProjectProgress();
            } else {
                throw new Error(result.detail || '创建项目失败');
            }
        } catch (error) {
            addLog(`错误: ${error.message}`, 'error');
            updateTimeline(1, 'error', '失败');
            alert('创建项目失败: ' + error.message);
        }
        
    } else {
        // 零散镜头组装模式
        if (!manifestFile) {
            throw new Error('请选择素材清单文件');
        }
        
        formData.append('assets_manifest', manifestFile);
        
        if (scriptFile) {
            formData.append('script_outline', scriptFile);
        }
        
        formData.append('platform', document.getElementById('platform').value);
        formData.append('style', document.getElementById('style').value);
        formData.append('pace', 'medium');
        formData.append('subtitle_density', 'standard');
        formData.append('music_preference', 'emotional');
        
        try {
            const response = await fetch('/api/assembly/create', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                currentJobId = result.project_id;
                addLog(`组装项目创建成功 (ID: ${result.project_id})`);
                
                // 开始轮询进度
                await pollAssemblyProgress();
            } else {
                throw new Error(result.detail || '创建组装项目失败');
            }
        } catch (error) {
            addLog(`错误: ${error.message}`, 'error');
            updateTimeline(1, 'error', '失败');
            alert('创建组装项目失败: ' + error.message);
        }
    }
}

// 轮询组装项目进度
async function pollAssemblyProgress() {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/assembly/${currentJobId}/status`);
            const status = await response.json();
            
            // 更新进度
            updateProgress(status.progress);
            
            // 更新日志
            if (status.current_step) {
                addLog(`当前步骤: ${status.current_step}`);
            }
            
            // 检查是否完成
            if (status.status === 'completed') {
                clearInterval(pollInterval);
                addLog('组装项目处理完成！');
                stopTimer();
                
                // 切换到预览步骤
                await sleep(1000);
                await showPreview();
            } else if (status.status === 'error') {
                clearInterval(pollInterval);
                addLog(`错误: ${status.error || '处理失败'}`, 'error');
                stopTimer();
                alert('处理失败，请重试');
            }
            
        } catch (error) {
            addLog(`轮询错误: ${error.message}`, 'error');
        }
    }, 2000);
}

// 轮询项目进度
async function pollProjectProgress() {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/projects/${currentJobId}/status`);
            const status = await response.json();
            
            // 更新进度
            updateProgress(status.progress);
            
            // 更新时间线
            if (status.steps) {
                status.steps.forEach((step, index) => {
                    const timelineIndex = index + 1;
                    if (step.status === 'completed') {
                        updateTimeline(timelineIndex, 'completed', '已完成');
                    } else if (step.status === 'active') {
                        updateTimeline(timelineIndex, 'active', step.message || '进行中...');
                    }
                });
            }
            
            // 更新日志
            if (status.current_step) {
                addLog(`当前步骤: ${status.current_step}`);
            }
            
            // 检查是否完成
            if (status.status === 'completed') {
                clearInterval(pollInterval);
                addLog('项目处理完成！');
                stopTimer();
                
                // 切换到预览步骤
                await sleep(1000);
                await showPreview();
            } else if (status.status === 'error') {
                clearInterval(pollInterval);
                addLog(`错误: ${status.error || '处理失败'}`, 'error');
                stopTimer();
                alert('处理失败，请重试');
            }
            
        } catch (error) {
            addLog(`轮询错误: ${error.message}`, 'error');
        }
    }, 2000);  // 每 2 秒轮询一次
}

// 显示预览
async function showPreview() {
    showStep(3);
    
    // 获取项目详情
    try {
        const response = await fetch(`/api/projects/${currentJobId}`);
        const project = await response.json();
        
        // 填充摘要信息
        if (project.summary) {
            document.getElementById('summaryHook').textContent = project.summary.hook || '未知';
            document.getElementById('summaryPace').textContent = project.summary.pace || '未知';
            document.getElementById('summaryBGM').textContent = project.summary.music || '无';
            document.getElementById('summaryDuration').textContent = project.summary.duration || '未知';
        } else {
            // 使用默认值
            document.getElementById('summaryHook').textContent = '前 3 秒精彩片段';
            document.getElementById('summaryPace').textContent = '中等';
            document.getElementById('summaryBGM').textContent = '情绪型';
            document.getElementById('summaryDuration').textContent = '45 秒';
        }
        
        // 设置预览视频
        const videoPreview = document.getElementById('videoPreview');
        videoPreview.src = project.preview_url || `/api/projects/${currentJobId}/preview`;
        
        addLog('预览加载完成');
    } catch (error) {
        addLog(`预览加载失败: ${error.message}`, 'error');
        // 使用默认值
        document.getElementById('summaryHook').textContent = '前 3 秒精彩片段';
        document.getElementById('summaryPace').textContent = '中等';
        document.getElementById('summaryBGM').textContent = '情绪型';
        document.getElementById('summaryDuration').textContent = '45 秒';
    }
}

// 调整意图
async function adjustIntent(intentType, action, event) {
    addLog(`用户调整: ${intentType} - ${action}`);
    
    // 显示处理中
    const btn = event.target;
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = '处理中...';
    
    try {
        // 构建调整对象
        const adjustments = {
            pace: 'keep',
            hook: 'keep',
            music: 'keep',
            subtitle: 'keep'
        };
        
        // 设置当前调整
        adjustments[intentType] = action;
        
        // 调用调整 API
        const response = await fetch(`/api/projects/${currentJobId}/adjust`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({adjustments})
        });
        
        const result = await response.json();
        
        if (response.ok) {
            addLog(`正在重新生成（版本 ${result.new_version}）...`);
            btn.textContent = '重新生成中...';
            
            // 轮询新版本进度
            await pollAdjustmentProgress(result.new_version);
            
            btn.disabled = false;
            btn.textContent = '✓ 已应用';
            
            // 3秒后恢复按钮文本
            setTimeout(() => {
                btn.textContent = originalText;
            }, 3000);
            
        } else {
            throw new Error(result.detail || '调整失败');
        }
        
    } catch (error) {
        addLog(`调整失败: ${error.message}`, 'error');
        btn.disabled = false;
        btn.textContent = originalText;
        alert('调整失败: ' + error.message);
    }
}

// 轮询调整进度
async function pollAdjustmentProgress(version) {
    return new Promise((resolve, reject) => {
        const pollInterval = setInterval(async () => {
            try {
                const versionProjectId = `${currentJobId}_v${version}`;
                const response = await fetch(`/api/projects/${versionProjectId}/status`);
                const status = await response.json();
                
                addLog(`调整进度: ${status.progress}%`);
                
                if (status.status === 'completed') {
                    clearInterval(pollInterval);
                    addLog('调整完成，刷新预览...');
                    
                    // 更新当前项目 ID 为新版本
                    currentJobId = versionProjectId;
                    
                    // 刷新预览
                    await showPreview();
                    
                    resolve();
                } else if (status.status === 'error') {
                    clearInterval(pollInterval);
                    reject(new Error(status.error || '调整失败'));
                }
                
            } catch (error) {
                clearInterval(pollInterval);
                reject(error);
            }
        }, 2000);
    });
}

// 确认并导出
function confirmAndExport() {
    showStep(4);
}

// 导出视频
async function exportVideo(quality) {
    addLog(`开始导出: ${quality}`);
    
    try {
        // 创建导出任务
        const response = await fetch('/api/exports/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                project_id: currentJobId.replace(/_v\d+$/, ''),  // 移除版本后缀
                quality: quality
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            const exportId = result.export_id;
            addLog(`导出任务创建成功 (ID: ${exportId})`);
            
            // 轮询导出进度
            await pollExportProgress(exportId);
            
            // 显示下载按钮
            document.getElementById('downloadCard').style.display = 'block';
            document.getElementById('downloadCard').dataset.exportId = exportId;
            
            addLog('导出完成！');
        } else {
            throw new Error(result.detail || '创建导出任务失败');
        }
        
    } catch (error) {
        addLog(`导出失败: ${error.message}`, 'error');
        alert('导出失败: ' + error.message);
    }
}

// 轮询导出进度
async function pollExportProgress(exportId) {
    return new Promise((resolve, reject) => {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/exports/${exportId}/status`);
                const status = await response.json();
                
                addLog(`导出进度: ${status.progress}%`);
                
                if (status.status === 'completed') {
                    clearInterval(pollInterval);
                    resolve();
                } else if (status.status === 'error') {
                    clearInterval(pollInterval);
                    reject(new Error(status.error || '导出失败'));
                }
                
            } catch (error) {
                clearInterval(pollInterval);
                reject(error);
            }
        }, 2000);
    });
}

// 下载视频
function downloadVideo() {
    const exportId = document.getElementById('downloadCard').dataset.exportId;
    if (!exportId) {
        alert('导出 ID 不存在');
        return;
    }
    
    // 直接打开下载链接
    window.location.href = `/api/exports/${exportId}/download`;
    addLog('开始下载成片...');
}

// 返回
function goBack() {
    if (confirm('确定要重新开始吗？当前进度将丢失。')) {
        location.reload();
    }
}

// 删除项目
function deleteProject() {
    if (confirm('确定要删除此项目吗？')) {
        alert('项目已删除');
        location.reload();
    }
}

// 创建新项目
function createNew() {
    location.reload();
}

// 加载版本
function loadVersion(version) {
    alert(`加载版本 V${version}`);
}

// 工具函数
function showStep(step) {
    document.querySelectorAll('.step-section').forEach(section => {
        section.style.display = 'none';
    });
    document.getElementById(`step${step}`).style.display = 'block';
    currentStep = step;
}

function updateTimeline(index, status, time) {
    const item = document.getElementById(`timeline${index}`);
    item.className = `timeline-item ${status}`;
    item.querySelector('.timeline-time').textContent = time;
}

function updateProgress(percent) {
    document.getElementById('progressBar').style.width = percent + '%';
}

function addLog(message, type = 'info') {
    const logContent = document.getElementById('logContent');
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logContent.appendChild(entry);
    logContent.scrollTop = logContent.scrollHeight;
}

function startTimer() {
    processingInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        document.getElementById('elapsedTime').textContent = 
            `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        // 更新预计剩余时间
        const remaining = Math.max(0, 180 - elapsed);
        const remMin = Math.floor(remaining / 60);
        const remSec = remaining % 60;
        document.getElementById('remainingTime').textContent = 
            `${remMin}:${remSec.toString().padStart(2, '0')}`;
    }, 1000);
}

function stopTimer() {
    if (processingInterval) {
        clearInterval(processingInterval);
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


// ============ 加载动画和错误处理 ============

// 显示加载动画
function showLoading(message = '处理中...') {
    // 移除已存在的加载动画
    hideLoading();
    
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.id = 'loadingOverlay';
    
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="loading-spinner"></div>
            <p>${message}</p>
        </div>
    `;
    
    document.body.appendChild(overlay);
}

// 隐藏加载动画
function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

// 显示错误消息
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    // 插入到当前步骤的顶部
    const currentStep = document.getElementById(`step${currentStep}`);
    if (currentStep) {
        currentStep.insertBefore(errorDiv, currentStep.firstChild);
        
        // 3秒后自动移除
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
}

// 显示成功消息
function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = message;
    
    // 插入到当前步骤的顶部
    const currentStepEl = document.getElementById(`step${currentStep}`);
    if (currentStepEl) {
        currentStepEl.insertBefore(successDiv, currentStepEl.firstChild);
        
        // 3秒后自动移除
        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }
}

// 错误处理包装器
async function withErrorHandling(fn, errorMessage = '操作失败') {
    try {
        return await fn();
    } catch (error) {
        console.error(error);
        showError(`${errorMessage}: ${error.message}`);
        addLog(`错误: ${error.message}`, 'error');
        throw error;
    }
}

// 重试机制
async function retryWithBackoff(fn, maxRetries = 3, initialDelay = 1000) {
    let lastError;
    
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await fn();
        } catch (error) {
            lastError = error;
            
            if (i < maxRetries - 1) {
                const delay = initialDelay * Math.pow(2, i);
                addLog(`重试 ${i + 1}/${maxRetries}，等待 ${delay}ms...`);
                await sleep(delay);
            }
        }
    }
    
    throw lastError;
}

// 网络请求包装器（带超时和重试）
async function fetchWithTimeout(url, options = {}, timeout = 30000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        
        if (error.name === 'AbortError') {
            throw new Error('请求超时，请检查网络连接');
        }
        
        throw error;
    }
}

// 验证文件
function validateFile(file) {
    // 检查文件类型
    const validTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo'];
    if (!validTypes.includes(file.type)) {
        throw new Error('不支持的文件格式，请上传 MP4、MOV 或 AVI 格式');
    }
    
    // 检查文件大小（2GB）
    const maxSize = 2 * 1024 * 1024 * 1024;
    if (file.size > maxSize) {
        throw new Error('文件太大，最大支持 2GB');
    }
    
    return true;
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// 格式化时间
function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

// 更新文件选择显示
function handleFileSelect(file) {
    try {
        // 验证文件
        validateFile(file);
        
        selectedFile = file;
        
        // 更新显示
        const fileName = document.getElementById('fileName');
        fileName.textContent = `${file.name} (${formatFileSize(file.size)})`;
        
        document.getElementById('fileSelected').style.display = 'flex';
        document.getElementById('uploadZone').style.display = 'none';
        document.getElementById('startBtn').disabled = false;
        
        addLog(`文件已选择: ${file.name}`);
        
    } catch (error) {
        showError(error.message);
        selectedFile = null;
    }
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查浏览器兼容性
    if (!window.fetch) {
        showError('您的浏览器不支持，请使用 Chrome、Edge 或 Firefox 最新版本');
    }
    
    // 检查服务器连接
    checkServerConnection();
});

// 检查服务器连接
async function checkServerConnection() {
    try {
        const response = await fetchWithTimeout('/health', {}, 5000);
        if (response.ok) {
            console.log('服务器连接正常');
        } else {
            showError('服务器连接异常，请检查服务是否启动');
        }
    } catch (error) {
        showError('无法连接到服务器，请检查服务是否启动');
    }
}


// ============ 工作流切换 ============

// 初始化工作流切换
function initWorkflowSwitch() {
    // 监听清单文件选择
    const manifestInput = document.getElementById('manifestInput');
    if (manifestInput) {
        manifestInput.onchange = (e) => {
            if (e.target.files.length > 0) {
                manifestFile = e.target.files[0];
                addLog(`素材清单已选择: ${manifestFile.name}`);
            }
        };
    }
    
    // 监听脚本文件选择
    const scriptInput = document.getElementById('scriptInput');
    if (scriptInput) {
        scriptInput.onchange = (e) => {
            if (e.target.files.length > 0) {
                scriptFile = e.target.files[0];
                addLog(`脚本大纲已选择: ${scriptFile.name}`);
            }
        };
    }
}

// 切换工作流
function switchWorkflow(workflow) {
    currentWorkflow = workflow;
    
    const singleVideoMode = document.getElementById('singleVideoMode');
    const scriptAssemblyMode = document.getElementById('scriptAssemblyMode');
    
    if (workflow === 'single_video') {
        singleVideoMode.style.display = 'block';
        scriptAssemblyMode.style.display = 'none';
        addLog('切换到单视频剪辑模式');
    } else {
        singleVideoMode.style.display = 'none';
        scriptAssemblyMode.style.display = 'block';
        addLog('切换到零散镜头组装模式');
    }
    
    // 检查是否可以开始
    checkCanStart();
}

// 切换视频来源
function switchVideoSource(source) {
    videoSource = source;
    
    const localFileMode = document.getElementById('localFileMode');
    const uploadFileMode = document.getElementById('uploadFileMode');
    
    if (source === 'local') {
        localFileMode.style.display = 'block';
        uploadFileMode.style.display = 'none';
        addLog('切换到本地文件模式');
    } else {
        localFileMode.style.display = 'none';
        uploadFileMode.style.display = 'block';
        addLog('切换到上传文件模式');
    }
    
    // 检查是否可以开始
    checkCanStart();
}

// 浏览本地文件
function browseLocalFile() {
    // 创建一个隐藏的文件输入
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'video/*';
    
    input.onchange = (e) => {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            // 在本地模式下，我们只需要文件路径
            // 但浏览器不允许直接获取完整路径，所以我们使用文件名
            document.getElementById('localFilePath').value = file.name;
            localFilePath = file.name;
            
            // 实际上我们仍然需要文件对象用于后续处理
            selectedFile = file;
            
            addLog(`本地文件已选择: ${file.name}`);
            checkCanStart();
        }
    };
    
    input.click();
}

// 检查是否可以开始
function checkCanStart() {
    const startBtn = document.getElementById('startBtn');
    
    if (currentWorkflow === 'single_video') {
        // 单视频模式
        if (videoSource === 'local') {
            // 本地文件模式：需要文件路径
            startBtn.disabled = !localFilePath && !selectedFile;
        } else {
            // 上传模式：需要选择文件
            startBtn.disabled = !selectedFile;
        }
    } else {
        // 零散镜头模式：需要素材清单
        startBtn.disabled = !manifestFile;
    }
}
