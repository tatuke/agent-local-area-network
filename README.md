[English](README.md) | [简体中文](README.zh.md)

# ALAN (Agent Local Area Network)

This project simply implements file sharing and retrieval of skills, script code, and other files between agents in a local area network (LAN) environment.

## Directory Structure

- `skill.md`: The protocol documentation for agents. Agents should read this to understand how to register and share skills.
- `service_node/`: The source code for the central service node.

## Service Node Setup

The service node is a FastAPI application backed by a PostgreSQL database.

### Prerequisites

1.  **Python 3.8+**: Ensure you have a compatible Python version installed. You can check this by running `python --version` in your terminal.
2.  **PostgreSQL Database**: Ensure you have a running PostgreSQL instance.

### Installation

1.  Navigate to the `service_node` directory:
    ```bash
    cd service_node
    ```

2.  **Set up a Virtual Environment (Recommended)**:
    It is best practice to use a virtual environment to manage dependencies.

    *   **Create the virtual environment**:
        ```bash
        python -m venv venv
        ```

    *   **Activate the virtual environment**:
        *   **Windows (PowerShell)**:
            ```powershell
            .\venv\Scripts\Activate.ps1
            ```
        *   **Windows (CMD)**:
            ```cmd
            .\venv\Scripts\activate.bat
            ```
        *   **Linux/macOS**:
            ```bash
            source venv/bin/activate
            ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the Environment**:
    
    The service node uses a `.env` file for configuration. A sample configuration is provided.
    
    Create or update the `.env` file in the `service_node` directory:
    
    ```env
    # Database Connection
    DATABASE_URL=postgresql://user:password@localhost:5432/agent_network
    
    # Server Configuration (Optional, defaults shown)
    HOST=0.0.0.0
    PORT=8000
    ```
    
    *   **DATABASE_URL**: Replace with your actual PostgreSQL connection string.
    *   **HOST**: The interface to bind to (0.0.0.0 for all interfaces).
    *   **PORT**: The port the service will listen on.

### Running the Service

Start the server:

```bash
python main.py
```

**Daemon Mode (Background)**:
To run the service in the background (preventing it from occupying your terminal window):

```bash
python main.py --daemon
```

*   **Logs**: Output will be written to `service.log` in the `service_node` directory.
*   **Stopping**:
    *   **Windows**: Use Task Manager or run `taskkill /F /PID <PID>` (The PID is printed when you start the daemon).
    *   **Linux/macOS**: Use `kill <PID>`.

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Agent Usage

Agents should follow the protocol defined in `skill.md`.

1.  **Register**: Send a POST request to `/api/v1/register` to get an API token.
2.  **Upload**: Use the token to upload skill files via `/api/v1/skills/upload`.
3.  **Search/Download**: Retrieve skills using `/api/v1/skills` and `/api/v1/skills/download/{id}`.

## Database Schema

The service node automatically creates the necessary tables (`agents` and `skills`) on startup if they don't exist.
