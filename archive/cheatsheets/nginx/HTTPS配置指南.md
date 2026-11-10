> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# HTTPS配置指南

## 问题
如何配置Nginx以支持HTTPS？

## 判断
需要配置Nginx做HTTPS终结，以确保网站通过HTTPS提供服务。

## 规则
1. **安装SSL证书**：
   - 获取SSL证书（如Let's Encrypt）。
   - 将证书文件（如`fullchain.pem`）和私钥文件（如`privkey.pem`）放置在服务器上。

2. **配置Nginx虚拟主机**：
   - 打开Nginx配置文件（通常位于`/etc/nginx/sites-available/`）。
   - 添加或修改虚拟主机配置，启用HTTPS：
     ```nginx
     server {
         listen 443 ssl;
         server_name your_domain.com;

         ssl_certificate /path/to/fullchain.pem;
         ssl_certificate_key /path/to/privkey.pem;

         # 配置其他选项，如SSL协议和加密套件
         ssl_protocols TLSv1.2 TLSv1.3;
         ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
         ssl_prefer_server_ciphers on;

         # 代理设置（如反向代理）
         location / {
             proxy_pass http://backend_server;
             proxy_set_header Host $host;
             proxy_set_header X-Real-IP $remote_addr;
             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
             proxy_set_header X-Forwarded-Proto $scheme;
         }
     }
     ```

3. **启用HTTP到HTTPS重定向**：
   - 在HTTP虚拟主机中添加重定向：
     ```nginx
     server {
         listen 80;
         server_name your_domain.com;
         return 301 https://$host$request_uri;
     }
     ```

4. **测试配置**：
   - 运行`nginx -t`检查配置是否正确。
   - 如果无误，重新加载Nginx配置：
     ```bash
     sudo systemctl reload nginx
     ```

5. **优化**：
   - 启用OCSP stapling以提高安全性：
     ```nginx
     ssl_stapling on;
     ssl_stapling_verify on;
     ```
   - 配置HSTS以强制浏览器使用HTTPS：
     ```nginx
     add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
     ```

## 例外
- 如果使用的是自签名证书，可能需要在客户端信任该证书。
- 如果Nginx后端服务未启用HTTPS，需确保反向代理正确处理协议转换。

## 检查清单
1. 确认证书路径和文件权限正确。
2. 验证Nginx配置无误，且服务已重新加载。
3. 使用浏览器或工具（如`curl --insecure`）测试HTTPS连接。
4. 检查SSL/TLS配置是否符合最佳实践（如使用现代协议和加密套件）。

```markdown
# HTTPS配置指南

## 问题
如何配置Nginx以支持HTTPS？

## 判断
需要配置Nginx做HTTPS终结，以确保网站通过HTTPS提供服务。

## 规则
1. **安装SSL证书**：
   - 获取SSL证书（如Let's Encrypt）。
   - 将证书文件（如`fullchain.pem`）和私钥文件（如`privkey.pem`）放置在服务器上。

2. **配置Nginx虚拟主机**：
   - 打开Nginx配置文件（通常位于`/etc/nginx/sites-available/`）。
   - 添加或修改虚拟主机配置，启用HTTPS：
     ```nginx
     server {
         listen 443 ssl;
         server_name your_domain.com;

         ssl_certificate /path/to/fullchain.pem;
         ssl_certificate_key /path/to/privkey.pem;

         # 配置其他选项，如SSL协议和加密套件
         ssl_protocols TLSv1.2 TLSv1.3;
         ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
         ssl_prefer_server_ciphers on;

         # 代理设置（如反向代理）
         location / {
             proxy_pass http://backend_server;
             proxy_set_header Host $host;
             proxy_set_header X-Real-IP $remote_addr;
             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
             proxy_set_header X-Forwarded-Proto $scheme;
         }
     }
     ```

3. **启用HTTP到HTTPS重定向**：
   - 在HTTP虚拟主机中添加重定向：
     ```nginx
     server {
         listen 80;
         server_name your_domain.com;
         return 301 https://$host$request_uri;
     }
     ```

4. **测试配置**：
   - 运行`nginx -t`检查配置是否正确。
   - 如果无误，重新加载Nginx配置：
     ```bash
     sudo systemctl reload nginx
     ```

5. **优化**：
   - 启用OCSP stapling以提高安全性：
     ```nginx
     ssl_stapling on;
     ssl_stapling_verify on;
     ```
   - 配置HSTS以强制浏览器使用HTTPS：
     ```nginx
     add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
     ```

## 例外
- 如果使用的是自签名证书，可能需要在客户端信任该证书。
- 如果Nginx后端服务未启用HTTPS，需确保反向代理正确处理协议转换。

## 检查清单
1. 确认证书路径和文件权限正确。
2. 验证Nginx配置无误，且服务已重新加载。
3. 使用浏览器或工具（如`curl --insecure`）测试HTTPS连接。
4. 检查SSL/TLS配置是否符合最佳实践（如使用现代协议和加密套件）。
```
