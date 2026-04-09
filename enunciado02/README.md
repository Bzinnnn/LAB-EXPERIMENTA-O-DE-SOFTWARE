# Enunciado 02 — LAB de Medição de Software

Este trabalho prático tem como objetivo aplicar conceitos de medição de software, conforme solicitado no enunciado do LAB02.

## Estrutura do Projeto

- `src/main.py`: executa o fluxo completo do laboratório.
- `src/lab02_pipeline.py`: pipeline de coleta, medição de qualidade, consolidação, relatório e gráficos.
- `docs/LAB02_ENUNCIADO_REFORMULADO.md`: enunciado detalhado do trabalho.
- `docs/LAB02_RELATORIO_ESBOCO.md`: modelo de relatório para entrega.

## Como Executar

1. Instale as dependências:
	```bash
	pip install -r requirements.txt
	```
2. Configure o arquivo `.env` com seu token do GitHub:
	```env
	GITHUB_TOKEN=seu_token_aqui
	```
3. Execute o projeto:
	```bash
	python src/main.py
	```

O script irá:
- Coletar 1000 repositórios Java;
- Clonar e medir um repositório piloto;
- Executar medições de qualidade para toda a base (CK ou fallback);
- Consolidar os dados por repositório;
- Gerar o esboço do relatório final;
- Gerar gráficos de correlação (bônus).

> **Observação:** Os clones são salvos em `C:/lab02_clones` para evitar problemas de caminho no Windows.

