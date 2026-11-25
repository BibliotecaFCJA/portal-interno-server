# Design do Portal Interno

## Objetivo

O portal deve ajudar a pessoa a localizar e abrir um sistema com o mínimo de leitura. A Gestão deve deixar claro o próximo passo de cada projeto.

## Catálogo

1. Cabeçalho compacto com identificação, tema e acesso à Gestão.
2. Título direto e uma frase curta de orientação.
3. Busca e categorias antes da lista.
4. Uma contagem de resultados, sem repetir totais em vários lugares.
5. Cartões simples com nome, categoria, descrição, estado e uma ação principal.
6. Estados diferentes para sistema local, link externo, carregamento e lista vazia.

## Hero

- Reaproveitar a composição original: título central, foto de José Américo ao fundo e atalhos para sistemas e busca.
- Manter a altura contida e a foto suave para a lista continuar perto do topo.

## Gestão

- Fluxo principal: **Adicionar → Testar → Publicar**.
- Ordenar projetos pela ação necessária: testar, publicar, depois publicados.
- Dar destaque a apenas uma ação principal por projeto.
- Colocar edição, atualização e exclusão em “Mais ações”.
- Informar erros e etapas de preparação junto ao projeto correspondente.

## Estilo

- Layout plano, alinhado à esquerda, com espaços e divisores para separar conteúdo.
- Cantos quadrados nos cartões, campos, botões e etiquetas. Manter redondo somente o ponto de estado.
- Vermelho reservado para a ação principal e erros; verde identifica sistemas online.
- Evitar hero alto, sombras fortes, animações e etiquetas em formato de pílula.
- Foco visível no teclado e mensagens de estado que não dependem só de cor.

## Manter

- Tema claro e escuro.
- Pesquisa por nome, categoria e descrição, além de filtros por categoria.
- Segurança e ordem do fluxo Testar → Publicar.
- No catálogo, expor apenas os dados públicos permitidos pela função `toPublicSystem`.
