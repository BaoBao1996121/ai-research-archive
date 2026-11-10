// 2D 矩阵变换可视化
class Matrix2D {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.width = this.canvas.width;
        this.height = this.canvas.height;
        this.centerX = this.width / 2;
        this.centerY = this.height / 2;
        this.scale = 50; // 像素/单位
        
        // 矩阵参数
        this.matrix = {
            a: 1, b: 0,
            c: 0, d: 1
        };
        
        // 动画参数
        this.animating = false;
        this.animationProgress = 0;
        this.startMatrix = { a: 1, b: 0, c: 0, d: 1 };
        this.targetMatrix = { a: 1, b: 0, c: 0, d: 1 };
        
        this.init();
    }
    
    init() {
        this.draw();
    }
    
    setMatrix(a, b, c, d) {
        this.matrix = { a, b, c, d };
        this.draw();
        this.updateInfo();
    }
    
    animateToMatrix(a, b, c, d, duration = 1500) {
        this.startMatrix = { ...this.matrix };
        this.targetMatrix = { a, b, c, d };
        this.animating = true;
        this.animationProgress = 0;
        
        const startTime = Date.now();
        const animate = () => {
            const elapsed = Date.now() - startTime;
            this.animationProgress = Math.min(elapsed / duration, 1);
            
            // 使用缓动函数
            const t = this.easeInOutCubic(this.animationProgress);
            
            this.matrix.a = this.lerp(this.startMatrix.a, this.targetMatrix.a, t);
            this.matrix.b = this.lerp(this.startMatrix.b, this.targetMatrix.b, t);
            this.matrix.c = this.lerp(this.startMatrix.c, this.targetMatrix.c, t);
            this.matrix.d = this.lerp(this.startMatrix.d, this.targetMatrix.d, t);
            
            this.draw();
            this.updateInfo();
            
            if (this.animationProgress < 1) {
                requestAnimationFrame(animate);
            } else {
                this.animating = false;
            }
        };
        
        animate();
    }
    
    easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }
    
    lerp(start, end, t) {
        return start + (end - start) * t;
    }
    
    // 计算行列式
    getDeterminant() {
        return this.matrix.a * this.matrix.d - this.matrix.b * this.matrix.c;
    }
    
    updateInfo() {
        const det = this.getDeterminant();
        document.getElementById('det2d').textContent = det.toFixed(2);
        document.getElementById('scale2d').textContent = '×' + Math.abs(det).toFixed(2);
        
        // 更新输入框
        document.getElementById('m00').value = this.matrix.a.toFixed(2);
        document.getElementById('m01').value = this.matrix.b.toFixed(2);
        document.getElementById('m10').value = this.matrix.c.toFixed(2);
        document.getElementById('m11').value = this.matrix.d.toFixed(2);
    }
    
    // 变换点
    transformPoint(x, y) {
        return {
            x: this.matrix.a * x + this.matrix.b * y,
            y: this.matrix.c * x + this.matrix.d * y
        };
    }
    
    // 转换为画布坐标
    toCanvasCoords(x, y) {
        return {
            x: this.centerX + x * this.scale,
            y: this.centerY - y * this.scale
        };
    }
    
    draw() {
        const ctx = this.ctx;
        
        // 清空画布
        ctx.clearRect(0, 0, this.width, this.height);
        
        // 绘制背景网格（原始）
        this.drawGrid(false);
        
        // 绘制变换后的网格
        this.drawGrid(true);
        
        // 绘制原始和变换后的形状
        this.drawShape();
        
        // 绘制基向量
        this.drawBasisVectors();
        
        // 绘制坐标轴
        this.drawAxes();
    }
    
    drawGrid(transformed) {
        const ctx = this.ctx;
        const gridSize = 10;
        const range = 6;
        
        ctx.strokeStyle = transformed ? 'rgba(102, 126, 234, 0.2)' : 'rgba(200, 200, 200, 0.3)';
        ctx.lineWidth = transformed ? 1.5 : 0.5;
        
        // 垂直线
        for (let i = -range; i <= range; i++) {
            ctx.beginPath();
            for (let j = -range; j <= range; j += 0.1) {
                let x = i;
                let y = j;
                
                if (transformed) {
                    const tp = this.transformPoint(x, y);
                    x = tp.x;
                    y = tp.y;
                }
                
                const cp = this.toCanvasCoords(x, y);
                
                if (j === -range) {
                    ctx.moveTo(cp.x, cp.y);
                } else {
                    ctx.lineTo(cp.x, cp.y);
                }
            }
            ctx.stroke();
        }
        
        // 水平线
        for (let j = -range; j <= range; j++) {
            ctx.beginPath();
            for (let i = -range; i <= range; i += 0.1) {
                let x = i;
                let y = j;
                
                if (transformed) {
                    const tp = this.transformPoint(x, y);
                    x = tp.x;
                    y = tp.y;
                }
                
                const cp = this.toCanvasCoords(x, y);
                
                if (i === -range) {
                    ctx.moveTo(cp.x, cp.y);
                } else {
                    ctx.lineTo(cp.x, cp.y);
                }
            }
            ctx.stroke();
        }
    }
    
    drawShape() {
        const ctx = this.ctx;
        
        // 绘制一个单位正方形
        const square = [
            { x: 1, y: 1 },
            { x: 2, y: 1 },
            { x: 2, y: 2 },
            { x: 1, y: 2 }
        ];
        
        // 原始形状
        ctx.fillStyle = 'rgba(255, 182, 193, 0.3)';
        ctx.strokeStyle = 'rgba(255, 105, 180, 0.6)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        square.forEach((p, i) => {
            const cp = this.toCanvasCoords(p.x, p.y);
            if (i === 0) ctx.moveTo(cp.x, cp.y);
            else ctx.lineTo(cp.x, cp.y);
        });
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        
        // 变换后的形状
        ctx.fillStyle = 'rgba(118, 75, 162, 0.4)';
        ctx.strokeStyle = 'rgba(118, 75, 162, 0.8)';
        ctx.lineWidth = 3;
        ctx.beginPath();
        square.forEach((p, i) => {
            const tp = this.transformPoint(p.x, p.y);
            const cp = this.toCanvasCoords(tp.x, tp.y);
            if (i === 0) ctx.moveTo(cp.x, cp.y);
            else ctx.lineTo(cp.x, cp.y);
        });
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
    }
    
    drawBasisVectors() {
        const ctx = this.ctx;
        
        // i-hat (红色) - x轴基向量
        const iHat = this.transformPoint(1, 0);
        this.drawVector(0, 0, iHat.x, iHat.y, '#e74c3c', 'î');
        
        // j-hat (绿色) - y轴基向量
        const jHat = this.transformPoint(0, 1);
        this.drawVector(0, 0, jHat.x, jHat.y, '#2ecc71', 'ĵ');
    }
    
    drawVector(x1, y1, x2, y2, color, label) {
        const ctx = this.ctx;
        const start = this.toCanvasCoords(x1, y1);
        const end = this.toCanvasCoords(x2, y2);
        
        // 绘制箭头
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = 3;
        
        ctx.beginPath();
        ctx.moveTo(start.x, start.y);
        ctx.lineTo(end.x, end.y);
        ctx.stroke();
        
        // 箭头头部
        const angle = Math.atan2(end.y - start.y, end.x - start.x);
        const arrowSize = 10;
        
        ctx.beginPath();
        ctx.moveTo(end.x, end.y);
        ctx.lineTo(
            end.x - arrowSize * Math.cos(angle - Math.PI / 6),
            end.y - arrowSize * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
            end.x - arrowSize * Math.cos(angle + Math.PI / 6),
            end.y - arrowSize * Math.sin(angle + Math.PI / 6)
        );
        ctx.closePath();
        ctx.fill();
        
        // 标签
        ctx.font = 'bold 16px Arial';
        ctx.fillText(label, end.x + 10, end.y - 10);
    }
    
    drawAxes() {
        const ctx = this.ctx;
        
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 1;
        
        // X轴
        ctx.beginPath();
        ctx.moveTo(0, this.centerY);
        ctx.lineTo(this.width, this.centerY);
        ctx.stroke();
        
        // Y轴
        ctx.beginPath();
        ctx.moveTo(this.centerX, 0);
        ctx.lineTo(this.centerX, this.height);
        ctx.stroke();
        
        // 原点
        ctx.fillStyle = '#333';
        ctx.font = '14px Arial';
        ctx.fillText('O', this.centerX + 5, this.centerY - 5);
    }
}
