+++
title = "Similar approach for allowed_host ip whitelist filtering in django, but in fastapi"
date = "2025-12-02T09:22:38.006590"
slug = "similar-approach-for-allowed_host-ip-whitelist-filtering-in-django,-but-in-fastapi"
description = "When developing web applications, it's crucial to ensure that only trusted clients can access your APIs. In Django, you might be familiar with the `ALLOWED_HOSTS` setting to filter incoming requests based on their IP addresses. FastAPI,..."
+++

When developing web applications, it's crucial to ensure that only trusted clients can access your APIs. In Django, you might be familiar with the `ALLOWED_HOSTS` setting to filter incoming requests based on their IP addresses. FastAPI, being a modern web framework, provides a flexible way to implement similar IP whitelist filtering. This tutorial will guide you through the process of setting up IP filtering in FastAPI.

## Why This Happens

IP whitelisting is a security measure that restricts access to your application based on the client's IP address. This is important for preventing unauthorized access and mitigating potential attacks. In FastAPI, you can implement this by creating middleware that checks the incoming request's IP against a predefined list of allowed IPs.

## Step-by-step Solution

### Step 1: Install FastAPI and Uvicorn

If you haven't already set up FastAPI, you need to install it along with Uvicorn, an ASGI server for running FastAPI applications.

```bash
pip install fastapi uvicorn
```

### Step 2: Create the Middleware

You will need to create a middleware that checks the client's IP address against a whitelist. Here's how you can do it:

```python
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class IPWhitelistMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, allowed_ips: list):
        super().__init__(app)
        self.allowed_ips = allowed_ips

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        if client_ip not in self.allowed_ips:
            raise HTTPException(status_code=403, detail="Forbidden: Your IP is not allowed")
        response = await call_next(request)
        return response

# Initialize the FastAPI app
app = FastAPI()

# Define your allowed IPs
allowed_ips = ["192.168.1.1", "203.0.113.5"]

# Add the middleware to the app
app.add_middleware(IPWhitelistMiddleware, allowed_ips=allowed_ips)
```

### Step 3: Create Your Endpoints

Now that the middleware is set up, you can create your API endpoints. Here's a simple example:

```python
@app.get("/")
async def read_root():
    return {"message": "Welcome to the API!"}

@app.get("/secure-data")
async def read_secure_data():
    return {"data": "This is secure data only for allowed IPs."}
```

### Step 4: Run Your Application

You can run your FastAPI application using Uvicorn. Open your terminal and execute:

```bash
uvicorn main:app --reload
```

Replace `main` with the name of your Python file if it's different.

## Example Variation

You might want to allow a range of IP addresses or use CIDR notation for more complex filtering. You can modify the middleware to handle this:

```python
import ipaddress

class IPWhitelistMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, allowed_ips: list):
        super().__init__(app)
        self.allowed_ips = [ipaddress.ip_network(ip) for ip in allowed_ips]

    async def dispatch(self, request: Request, call_next):
        client_ip = ipaddress.ip_address(request.client.host)
        if not any(client_ip in network for network in self.allowed_ips):
            raise HTTPException(status_code=403, detail="Forbidden: Your IP is not allowed")
        response = await call_next(request)
        return response

# Define your allowed IPs using CIDR notation
allowed_ips = ["192.168.1.0/24", "203.0.113.0/24"]
```

## Common Errors & Fixes

1. **403 Forbidden Error**: This error indicates that the client's IP is not in the whitelist. Ensure that the IPs are correctly configured in the `allowed_ips` list.

2. **IP Address Format Issues**: Make sure that the IP addresses are in the correct format. If using CIDR notation, ensure it is correctly defined.

3. **Middleware Not Applied**: If the middleware is not functioning, double-check that it has been added to the FastAPI app correctly.

## Cheat Sheet Summary

- **Install FastAPI and Uvicorn**:
  ```bash
  pip install fastapi uvicorn
  ```

- **Create Middleware**:
  ```python
  class IPWhitelistMiddleware(BaseHTTPMiddleware):
      def __init__(self, app: FastAPI, allowed_ips: list):
          ...
  ```

- **Add Middleware to FastAPI**:
  ```python
  app.add_middleware(IPWhitelistMiddleware, allowed_ips=["192.168.1.1", "203.0.113.5"])
  ```

- **Run the Application**:
  ```bash
  uvicorn main:app --reload
  ```

- **Handle IP Ranges**:
  Use `ipaddress` module to handle CIDR notation for IP ranges.

By following this tutorial, you should now have a basic understanding of how to implement IP whitelist filtering in FastAPI, ensuring that your application is more secure against unauthorized access.
