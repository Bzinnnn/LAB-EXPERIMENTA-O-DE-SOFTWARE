# Enunciado 01

Este diretório contém a solução do Enunciado 01.

## Estrutura

- `src/`: scripts de coleta e processamento.
- `data/`: arquivos CSV gerados.
- `docs/`: documentação complementar.
- `output/`: saídas de execução.

## Como executar

1. Abra terminal em `enunciado01`.
2. Instale dependências:

```bash
pip install -r requirements.txt
```

3. Configure o token no arquivo `.env`:

```env
GITHUB_TOKEN=seu_token_aqui
```

4. Execute o script principal:

```bash
python src/main.py
```
