# Stage 1: Build
FROM arm64v8/python:3.11-slim AS builder

# Set the working directory in the container
WORKDIR /app

# Install pipenv
RUN pip install --no-cache-dir pipenv

# Install system dependencies for OpenCV
RUN apt update && apt install -y libgl1-mesa-glx libglib2.0-0

# Copy Pipfile and Pipfile.lock to install dependencies
COPY Pipfile Pipfile.lock ./

# Install the dependencies using pipenv
RUN pipenv install --deploy --ignore-pipfile


# Copy the pipenv executable and dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/pipenv /usr/local/bin/pipenv
COPY --from=builder /app /app

# Copy the rest of the application code into the container
COPY . .

# Expose port 8000
EXPOSE 8000

# Specify the command to run the application
CMD ["pipenv", "run", "python", "main.py"]
