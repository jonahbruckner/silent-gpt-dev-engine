+++
title = "Multiple Datasources with Docker Compose, Spring Boot, and Flyway"
date = "2025-12-02T14:16:32.537936"
slug = "multiple-datasources-with-docker-compose-spring-boot-and-flyway"
description = "When building applications that require multiple databases, managing the configuration and migrations can be challenging. This micro-tutorial will guide you through setting up multiple datasources in a Spring Boot application using Docke..."
+++

When building applications that require multiple databases, managing the configuration and migrations can be challenging. This micro-tutorial will guide you through setting up multiple datasources in a Spring Boot application using Docker Compose and Flyway for database migrations. 

## Why this happens

Spring Boot simplifies database connectivity but configuring multiple datasources requires additional setup. Each datasource needs its own configuration, and managing migrations with Flyway can become complex when multiple databases are involved. Docker Compose adds another layer, allowing you to orchestrate multiple containers for your application and databases seamlessly.

## Step-by-step solution

### Step 1: Set up your Spring Boot application

First, create a new Spring Boot application. You can use Spring Initializr to bootstrap your project with the necessary dependencies. Make sure to include:

- Spring Web
- Spring Data JPA
- Flyway Migration
- Your preferred database driver (e.g., PostgreSQL, MySQL)

### Step 2: Configure multiple datasources

In your `application.yml`, define the configurations for each datasource. Here’s an example configuration for two PostgreSQL datasources:

```yaml
spring:
  datasource:
    primary:
      url: jdbc:postgresql://db1:5432/primarydb
      username: user1
      password: pass1
      driver-class-name: org.postgresql.Driver
    secondary:
      url: jdbc:postgresql://db2:5432/secondarydb
      username: user2
      password: pass2
      driver-class-name: org.postgresql.Driver

  flyway:
    locations: 
      - classpath:db/migration/primary
      - classpath:db/migration/secondary
```

### Step 3: Create configuration classes

You need to create configuration classes for each datasource. Here’s how to do it:

```java
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.autoconfigure.orm.jpa.EntityManagerFactoryBuilder;
import org.springframework.boot.autoconfigure.orm.jpa.HibernatePropertiesCustomizer;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.orm.jpa.EntityManagerFactoryBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.orm.jpa.JpaTransactionManager;
import org.springframework.orm.jpa.LocalContainerEntityManagerFactoryBean;
import org.springframework.transaction.PlatformTransactionManager;

import javax.persistence.EntityManagerFactory;

@Configuration
@EnableJpaRepositories(
        basePackages = "com.example.repository.primary",
        entityManagerFactoryRef = "primaryEntityManagerFactory",
        transactionManagerRef = "primaryTransactionManager"
)
public class PrimaryDataSourceConfig {

    @Primary
    @Bean(name = "primaryEntityManagerFactory")
    public LocalContainerEntityManagerFactoryBean primaryEntityManagerFactory(
            EntityManagerFactoryBuilder builder) {
        return builder
                .dataSource(primaryDataSource())
                .packages("com.example.model.primary")
                .persistenceUnit("primary")
                .build();
    }

    @Primary
    @Bean(name = "primaryTransactionManager")
    public PlatformTransactionManager primaryTransactionManager(
            @Qualifier("primaryEntityManagerFactory") EntityManagerFactory primaryEntityManagerFactory) {
        return new JpaTransactionManager(primaryEntityManagerFactory);
    }

    @Bean(name = "primaryDataSource")
    @ConfigurationProperties("spring.datasource.primary")
    public DataSource primaryDataSource() {
        return DataSourceBuilder.create().build();
    }
}
```

Repeat the above for the secondary datasource, changing the names accordingly.

### Step 4: Set up Docker Compose

Create a `docker-compose.yml` file to define your application and databases. Here’s an example:

```yaml
version: '3.8'
services:
  app:
    image: your-spring-boot-app
    build: .
    ports:
      - "8080:8080"
    depends_on:
      - db1
      - db2

  db1:
    image: postgres:latest
    environment:
      POSTGRES_DB: primarydb
      POSTGRES_USER: user1
      POSTGRES_PASSWORD: pass1
    ports:
      - "5432:5432"

  db2:
    image: postgres:latest
    environment:
      POSTGRES_DB: secondarydb
      POSTGRES_USER: user2
      POSTGRES_PASSWORD: pass2
    ports:
      - "5433:5432"
```

### Step 5: Create Flyway migration scripts

Organize your Flyway migration scripts in the specified locations in your `application.yml`. For example, create a directory structure like this:

```
src/main/resources/db/migration/primary
src/main/resources/db/migration/secondary
```

Add your migration scripts (e.g., `V1__Create_table.sql`) in the respective directories.

## Example variation

You can modify the example to use different databases like MySQL or Oracle by changing the datasource configurations and the Docker images. For instance, replace the PostgreSQL images with MySQL images and adjust the connection URLs accordingly.

## Common errors & fixes

1. **Error: `Cannot create JDBC driver of class...`**
   - **Fix:** Ensure that you have the correct database driver dependency in your `pom.xml` or `build.gradle`.

2. **Error: `Flyway migration failed...`**
   - **Fix:** Check your migration scripts for syntax errors or ensure that the database is accessible.

3. **Error: `DataSource not found`**
   - **Fix:** Make sure the datasource configuration classes are correctly annotated and scanned by Spring.

## Cheat sheet summary

- **Multiple Datasources:** Define separate configurations for each datasource in `application.yml`.
- **Configuration Classes:** Create configuration classes for each datasource with `@EnableJpaRepositories`.
- **Docker Compose:** Use `docker-compose.yml` to define your application and database services.
- **Flyway Migrations:** Organize migration scripts in specified locations for each datasource.

By following this guide, you should be able to set up a Spring Boot application with multiple datasources, managed by Docker Compose and Flyway for seamless migrations. Happy coding!
