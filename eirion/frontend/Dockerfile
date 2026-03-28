# Stage 1: Build Node.js React application
FROM node:18-alpine AS builder
WORKDIR /app

# Install dependencies rapidly leveraging cache
COPY package*.json ./
RUN npm install

# Copy source and build static bundle
COPY . .
RUN npm run build

# Stage 2: Serve static files via Nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
