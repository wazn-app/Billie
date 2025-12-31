# Stage 1: Build Stage - Build the React application
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files for dependency installation
COPY package.json package-lock.json ./

# Install dependencies with npm ci for reproducible builds
RUN npm ci

# Copy all source files
COPY . .

# Build the React application
RUN npm run build

# Stage 2: Production Stage - Serve with nginx
FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from builder stage to nginx html directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80 for HTTP
EXPOSE 80

# Use default nginx command
CMD ["nginx", "-g", "daemon off;"]