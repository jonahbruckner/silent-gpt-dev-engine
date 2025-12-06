+++
title = "Deploying Odoo 18 (Docker/Dockploy): Container crash or 502 Bad Gateway when using custom odoo.conf to pre-configure DB"
date = "2025-12-02T14:17:00.482308"
slug = "deploying-odoo-18-docker-dockploy-container-crash-or-502-bad-gateway-when-using-custom-odoo-conf-to-pre-configure-db"
description = "Deploying Odoo 18 using Docker can lead to issues such as container crashes or 502 Bad Gateway errors, especially when using a custom `odoo.conf` file to pre-configure the database. This micro-tutorial will help you understand why these..."
+++

Deploying Odoo 18 using Docker can lead to issues such as container crashes or 502 Bad Gateway errors, especially when using a custom `odoo.conf` file to pre-configure the database. This micro-tutorial will help you understand why these issues occur and provide a step-by-step solution to resolve them.

## Why This Happens

When deploying Odoo in a Docker container, the application relies on the configuration specified in the `odoo.conf` file. If there are errors in this configuration, such as incorrect database credentials, misconfigured ports, or missing parameters, the Odoo server may fail to start, leading to a container crash or a 502 Bad Gateway error when trying to access the application. 

Common causes include:
- Incorrect database connection settings.
- Missing or incorrect parameters in the `odoo.conf`.
- Network issues between the Odoo container and the database container.

## Step-by-step Solution

### Step 1: Verify Your Docker Setup

Ensure you have Docker and Docker Compose installed correctly. You can check this by running:

```bash
docker --version
docker-compose --version
```

### Step 2: Create a Custom `odoo.conf`

Create a custom `odoo.conf` file with the necessary configurations. Here’s a basic example:

```ini
[options]
; This is the main configuration file for Odoo
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo_password
addons_path = /mnt/extra-addons
logfile = /var/log/odoo/odoo.log
```

### Step 3: Create a Docker Compose File

Create a `docker-compose.yml` file to define your Odoo and PostgreSQL services:

```yaml
version: '3.1'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: odoo
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo_password
    volumes:
      - db_data:/var/lib/postgresql/data

  web:
    image: odoo:18
    depends_on:
      - db
    ports:
      - "8069:8069"
    volumes:
      - ./odoo.conf:/etc/odoo/odoo.conf
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo_password
      - DB_PORT=5432

volumes:
  db_data:
```

### Step 4: Start the Services

Run the following command to start your Odoo and PostgreSQL containers:

```bash
docker-compose up -d
```

### Step 5: Check Logs for Errors

If you encounter a crash or a 502 Bad Gateway error, check the logs of the Odoo container to identify the issue:

```bash
docker-compose logs web
```

Look for any error messages related to database connection or configuration issues.

### Step 6: Test the Connection

Once the containers are up and running, access Odoo by navigating to `http://localhost:8069` in your web browser. If everything is configured correctly, you should see the Odoo setup screen.

## Example Variation

If you want to customize the Odoo installation further, consider adding additional addons or changing the database settings. For example, if you want to use a different database name, modify the `POSTGRES_DB` in the `docker-compose.yml` file and update the `db_name` in the `odoo.conf` accordingly.

```ini
db_name = my_custom_db
```

## Common Errors & Fixes

### Error: 502 Bad Gateway

- **Cause**: Odoo is not running or is unreachable.
- **Fix**: Check the Odoo container logs for errors. Ensure that the database is running and accessible.

### Error: Container Crash

- **Cause**: Incorrect configuration in `odoo.conf`.
- **Fix**: Review the `odoo.conf` file for typos or incorrect parameters. Ensure that the database credentials match those in the PostgreSQL service.

### Error: Database Connection Error

- **Cause**: Incorrect database host or credentials.
- **Fix**: Ensure that the `db_host`, `db_user`, and `db_password` in `odoo.conf` match the environment variables set in the `docker-compose.yml` file.

## Cheat Sheet Summary

- **Verify Docker Installation**: Ensure Docker and Docker Compose are installed.
- **Custom `odoo.conf`**: Create a configuration file with correct database settings.
- **Docker Compose Setup**: Define services for Odoo and PostgreSQL in `docker-compose.yml`.
- **Start Services**: Use `docker-compose up -d` to start the containers.
- **Check Logs**: Use `docker-compose logs web` to troubleshoot issues.
- **Access Odoo**: Navigate to `http://localhost:8069` to access the application.

By following these steps, you should be able to successfully deploy Odoo 18 with Docker and resolve any issues related to container crashes or 502 Bad Gateway errors when using a custom `odoo.conf`. Happy coding!
