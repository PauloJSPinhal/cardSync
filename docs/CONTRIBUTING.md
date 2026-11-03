# Guia de Contribuição

Obrigado pelo interesse em contribuir para o cardSync.

## Estrutura

Ver [`ARCHITECTURE.md`](ARCHITECTURE.md) para a organização do código.

## Convenções

- **Dart/Flutter** com formatação padrão (`dart format .`).
- **Sem dependências entre `core` e UI/serviços** — a lógica de domínio deve permanecer pura.
- Nomes de ficheiros e classes em inglês; textos de interface em português.
- Usar `const` sempre que possível.

## Fluxo de trabalho

1. Criar uma *branch* a partir de `main`.
2. Fazer as alterações.
3. Executar:
   ```bash
   flutter analyze
   flutter test
   ```
4. Submeter um *Pull Request* com uma descrição clara.

## Testes

Os testes ficam em `test/`. Executar:

```bash
flutter test
```

## Reportar problemas

Abrir uma *issue* com:
- Descrição do problema.
- Passos para reproduzir.
- Ambiente (SO, versão do Flutter, dispositivo).
- Logs relevantes (`flutter run --verbose`).
