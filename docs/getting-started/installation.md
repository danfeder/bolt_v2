# Installation

This guide will walk you through the process of installing the Gym Class Rotation Scheduler.

## System Requirements

- **Operating System**: Windows 10+, macOS 10.15+, or Linux
- **Frontend**:
  - Node.js 16+
  - npm 7+
  - 2GB RAM minimum
  - 1GB disk space
- **Backend**:
  - Python 3.9+
  - pip 21+
  - 4GB RAM minimum for scheduling operations

## Installation Options

=== "Standard Installation"

    ## Step 1: Clone the Repository

    ```bash
    git clone https://github.com/example/bolt_v2.git
    cd bolt_v2
    ```

    ## Step 2: Install Backend Dependencies

    ```bash
    cd scheduler-backend
    python -m pip install -r requirements.txt
    ```

    ## Step 3: Install Frontend Dependencies

    ```bash
    cd ..  # Return to the project root
    npm install
    ```

    ## Step 4: Configuration

    Copy the example configuration files:

    ```bash
    cp scheduler-backend/.env.example scheduler-backend/.env
    cp .env.example .env
    ```

    Edit the configuration files as needed.

    ## Step 5: Start the Application

    ```bash
    # Start the backend
    cd scheduler-backend
    python -m app.main

    # In a separate terminal, start the frontend
    cd bolt_v2  # Navigate to the project root
    npm run dev
    ```

    Your application should now be running at [http://localhost:5173](http://localhost:5173)

=== "Docker Installation"

    ## Step 1: Clone the Repository

    ```bash
    git clone https://github.com/example/bolt_v2.git
    cd bolt_v2
    ```

    ## Step 2: Docker Compose

    ```bash
    docker-compose up -d
    ```

    This will build and start both the frontend and backend containers.

    ## Step 3: Access the Application

    Your application should now be running at [http://localhost:5173](http://localhost:5173)

## Verification

To verify your installation:

1. Navigate to [http://localhost:5173](http://localhost:5173) in your browser
2. You should see the Gym Class Rotation Scheduler login page
3. To test the backend, visit [http://localhost:8000/docs](http://localhost:8000/docs) to access the API documentation

## Troubleshooting

If you encounter issues during installation:

- Check that all prerequisites are correctly installed
- Ensure all required ports (5173, 8000) are available
- Verify that the .env configuration files are properly set up

For more detailed troubleshooting, see the [Troubleshooting](../user-guide/troubleshooting.md) section.
