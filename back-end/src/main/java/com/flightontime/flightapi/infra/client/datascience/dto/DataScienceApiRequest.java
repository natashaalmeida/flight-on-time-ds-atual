package com.flightontime.flightapi.infra.client.datascience.dto;

import com.fasterxml.jackson.annotation.JsonFormat;

import java.time.Instant;

public record DataScienceApiRequest(
    String companhia,
    String origem,
    String destino,
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'", timezone = "UTC") Instant data_partida
) {}
