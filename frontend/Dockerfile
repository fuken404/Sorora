# Usar Nginx como servidor web ligero
FROM nginx:alpine

# Copiar la configuración personalizada de Nginx
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
    # Configuración CORS para las APIs \
    location /api/ { \
        proxy_pass http://backend:10000/; \
        proxy_http_version 1.1; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
        proxy_set_header Host $host; \
        proxy_cache_bypass $http_upgrade; \
        # Configuración CORS \
        add_header Access-Control-Allow-Origin * always; \
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always; \
        add_header Access-Control-Allow-Headers "DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization" always; \
        if ($request_method = OPTIONS ) { \
            return 204; \
        } \
    } \
}' > /etc/nginx/conf.d/default.conf

# Copiar los archivos estáticos
COPY index.html /usr/share/nginx/html/
COPY styles.css /usr/share/nginx/html/
COPY app.js /usr/share/nginx/html/

# Exponer el puerto 80
EXPOSE 80

# Nginx arranca automáticamente, no necesitamos CMD