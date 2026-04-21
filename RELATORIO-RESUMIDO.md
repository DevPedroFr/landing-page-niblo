# Relatorio resumido das correcoes

## Ajustes aplicados

- Adicionado `Permissions-Policy` em [vercel.json](vercel.json) para desabilitar recursos do navegador que nao sao usados pelo site.
- Ajustado `Cache-Control` em [vercel.json](vercel.json) para `no-store, no-cache, must-revalidate`, reduzindo o alerta informativo sobre cache publico.
- Padronizado `rel="noopener noreferrer"` em links externos com `target="_blank"` nas paginas institucionais, de contato, parceiros, solucoes, sobre e blog posts.

## Impacto esperado

- Reducao de superficie de ataque em abas externas abertas pelo site.
- Hardening adicional de headers sem alterar o fluxo atual do Google Forms.
- Menor exposicao de conteudo estatico a cache publico desnecessario apos novo deploy.

## Itens que permanecem por decisao de arquitetura

- A dependencia de Google Forms permanece nas paginas de contato e parceiros.
- A identificacao da plataforma Vercel continuara visivel enquanto o ativo permanecer publicado nessa infraestrutura e dominio.

## Validacao realizada

- Arquivos alterados sem erros estruturais reportados pelo editor.
- Nao foram encontrados links com `target="_blank"` sem `rel` nas paginas HTML apos a correcao.
- Nenhuma alteracao foi feita na logica JavaScript nem nos iframes de formulario.