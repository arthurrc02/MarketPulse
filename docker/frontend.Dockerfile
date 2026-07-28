# syntax=docker/dockerfile:1.7
#
# Imagem do frontend (React + Vite). O contexto de build é a RAIZ do
# repositório, para que o estágio de produção possa copiar docker/nginx.conf.

# ---------------------------------------------------------------------------
# deps — instala node_modules a partir do lockfile
# ---------------------------------------------------------------------------
FROM node:22-alpine AS deps

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# ---------------------------------------------------------------------------
# development — servidor de desenvolvimento do Vite com HMR
# ---------------------------------------------------------------------------
FROM deps AS development

COPY frontend/ ./
EXPOSE 5173
CMD ["npm", "run", "dev"]

# ---------------------------------------------------------------------------
# builder — bundle de produção
# ---------------------------------------------------------------------------
FROM deps AS builder

ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------------------
# production — assets estáticos servidos pelo Nginx
# ---------------------------------------------------------------------------
FROM nginx:1.27-alpine AS production

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --spider http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
