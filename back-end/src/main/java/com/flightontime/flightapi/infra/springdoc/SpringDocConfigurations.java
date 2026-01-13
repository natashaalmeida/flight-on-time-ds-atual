package com.flightontime.flightapi.infra.springdoc;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SpringDocConfigurations {

    @Value("${application.version}")
    private String version;

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .components(new Components()
                        .addSecuritySchemes("bearer-key",
                                new SecurityScheme()
                                        .type(SecurityScheme.Type.HTTP)
                                        .scheme("bearer")
                                        .bearerFormat("JWT")))
                        .info(new Info()
                                .title("Flight On Time API")
                                .version(version)
                                .summary("REST API para previsão de status de voos")
                                .description("""
                                        API Back-End desenvolvida em Java com Spring Boot que fornece previsões sobre o status de voos utilizando modelo de Data Science.

                                        **Stack:** Java 21, Spring Boot 3.5.4, MySQL, Flyway, Resilience4j
                                        """)
                                .contact(new Contact()
                                        .name("Github")
                                        .url("https://github.com/dragoscalin33/flight-on-time-ds/"))
                        .license(new License()
                                .name("MIT")));
    }

}
