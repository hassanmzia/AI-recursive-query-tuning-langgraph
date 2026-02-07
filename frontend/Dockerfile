FROM node:20-alpine AS build

WORKDIR /app

ARG REACT_APP_GATEWAY_URL=http://172.168.1.95:3083
ARG REACT_APP_WS_URL=ws://172.168.1.95:3083
ARG REACT_APP_LANGFUSE_URL=http://172.168.1.95:3084

ENV REACT_APP_GATEWAY_URL=$REACT_APP_GATEWAY_URL
ENV REACT_APP_WS_URL=$REACT_APP_WS_URL
ENV REACT_APP_LANGFUSE_URL=$REACT_APP_LANGFUSE_URL

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
