package com.flightontime.flightapi.domain.flight.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Future;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.Instant;

public record FlightRequest(
        @NotBlank
        @JsonProperty("companhia")
        String airline,

        @NotBlank
        @JsonProperty("origem")
        String origin,

        @NotBlank
        @JsonProperty("destino")
        String destination,

        @JsonProperty("data_partida")
        @Future
        @NotNull Instant departureDate
) {
}
