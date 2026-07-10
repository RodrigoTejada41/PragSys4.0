FROM node:22-alpine

WORKDIR /bridge

RUN apk add --no-cache git

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY src ./src

ENV WHATSAPP_BRIDGE_PORT=3100
EXPOSE 3100

CMD ["node", "src/server.js"]
