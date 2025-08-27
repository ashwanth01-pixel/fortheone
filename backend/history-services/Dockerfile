# ============================
# Stage 1: Build the JAR
# ============================
FROM maven:3.9.9-eclipse-temurin-17 AS builder

# Set working directory
WORKDIR /app

# Copy pom.xml and download dependencies (for caching)
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Copy the rest of the source code
COPY src ./src

# Package the application (skip tests for faster build, remove -DskipTests if you want tests)
RUN mvn clean package -DskipTests

# ============================
# Stage 2: Run the app
# ============================
FROM eclipse-temurin:17-jre-alpine

# Create non-root user
RUN addgroup -S spring && adduser -S spring -G spring

WORKDIR /app

# Copy only the built jar from builder stage
COPY --from=builder /app/target/history-service-1.0.0.jar app.jar

# Change ownership
RUN chown -R spring:spring /app
USER spring

# Expose port (default Spring Boot = 8080)
EXPOSE 8081

# Run the JAR
ENTRYPOINT ["java","-jar","app.jar"]

