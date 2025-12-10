# FlightOnTime - Previsão de Atrasos de Voos

## Sobre o Projeto
Este repositório contém o motor de Inteligência Artificial do projeto FlightOnTime, desenvolvido durante a Simulação da No Country.

O objetivo do MVP é fornecer um microserviço capaz de calcular a probabilidade de atraso de voos comerciais no Brasil. O modelo utiliza dados históricos de operações para identificar padrões de risco baseados em companhia aérea, rota, data e horário.

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

## Regra de Negócio (Modelo)
O modelo atual opera com as seguintes definições:
* **Target:** Um voo é considerado "Atrasado" se a diferença entre a partida real e prevista for maior que 15 minutos.
* **Features:** O modelo considera a companhia aérea, aeroporto de origem, destino, mês, dia da semana e hora do voo.
* **Métrica Principal:** Priorizamos o Recall (Sensibilidade) para garantir que o sistema alerte sobre a maioria dos possíveis atrasos.

## Guia de Instalação e Execução

### 1. Preparar o Ambiente
Certifique-se de ter o Python instalado. Recomenda-se o uso de um ambiente virtual (venv).

Instale as dependências do projeto:
```bash
pip install -r requirements.txt
```

### 2. Treinar o Modelo (Gerar o Cérebro)
Antes de iniciar a API, é necessário processar os dados e gerar o arquivo do modelo (.joblib). Execute o script de treinamento:

```bash
python src/train.py
```
*Isso criará o arquivo `flight_model_mvp.joblib` dentro da pasta src.*

### 3. Iniciar a API
Com o modelo gerado, inicie o servidor local:

```bash
python -m uvicorn src.app:app --reload
```
A API estará disponível em: `http://127.0.0.1:8000`

## Documentação da API (Contrato)

**Endpoint:** `POST /predict`

**Exemplo de Requisição (JSON):**
```json
{
  "companhia": "AZUL",
  "origem": "Guarulhos",
  "destino": "Recife",
  "data_partida": "2025-12-25T14:30:00"
}
```

**Exemplo de Resposta:**
```json
{
  "atrasado": true,
  "probabilidade": 0.72,
  "nivel_risco": "ALTO",
  "modelo": "Random Forest MVP v1"
}
```