# Flight On Time API

A Flight on Time é uma aplicação Back-End (REST) desenvolvida em Java com o framework Spring Boot. O objetivo principal
é fornecer previsões sobre o status de voos (atrasado ou pontual) utilizando o modelo de Data Science integrado via
microserviço.

## Processo de Previsão (Dados -> Modelo -> Previsão)

O fluxo da aplicação segue três etapas principais:

1. **Entrada de Dados**: A API Java recebe via JSON os detalhes do voo (companhia, aeroportos e data de partida).
2. **Integração DS:** O serviço (`FlightPredictionService`) comunica-se via `RestClient` com o microserviço de Data Science.
3. **Resposta:** A API padroniza o retorno com a previsão, a probabilidade decimal, a cor do semáforo de risco e os detalhes utilizados.

## Ferramentas e Dependências

- **Linguagem:** Java 21
- **Framework:** Spring Boot 3.5.4
- **Banco de Dados**: MySQL com migrações via Flyway
- **Documentação**: SpringDoc OpenAPI (Swagger)
- **Resiliência**: Resilience4j (Circuit Breaker)

## Como Executar o Projeto Localmente

**Pré-requisitos**

- Java 21 e Maven (ou use o `./mvnw` incluso)
- MySQL rodando localmente
- O microserviço de Data Science em execução

**Passos**

1. **Configurar o Banco de Dados**: Execute as migrações presentes em `src/main/resources/db/migration` para criar
   as tabelas de usuários, perfis, aeroportos e companhias aéreas.

2. **Configurar as variáveis de ambiente**: Defina as credenciais do banco e a URL dos serviços:

| Variável | Descrição |
|----------|-----------|
| `FLIGHTONTIME_DATASOURCE_DEV` | URL do MySQL (ex: `jdbc:mysql://localhost:3306/flightontime`) |
| `FLIGHTONTIME_USERNAME_DEV` | Usuário do banco de dados |
| `FLIGHTONTIME_PASSWORD_DEV` | Senha do banco de dados |
| `FLIGHTONTIME_DATASCIENCE_BASEURL` | URL do motor de IA (ex: `http://localhost:8000`) |
| `FLIGHTONTIME_JWT_SECRET_DEV` | Secret para geração de tokens JWT |
| `FLIGHTONTIME_PATH_DEV` | Context path da aplicação (opcional) |

3. **Executar a API**:

```bash
./mvnw spring-boot:run
```

4. **Acesso:** A documentação interativa estará disponível em `/swagger-ui.html`.

## Exemplos de Uso (Endpoint `/predict`)

O serviço expõe um endpoint `POST` que valida a presença de todos os campos obrigatórios antes de processar a consulta.

### 1. Exemplo de Voo Pontual (Risco Baixo)

**Requisição:**

```json
{
  "companhia": "GOL",
  "origem": "GIG",
  "destino": "GRU",
  "data_partida": "2025-11-10T14:30:00Z"
}
```

**Resposta (Probabilidade < 0.35):**

```json
{
  "previsao": "🟢 PONTUAL",
  "probabilidade": 0.15,
  "cor": "green",
  "detalhes": {
    "distancia": 350.0,
    "chuva": 0.0,
    "vento": 5.2,
    "fonte_clima": "✅ LIVE (OpenMeteo)"
  }
}
```

### 2. Exemplo de Voo Atrasado (Risco Alto)

**Requisição (Feriado de Natal com mau tempo):**

```json
{
  "companhia": "GOL",
  "origem": "GRU",
  "destino": "REC",
  "data_partida": "2025-12-25T14:30:00Z"
}
```

**Resposta (Probabilidade > 0.70):**

```json
{
  "previsao": "🔴 ATRASO PROVÁVEL",
  "probabilidade": 0.72,
  "cor": "red",
  "detalhes": {
    "distancia": 2689.0,
    "chuva": 12.5,
    "vento": 18.3,
    "fonte_clima": "✅ LIVE (OpenMeteo)"
  }
}
```

### 3. Exemplo de Erro de Validação

Se um campo obrigatório como `data_partida` for omitido, a API retorna um erro padronizado:

**Resposta (400 Bad Request):**

```json
[
  {
    "campo": "data_partida",
    "mensagem": "data_partida não deve ser nulo"
  }
]
```