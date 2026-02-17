# frontend/Dockerfile
# Build
FROM node:20-alpine AS build
WORKDIR /app

ARG VITE_API_BASE=""
ENV VITE_API_BASE=${VITE_API_BASE}

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# Production image
FROM nginx:stable-alpine AS production
WORKDIR /usr/share/nginx/html
RUN rm -rf ./*

COPY --from=build /app/dist/ .

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]