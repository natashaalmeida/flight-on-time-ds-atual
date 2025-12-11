# FlightOnTime - Previsão de Atrasos de Voos

## Sobre o Projeto
Este repositório contém o motor de Inteligência Artificial do projeto FlightOnTime, desenvolvido durante a Simulação da No Country.

O objetivo do MVP é fornecer um microserviço capaz de calcular a probabilidade de atraso de voos comerciais no Brasil. O modelo utiliza dados históricos de operações para identificar padrões de risco baseados em companhia aérea, rota, data, horário, distância e **feriados nacionais**.

## Arquitetura e Tecnologias
A solução foi construída com foco em simplicidade de integração e robustez.

* **Linguagem:** Python 3.x
* **Machine Learning:** Scikit-Learn (Random Forest Classifier)
* **API:** FastAPI (Interface para o Back-End Java)
* **Processamento de Dados:** Pandas e Numpy
* **Serialização:** Joblib

## Estrutura do Repositório

* **src/**: Contém o código-fonte principal.
    * `train.py`: Script responsável pelo tratamento de dados e treinamento do modelo.
    * `app.py`: Aplicação web (API) que serve as predições.
* **notebooks/**: Contém os estudos exploratórios e validação das hipóteses de negócio.
* **data/**: Diretório local para armazenamento do dataset (BrFlights2.csv).

## Regra de Negócio (Modelo V3 - Semáforo)
O modelo atual opera com uma lógica de **Risco Escalonado** para apoiar a decisão do usuário:

* **Target:** Um voo é tecnicamente "Atrasado" se a diferença for > 15 minutos.
* **Semáforo de Risco (Probabilidade):**
    * 🟢 **BAIXO (< 40%):** Previsão de Pontualidade.
    * 🟡 **MÉDIO (40% - 60%):** Estado de Alerta (Monitorar).
    * 🔴 **ALTO (> 60%):** Alta probabilidade de Atraso.
* **Métrica Principal:** Priorizamos o Recall (Sensibilidade) de **87%** para garantir alertas de segurança.

## Guia de Instalação e Execução (Local)

### 1. Preparar o Ambiente
Certifique-se de ter o Python instalado. Recomenda-se o uso de um ambiente virtual (venv).

Instale as dependências do projeto (agora inclui a lib `holidays`):
```bash
pip install -r requirements.txt
```

### 2. Treinar o Modelo (Gerar o Cérebro)
Antes de iniciar a API, é necessário processar os dados e gerar o arquivo do modelo (.joblib). Execute o script de treinamento:

```bash
python src/train.py
```
*Isso criará o arquivo `flight_classifier_mvp.joblib` dentro da pasta src.*

### 3. Iniciar a API
Com o modelo gerado, inicie o servidor local:

```bash
python -m uvicorn src.app:app --reload
```
A API estará disponível em: `http://127.0.0.1:8000`

## Documentação da API (Contrato V3)

**Endpoint:** `POST /predict`

**Exemplo de Requisição (JSON):**
```json
{
  "companhia": "AZUL",
  "origem": "Guarulhos",
  "destino": "Recife",
  "data_partida": "2025-12-25T14:30:00",
  "distancia_km": 2100.5
}

```

**Exemplo de Resposta:**
```json
{
  "previsao": "ATRASADO",
  "probabilidade": 0.7221,
  "nivel_risco": "ALTO",
  "mensagem": "Alta probabilidade de atraso (72.2%).",
  "detalles": {
    "is_feriado": true,
    "distancia": 2689.0
  }
}
```

##  Deploy em Produção (Oracle Cloud)

Graças à infraestrutura configurada na OCI, a API já está disponível publicamente para integração via internet.

* **Base URL:** `http://flight-on-time-ds.vm3.arbly.com`
* **Endpoint de Predição:** `POST /predict`
* **Documentação Interativa (Swagger):** [Acessar Docs](http://flight-on-time-ds.vm3.arbly.com/docs)

**Teste rápido via Terminal (cURL):**
```bash
curl -X POST "http://flight-on-time-ds.vm3.arbly.com/predict" \
-H "Content-Type: application/json" \
-d '{"companhia": "AZUL", "origem": "Guarulhos", "destino": "Recife", "data_partida": "2025-12-25T14:30:00", "distancia_km": 2100.5}'
```