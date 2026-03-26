# Publicacao No GitHub

## Estrutura minima obrigatoria

- `README.md`
- `CHANGELOG.md`
- `.gitignore`
- `docs/`
- `scripts/`
- testes automatizados em `tests/`

## Fluxo recomendado

```powershell
git status
git add .
git commit -m "feat: iniciar remodelacao arquitetural 4.0.0"
git push origin <branch>
```

## Regras

- commits pequenos e com intencao unica;
- sempre atualizar documentacao e changelog na mesma entrega;
- nao versionar `.env`, certificados, bancos reais ou artefatos locais;
- manter release notes rastreadas em `release/`.
