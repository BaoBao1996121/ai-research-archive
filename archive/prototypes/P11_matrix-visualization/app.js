// 主应用逻辑
let matrix2d, matrix3d;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initialize2D();
    initialize3D();
});

// 标签页切换
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            
            // 移除所有活动状态
            tabButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // 激活选中的标签
            btn.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');
        });
    });
}

// 初始化 2D 可视化
function initialize2D() {
    matrix2d = new Matrix2D('canvas2d');
    
    // 监听矩阵输入变化
    const inputs = ['m00', 'm01', 'm10', 'm11'];
    inputs.forEach(id => {
        const input = document.getElementById(id);
        input.addEventListener('input', () => {
            updateMatrixFromInputs2D();
        });
    });
    
    // 预设按钮
    const presetButtons = document.querySelectorAll('.preset-btn');
    presetButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const values = btn.dataset.matrix.split(',').map(Number);
            matrix2d.animateToMatrix(values[0], values[1], values[2], values[3]);
        });
    });
    
    // 动画按钮
    document.getElementById('animate2d').addEventListener('click', () => {
        animateTransformation2D();
    });
    
    // 重置按钮
    document.getElementById('reset2d').addEventListener('click', () => {
        matrix2d.animateToMatrix(1, 0, 0, 1);
    });
}

function updateMatrixFromInputs2D() {
    const a = parseFloat(document.getElementById('m00').value) || 0;
    const b = parseFloat(document.getElementById('m01').value) || 0;
    const c = parseFloat(document.getElementById('m10').value) || 0;
    const d = parseFloat(document.getElementById('m11').value) || 0;
    
    matrix2d.setMatrix(a, b, c, d);
}

function animateTransformation2D() {
    const transformations = [
        [1, 0, 0, 1],       // 恒等
        [1.5, 0, 0, 1.5],   // 放大
        [0.7071, -0.7071, 0.7071, 0.7071], // 旋转 45°
        [1, 0.5, 0, 1],     // 剪切
        [2, 0, 0, 1],       // X 拉伸
        [1, 0, 0, 2],       // Y 拉伸
        [0, 1, 1, 0],       // 交换轴
        [1, 0, 0, 1]        // 回到恒等
    ];
    
    let index = 0;
    const animate = () => {
        if (index < transformations.length) {
            const t = transformations[index];
            matrix2d.animateToMatrix(t[0], t[1], t[2], t[3], 1000);
            index++;
            setTimeout(animate, 1200);
        }
    };
    
    animate();
}

// 初始化 3D 可视化
function initialize3D() {
    matrix3d = new Matrix3D('canvas3d');
    
    // 监听矩阵输入变化
    const inputs = [
        'm3d00', 'm3d01', 'm3d02',
        'm3d10', 'm3d11', 'm3d12',
        'm3d20', 'm3d21', 'm3d22'
    ];
    
    inputs.forEach(id => {
        const input = document.getElementById(id);
        input.addEventListener('input', () => {
            updateMatrixFromInputs3D();
        });
    });
    
    // 预设按钮
    const presetButtons = document.querySelectorAll('.preset-btn-3d');
    presetButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const values = btn.dataset.matrix.split(',').map(Number);
            matrix3d.animateToMatrix(
                values[0], values[1], values[2],
                values[3], values[4], values[5],
                values[6], values[7], values[8]
            );
        });
    });
    
    // 动画按钮
    document.getElementById('animate3d').addEventListener('click', () => {
        animateTransformation3D();
    });
    
    // 重置按钮
    document.getElementById('reset3d').addEventListener('click', () => {
        matrix3d.animateToMatrix(1, 0, 0, 0, 1, 0, 0, 0, 1);
    });
    
    // 自动旋转开关
    document.getElementById('autoRotate3d').addEventListener('change', (e) => {
        matrix3d.camera.autoRotate = e.target.checked;
    });
}

function updateMatrixFromInputs3D() {
    const values = [
        parseFloat(document.getElementById('m3d00').value) || 0,
        parseFloat(document.getElementById('m3d01').value) || 0,
        parseFloat(document.getElementById('m3d02').value) || 0,
        parseFloat(document.getElementById('m3d10').value) || 0,
        parseFloat(document.getElementById('m3d11').value) || 0,
        parseFloat(document.getElementById('m3d12').value) || 0,
        parseFloat(document.getElementById('m3d20').value) || 0,
        parseFloat(document.getElementById('m3d21').value) || 0,
        parseFloat(document.getElementById('m3d22').value) || 0
    ];
    
    matrix3d.setMatrix(...values);
}

function animateTransformation3D() {
    const transformations = [
        [1, 0, 0, 0, 1, 0, 0, 0, 1],           // 恒等
        [1.5, 0, 0, 0, 1.5, 0, 0, 0, 1.5],     // 放大
        [1, 0, 0, 0, 0.7071, -0.7071, 0, 0.7071, 0.7071], // 绕 X 旋转 45°
        [0.7071, 0, 0.7071, 0, 1, 0, -0.7071, 0, 0.7071], // 绕 Y 旋转 45°
        [0.7071, -0.7071, 0, 0.7071, 0.7071, 0, 0, 0, 1],  // 绕 Z 旋转 45°
        [2, 0, 0, 0, 1, 0, 0, 0, 1],           // X 拉伸
        [1, 0, 0, 0, 2, 0, 0, 0, 1],           // Y 拉伸
        [1, 0, 0, 0, 1, 0, 0, 0, 2],           // Z 拉伸
        [1, 0, 0, 0, 1, 0, 0, 0, 1]            // 回到恒等
    ];
    
    let index = 0;
    const animate = () => {
        if (index < transformations.length) {
            const t = transformations[index];
            matrix3d.animateToMatrix(
                t[0], t[1], t[2],
                t[3], t[4], t[5],
                t[6], t[7], t[8],
                1000
            );
            index++;
            setTimeout(animate, 1200);
        }
    };
    
    animate();
}

// 添加键盘快捷键
document.addEventListener('keydown', (e) => {
    // 空格键：切换标签
    if (e.code === 'Space' && e.target.tagName !== 'INPUT') {
        e.preventDefault();
        const currentTab = document.querySelector('.tab-btn.active');
        const tabs = Array.from(document.querySelectorAll('.tab-btn'));
        const currentIndex = tabs.indexOf(currentTab);
        const nextIndex = (currentIndex + 1) % tabs.length;
        tabs[nextIndex].click();
    }
    
    // R 键：重置当前视图
    if (e.key === 'r' || e.key === 'R') {
        const active2D = document.getElementById('2d-tab').classList.contains('active');
        if (active2D) {
            matrix2d.animateToMatrix(1, 0, 0, 1);
        } else {
            matrix3d.animateToMatrix(1, 0, 0, 0, 1, 0, 0, 0, 1);
        }
    }
    
    // A 键：播放动画
    if (e.key === 'a' || e.key === 'A') {
        const active2D = document.getElementById('2d-tab').classList.contains('active');
        if (active2D) {
            animateTransformation2D();
        } else {
            animateTransformation3D();
        }
    }
});
