# Como executar

Para executar o projeto basta executar o seguinte comando:

```bash
docker compose up -d
```

Então serão criados 4 containers, `consumer`,`producer`,`mysql` e `rabbitmq`.
A API estará disponível na porta 5000 do seu host local.

# Endpoints

Os seguintes endpoints estão disponívels

`POST`:`<host>/api/v1/subscriptions`

Esse endpoint necessita que um JSON seja passado no corpo da requisição com a seguinte estrutura

```python
{
    "user_id": <id>
}
```

`PUT`:`<host>/api/v1/subscriptions/:id/status`

Esse endpoint necessita que um JSON seja passado no corpo da requisição com a seguinte estrutura

```python
{
    "canceled": true
}
```

ou 


```python
{
    "restarted": true
}
```

Onde o primeiro exemplo de corpo cancela a assinatura cujo o id foi passado na url, analogamente o segundo exemplo de corpo reinicia uma assinatura.

# Arquitetura

## Banco de dados

Decidi utilizar um banco de dados MySQL, pois já tinha prática com o banco e sabia da facilidade de integrar o banco com a aplicação no futuro e de inicar o serviço utilizando um container docker. Para realizar a conexão 

## Mensageria

Escolhi o Rabbitmq por conta do contexto do projeto em que estou inserido, onde utilizamos uma mensageria rabbitmq para enfileiramento de eventos do Amazon s3, então decidi me aprofundar mais na ferramenta visto que ela será presente no meu dia a dia.

A criação da instância utilizando docker compose foi bastante tranquila, bastou seguir os poucos passos de documentações que se pode encontrar em sites como o medium, e o container já estava lá sendo executado sem erros.

Para executar a mensageria foiram criadas 1 exchange chamada `SUBSCRIPTIONS` e 3 filas `PURCHASED`,`CANCELED`,`RESTARTED`. Onde todas as filas são bindadas com o exchange no modo direto, cada fila possui sua `routing_key` (que é o bind da fila com o exchange), que consiste na seguinte concatenação  `<NOME_EXCHANGE>_<NOME_FILA>`

O Producer envia as mensagens no formato JSON para a exchange, e essa lida com o enfileiramento.

O Consumer, como o nome de indica, consome as mensagens enfileiradas, e a partir de qual fila em que a mensagem foi recebida ele realiza uma operação no banco de dados. Além disso, existe uma feature de RPC que ao realizar as operações com sucesso no banco de dados é executado um callback que envia uma mensagem na fila e exchange default do rabbit, utilizando um correlation_id para bindar com a mensagem de retorno ao producer com os valores que foram inseridos/atualizados. 

links:

- [Criacao de exchanges no modo direto](https://www.rabbitmq.com/tutorials/tutorial-four-python.html)
- [RPC utilizando rabbitmq](https://www.rabbitmq.com/tutorials/tutorial-six-python.html)

## API (Producer)

Para densenvolvimento da API utilizei python junto com o micro-framework Flask, me baseei em sites da internet para a criação da estrutura de pastas e arquitetura dos arquivos. Basicamente foram criados módulos que separam os componentes de rotas e conexão com o broker, onde a conexão com o broker é feita através de uma classe para facilitar/padronizar a chamada de métodos que são comuns para todos os endpoints que utilizam a mensageria.

De início eu não iria tomar essa arquitetura porém antes de iniciar realmente o processo de desenvolvimento decidi pequisar mais sobre boas praticas de arquitetura de arquivos quando se utiliza flask e decidi adotar um template que mais me agradou.

Estrutura adotada:

```
.
├── Dockerfile
├── api
│   ├── router
│   │   └── subscription.py
│   ├── schema
│   │   ├── __init__.py
│   │   └── subscription.py
│   └── service
│       ├── __init__.py
│       └── connector.py
├── app.py
├── config.py
├── requirements.txt
└── run.py
```

## Consumer

Para desenvolvimento do consumer no que se refere a mensageria segui os passos da documentaçao oficial tanto para a criaçao do subscriber.

A conexão com o banco de dados foi feita utilizando a biblioteca `mysql-connector-python` na versão 8.0.30, a biblioteca é bastante simplista porém consegue entregar o que o desafio precisa, que é realizar queries simples de consulta, inserção e atualização de registros no banco de dados. Para realizar essas queries segui a documentção oficial da ferramenta, onde eu so precisava criar strings com as queries e chamar o método `execute(query)` do cursor que era criado.


Estrutura de pastas adotada:

```
.
├── Dockerfile
├── requirements.txt
├── run.py
└── service
    └── database.py
```

links:

- [Documentação do mysql-python-connector](https://dev.mysql.com/doc/connector-python/en/)

# Melhorias e upgrades

## Tratamento de erros

- Atualmente a API praticamente realiza apenas o caminho feliz das requisições, não tendo sido implementado nenhum teste unitário, sendo assim, ainda é um projeto pouco resiliente. Apesar de serem tratadas algumas excessões de conexão o ideal é que ouvessem mais validações dos dados passados nas requisições.

## Autenticação
 
- Não é utilizado nenhum token de autenticação, um upgrade que acho interessante é implementar o uso de tokens JWT para as rotas de criação e atualização de assinaturas. 
