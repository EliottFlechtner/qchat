# Stage 1: Build the frontend
FROM node:20-alpine AS build
WORKDIR /app

# Install dependencies (supports presence/absence of lock file)
COPY package*.json ./
RUN npm ci || npm install

# Copy source
COPY . .

# Allow overriding API/WS URLs at build-time; default to reverse-proxy paths
ARG VITE_API_BASE_URL=/api
ARG VITE_WS_BASE_URL=/ws
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_BASE_URL=$VITE_WS_BASE_URL

# Build static assets
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine AS runtime

# Copy build output to nginx html directory
COPY --from=build /app/dist /usr/share/nginx/html

# Default command (nginx image already defines it)
EXPOSE 80

