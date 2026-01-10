# 🛫 FlightOnTime - Sistema Inteligente de Previsão de Voos

> **Status do Projeto:** Em Produção (v5.0.0-LiveWeather)  
> **Arquitetura:** Monorepo (Frontend + Backend + Data Science)

O **FlightOnTime** é uma solução completa para prever atrasos em voos comerciais no Brasil. O sistema combina Inteligência Artificial avançada, dados meteorológicos em tempo real e uma arquitetura robusta de microserviços para garantir a segurança e o planejamento dos passageiros.

---

##  Estrutura do Repositório

Este repositório agrupa todas as camadas da aplicação:

```text
/ (Raiz)
├── data-science/  # Core de ML (Python, CatBoost, FastAPI)
├── back-end/      # API Gateway e Regras de Negócio (Java, Spring Boot)
└── front-end/     # Interface do Usuário (React, Vite, Tailwind)
 1. Data Science & Inteligência Artificial
Diretório: /data-science

**[📄 Ver Documentação Técnica (Data Science)](./data-science/README.md)**

O "cérebro" do projeto. Responsável por calcular a probabilidade matemática de um atraso.

Modelo: CatBoost Classifier (Gradient Boosting).

Recursos (v5.0): Integração Live Weather (OpenMeteo) para considerar chuva e vento em tempo real, detecção automática de feriados e cálculo geodésico de distâncias.

Performance: 90.7% de Recall (foco em segurança).

API: FastAPI (Python).

☕ 2. Backend API
Diretório: /back-end

**[📄 Ver Documentação Técnica (Backend)](./back-end/README.md)**

O orquestrador do sistema. Gerencia as requisições, conecta-se ao motor de IA e aplica regras de negócio.

Tecnologia: Java 21 + Spring Boot 3.5.4.

Banco de Dados: MySQL (com Flyway).

Funcionalidade: Recebe os dados do voo, consulta o microserviço de Data Science e formata a resposta padronizada para o cliente, gerenciando usuários e histórico.

💻 3. Frontend Dashboard
Diretório: /front-end

**[📄 Ver Documentação Técnica (Frontend)](./front-end/README.md)**

A interface visual para o usuário final.

Tecnologia: React + Vite + Tailwind CSS.

UX: Autocomplete inteligente para aeroportos e companhias, validação de códigos IATA e exibição visual do "Semáforo de Risco".

Como Executar o Projeto Completo
Para rodar a aplicação inteira localmente, você precisará de 3 terminais abertos (um para cada serviço).

Passo 1: Iniciar o Motor de IA (Data Science)

Bash
cd data-science

# Criar e ativar ambiente virtual (se necessário)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Subir a API de previsão
python -m uvicorn src.app:app --reload --port 8000
Passo 2: Iniciar o Backend (Java)

Bash
cd back-end

# Certifique-se de ter o MySQL rodando e configurado
# Executar a aplicação Spring Boot
./mvnw spring-boot:run
O Backend rodará por padrão na porta 8080.

Passo 3: Iniciar o Frontend (React)

Bash
cd front-end

# Instalar dependências
npm install

# Rodar servidor de desenvolvimento
npm run dev
O Frontend estará disponível em http://localhost:5173.

Regra de Negócio: O Semáforo de Risco
O sistema traduz a probabilidade matemática em uma experiência visual simples:

🟢 PONTUAL (Risco < 35%): Boas condições de voo e clima estável.

🟡 ALERTA (Risco 35% - 70%): Instabilidade detectada (chuva leve ou tráfego).

🔴 ATRASO PROVÁVEL (Risco > 70%): Condições críticas (Tempestade, Feriados).

Stack Tecnológico Geral
Linguagens: Python 3.10+, Java 21, JavaScript/ES6.

Frameworks: FastAPI, Spring Boot, React.

Dados: MySQL, Open-Meteo API, Kaggle Flight Data.

DevOps: Docker, OCI (Oracle Cloud), Git Monorepo.