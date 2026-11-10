// 3D 矩阵变换可视化
class Matrix3D {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.width = this.canvas.width;
        this.height = this.canvas.height;
        this.centerX = this.width / 2;
        this.centerY = this.height / 2;
        this.scale = 50;
        
        // 3x3 矩阵
        this.matrix = {
            a: 1, b: 0, c: 0,
            d: 0, e: 1, f: 0,
            g: 0, h: 0, i: 1
        };
        
        // 相机参数
        this.camera = {
            distance: 8,
            angleX: 0.3,
            angleY: 0.5,
            autoRotate: true
        };
        
        // 动画参数
        this.animating = false;
        this.animationProgress = 0;
        this.startMatrix = { a: 1, b: 0, c: 0, d: 0, e: 1, f: 0, g: 0, h: 0, i: 1 };
        this.targetMatrix = { a: 1, b: 0, c: 0, d: 0, e: 1, f: 0, g: 0, h: 0, i: 1 };
        
        this.init();
    }
    
    init() {
        this.startAnimation();
    }
    
    startAnimation() {
        const animate = () => {
            if (this.camera.autoRotate && !this.animating) {
                this.camera.angleY += 0.005;
            }
            this.draw();
            requestAnimationFrame(animate);
        };
        animate();
    }
    
    setMatrix(a, b, c, d, e, f, g, h, i) {
        this.matrix = { a, b, c, d, e, f, g, h, i };
        this.updateInfo();
    }
    
    animateToMatrix(a, b, c, d, e, f, g, h, i, duration = 1500) {
        this.startMatrix = { ...this.matrix };
        this.targetMatrix = { a, b, c, d, e, f, g, h, i };
        this.animating = true;
        this.animationProgress = 0;
        
        const startTime = Date.now();
        const animate = () => {
            const elapsed = Date.now() - startTime;
            this.animationProgress = Math.min(elapsed / duration, 1);
            
            const t = this.easeInOutCubic(this.animationProgress);
            
            this.matrix.a = this.lerp(this.startMatrix.a, this.targetMatrix.a, t);
            this.matrix.b = this.lerp(this.startMatrix.b, this.targetMatrix.b, t);
            this.matrix.c = this.lerp(this.startMatrix.c, this.targetMatrix.c, t);
            this.matrix.d = this.lerp(this.startMatrix.d, this.targetMatrix.d, t);
            this.matrix.e = this.lerp(this.startMatrix.e, this.targetMatrix.e, t);
            this.matrix.f = this.lerp(this.startMatrix.f, this.targetMatrix.f, t);
            this.matrix.g = this.lerp(this.startMatrix.g, this.targetMatrix.g, t);
            this.matrix.h = this.lerp(this.startMatrix.h, this.targetMatrix.h, t);
            this.matrix.i = this.lerp(this.startMatrix.i, this.targetMatrix.i, t);
            
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
    
    // 计算 3x3 矩阵的行列式
    getDeterminant() {
        const m = this.matrix;
        return m.a * (m.e * m.i - m.f * m.h) -
               m.b * (m.d * m.i - m.f * m.g) +
               m.c * (m.d * m.h - m.e * m.g);
    }
    
    updateInfo() {
        const det = this.getDeterminant();
        document.getElementById('det3d').textContent = det.toFixed(2);
        document.getElementById('scale3d').textContent = '×' + Math.abs(det).toFixed(2);
        
        // 更新输入框
        document.getElementById('m3d00').value = this.matrix.a.toFixed(2);
        document.getElementById('m3d01').value = this.matrix.b.toFixed(2);
        document.getElementById('m3d02').value = this.matrix.c.toFixed(2);
        document.getElementById('m3d10').value = this.matrix.d.toFixed(2);
        document.getElementById('m3d11').value = this.matrix.e.toFixed(2);
        document.getElementById('m3d12').value = this.matrix.f.toFixed(2);
        document.getElementById('m3d20').value = this.matrix.g.toFixed(2);
        document.getElementById('m3d21').value = this.matrix.h.toFixed(2);
        document.getElementById('m3d22').value = this.matrix.i.toFixed(2);
    }
    
    // 3D 矩阵变换
    transformPoint(x, y, z) {
        const m = this.matrix;
        return {
            x: m.a * x + m.b * y + m.c * z,
            y: m.d * x + m.e * y + m.f * z,
            z: m.g * x + m.h * y + m.i * z
        };
    }
    
    // 3D 到 2D 投影（简单透视投影）
    project3D(x, y, z) {
        // 应用相机旋转
        let p = this.rotateY({ x, y, z }, this.camera.angleY);
        p = this.rotateX(p, this.camera.angleX);
        
        // 透视投影
        const distance = this.camera.distance;
        const perspective = distance / (distance + p.z);
        
        return {
            x: this.centerX + p.x * this.scale * perspective,
            y: this.centerY - p.y * this.scale * perspective,
            z: p.z
        };
    }
    
    rotateX(p, angle) {
        const cos = Math.cos(angle);
        const sin = Math.sin(angle);
        return {
            x: p.x,
            y: p.y * cos - p.z * sin,
            z: p.y * sin + p.z * cos
        };
    }
    
    rotateY(p, angle) {
        const cos = Math.cos(angle);
        const sin = Math.sin(angle);
        return {
            x: p.x * cos + p.z * sin,
            y: p.y,
            z: -p.x * sin + p.z * cos
        };
    }
    
    draw() {
        const ctx = this.ctx;
        
        // 清空画布
        ctx.clearRect(0, 0, this.width, this.height);
        
        // 绘制 3D 网格
        this.draw3DGrid(false);
        this.draw3DGrid(true);
        
        // 绘制 3D 形状
        this.draw3DShape();
        
        // 绘制基向量
        this.draw3DBasisVectors();
        
        // 绘制坐标轴
        this.draw3DAxes();
    }
    
    draw3DGrid(transformed) {
        const ctx = this.ctx;
        const range = 3;
        const step = 1;
        
        ctx.strokeStyle = transformed ? 'rgba(102, 126, 234, 0.2)' : 'rgba(200, 200, 200, 0.2)';
        ctx.lineWidth = transformed ? 1.5 : 0.5;
        
        // XY 平面网格 (z = 0)
        for (let i = -range; i <= range; i += step) {
            // 沿 X 方向的线
            ctx.beginPath();
            for (let x = -range; x <= range; x += 0.2) {
                let p = { x: x, y: i, z: 0 };
                if (transformed) {
                    p = this.transformPoint(p.x, p.y, p.z);
                }
                const proj = this.project3D(p.x, p.y, p.z);
                if (x === -range) {
                    ctx.moveTo(proj.x, proj.y);
                } else {
                    ctx.lineTo(proj.x, proj.y);
                }
            }
            ctx.stroke();
            
            // 沿 Y 方向的线
            ctx.beginPath();
            for (let y = -range; y <= range; y += 0.2) {
                let p = { x: i, y: y, z: 0 };
                if (transformed) {
                    p = this.transformPoint(p.x, p.y, p.z);
                }
                const proj = this.project3D(p.x, p.y, p.z);
                if (y === -range) {
                    ctx.moveTo(proj.x, proj.y);
                } else {
                    ctx.lineTo(proj.x, proj.y);
                }
            }
            ctx.stroke();
        }
    }
    
    draw3DShape() {
        const ctx = this.ctx;
        
        // 绘制一个立方体
        const size = 1;
        const vertices = [
            { x: size, y: size, z: size },
            { x: -size, y: size, z: size },
            { x: -size, y: -size, z: size },
            { x: size, y: -size, z: size },
            { x: size, y: size, z: -size },
            { x: -size, y: size, z: -size },
            { x: -size, y: -size, z: -size },
            { x: size, y: -size, z: -size }
        ];
        
        const edges = [
            [0, 1], [1, 2], [2, 3], [3, 0], // 前面
            [4, 5], [5, 6], [6, 7], [7, 4], // 后面
            [0, 4], [1, 5], [2, 6], [3, 7]  // 连接边
        ];
        
        // 原始立方体
        this.drawCube(vertices, edges, 'rgba(255, 182, 193, 0.5)', false);
        
        // 变换后的立方体
        this.drawCube(vertices, edges, 'rgba(118, 75, 162, 0.8)', true);
    }
    
    drawCube(vertices, edges, color, transformed) {
        const ctx = this.ctx;
        
        // 变换顶点
        const transformedVertices = vertices.map(v => {
            if (transformed) {
                return this.transformPoint(v.x, v.y, v.z);
            }
            return v;
        });
        
        // 投影到 2D
        const projected = transformedVertices.map(v => this.project3D(v.x, v.y, v.z));
        
        // 绘制边
        ctx.strokeStyle = color;
        ctx.lineWidth = transformed ? 3 : 1.5;
        
        edges.forEach(([i, j]) => {
            ctx.beginPath();
            ctx.moveTo(projected[i].x, projected[i].y);
            ctx.lineTo(projected[j].x, projected[j].y);
            ctx.stroke();
        });
        
        // 绘制顶点
        ctx.fillStyle = color;
        projected.forEach(p => {
            ctx.beginPath();
            ctx.arc(p.x, p.y, transformed ? 4 : 2, 0, Math.PI * 2);
            ctx.fill();
        });
    }
    
    draw3DBasisVectors() {
        const ctx = this.ctx;
        
        // X 轴基向量（红色）
        const iHat = this.transformPoint(2, 0, 0);
        this.draw3DVector(0, 0, 0, iHat.x, iHat.y, iHat.z, '#e74c3c', 'x̂');
        
        // Y 轴基向量（绿色）
        const jHat = this.transformPoint(0, 2, 0);
        this.draw3DVector(0, 0, 0, jHat.x, jHat.y, jHat.z, '#2ecc71', 'ŷ');
        
        // Z 轴基向量（蓝色）
        const kHat = this.transformPoint(0, 0, 2);
        this.draw3DVector(0, 0, 0, kHat.x, kHat.y, kHat.z, '#3498db', 'ẑ');
    }
    
    draw3DVector(x1, y1, z1, x2, y2, z2, color, label) {
        const ctx = this.ctx;
        const start = this.project3D(x1, y1, z1);
        const end = this.project3D(x2, y2, z2);
        
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = 4;
        
        ctx.beginPath();
        ctx.moveTo(start.x, start.y);
        ctx.lineTo(end.x, end.y);
        ctx.stroke();
        
        // 箭头
        const angle = Math.atan2(end.y - start.y, end.x - start.x);
        const arrowSize = 12;
        
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
    
    draw3DAxes() {
        const ctx = this.ctx;
        const length = 5;
        
        ctx.strokeStyle = 'rgba(100, 100, 100, 0.3)';
        ctx.lineWidth = 1;
        
        // X 轴
        const xStart = this.project3D(-length, 0, 0);
        const xEnd = this.project3D(length, 0, 0);
        ctx.beginPath();
        ctx.moveTo(xStart.x, xStart.y);
        ctx.lineTo(xEnd.x, xEnd.y);
        ctx.stroke();
        
        // Y 轴
        const yStart = this.project3D(0, -length, 0);
        const yEnd = this.project3D(0, length, 0);
        ctx.beginPath();
        ctx.moveTo(yStart.x, yStart.y);
        ctx.lineTo(yEnd.x, yEnd.y);
        ctx.stroke();
        
        // Z 轴
        const zStart = this.project3D(0, 0, -length);
        const zEnd = this.project3D(0, 0, length);
        ctx.beginPath();
        ctx.moveTo(zStart.x, zStart.y);
        ctx.lineTo(zEnd.x, zEnd.y);
        ctx.stroke();
    }
}
