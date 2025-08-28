# Stage 1: Build the JAR
FROM maven:3.9.9-eclipse-temurin-17 AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn clean package -DskipTests

# Stage 2: Run the app
FROM eclipse-temurin:17-jre-alpine
RUN addgroup -S spring && adduser -S spring -G spring
WORKDIR /app
COPY --from=builder /app/target/history-service-1.0.0.jar app.jar
RUN chown -R spring:spring /app
USER spring
EXPOSE 8081
ENTRYPOINT ["java","-jar","app.jar"]

