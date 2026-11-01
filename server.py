import os
import http.server
import socketserver
import urllib.request
import urllib.error
import email.parser

PORT = 8080
UPLOAD_DIR = os.path.join(os.getcwd(), "temp_uploads")

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class CloudUploadHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/upload':
            try:
                # قراءة محتوى الطلب (Multipart Form Data) بالطريقة الحديثة
                content_type = self.headers.get('Content-Type', '')
                if 'multipart/form-data' not in content_type:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"<script>alert('Invalid Request'); window.history.back();</script>")
                    return

                content_length = int(self.headers.get('Content-Length', 0))
                body_data = self.rfile.read(content_length)

                # تحليل البيانات المرفوعة باستخدام email.parser القياسي
                header_data = f"Content-Type: {content_type}\n\n".encode('utf-8') + body_data
                msg = email.parser.BytesParser().parsebytes(header_data)

                file_item = None
                filename = "file.apk"

                for part in msg.walk():
                    disposition = part.get("Content-Disposition", "")
                    if 'filename="' in disposition:
                        # استخراج اسم الملف
                        for param in disposition.split(';'):
                            if 'filename=' in param:
                                filename = param.split('=')[1].strip('"\'')
                        file_item = part.get_payload(decode=True)
                        break

                if file_item:
                    temp_filepath = os.path.join(UPLOAD_DIR, os.path.basename(filename))
                    
                    with open(temp_filepath, 'wb') as output_file:
                        output_file.write(file_item)
                    
                    # رفع الملف إلى Catbox.moe
                    cloud_url = "https://catbox.moe/user/api.php"
                    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
                    data = []
                    data.append(f'--{boundary}\r\n'.encode('utf-8'))
                    data.append(b'Content-Disposition: form-data; name="reqtype"\r\n\r\nfileupload\r\n')
                    data.append(f'--{boundary}\r\n'.encode('utf-8'))
                    data.append(f'Content-Disposition: form-data; name="fileToUpload"; filename="{filename}"\r\n'.encode('utf-8'))
                    data.append(b'Content-Type: application/octet-stream\r\n\r\n')
                    data.append(file_item)
                    data.append(f'\r\n--{boundary}--\r\n'.encode('utf-8'))
                    
                    body = b''.join(data)
                    req = urllib.request.Request(cloud_url, data=body, method='POST')
                    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
                    
                    try:
                        with urllib.request.urlopen(req) as response:
                            download_url = response.read().decode('utf-8').strip()
                    except Exception as e:
                        download_url = ""
                    
                    # حذف الملف المؤقت فوراً لتفريغ مساحة الهاتف
                    if os.path.exists(temp_filepath):
                        os.remove(temp_filepath)
                    
                    if download_url.startswith("https://"):
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        script = f"<script>localStorage.setItem('lastCloudUrl', '{download_url}'); alert('تم الرفع للسحابة بنجاح!'); window.location.href='/games.html';</script>"
                        self.wfile.write(script.encode('utf-8'))
                    else:
                        self.send_response(500)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(b"<script>alert('Fashal al-raf3'); window.history.back();</script>")
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(b"<script>alert('No file selected'); window.history.back();</script>")
            except Exception as ex:
                self.send_response(500)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(b"<script>alert('Server Error'); window.history.back();</script>")
        else:
            super().do_GET()

with socketserver.TCPServer(("0.0.0.0", PORT), CloudUploadHandler) as httpd:
    print(f"Server running on: http://localhost:{PORT}")
    httpd.serve_forever()
