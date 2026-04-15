# Use official Node 20 slim
FROM node:20-slim

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the code
COPY . .

# Expose Vite's default dev port
EXPOSE 5173

# Run the app in host mode so it's accessible outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
