# ── EIRION Frontend — Production Dockerfile ───────────────────────────────────
# Multi-stage: Node build → nginx static serve
# ─────────────────────────────────────────────────────────────────────────────

# Stage 1: Build
FROM node:20-slim AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Pass API URL as build arg (can be overridden with --build-arg)
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine AS runner

# Copy build output
COPY --from=builder /app/dist /usr/share/nginx/html

# nginx config for React Router (SPA fallback to index.html)
RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
    location /api/ {\n\
        return 404;\n\
    }\n\
    gzip on;\n\
    gzip_types text/plain text/css application/javascript application/json;\n\
    gzip_min_length 1000;\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
