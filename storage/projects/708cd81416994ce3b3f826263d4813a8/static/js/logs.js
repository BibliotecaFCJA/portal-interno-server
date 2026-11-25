/* Digitaliza FCJA — área de atividades (/logs).

   Melhora progressiva do agrupamento por mês: sem JavaScript cada mês é um
   link e a página recarrega normalmente (o servidor já renderiza o mês
   pedido). Com JavaScript, abrir um mês busca o HTML na mesma hora.

   O HTML vem do parcial _logs_mes.html, o mesmo da carga inicial — não há
   uma segunda versão da tabela para manter em sincronia. */
(function () {
  'use strict';

  var area = document.querySelector('.logs-meses');
  if (!area) { return; }

  // Um pedido por mês: evita respostas fora de ordem se o usuário clicar
  // rápido em vários meses.
  var pedidos = {};

  function urlDoMes(mes) {
    var url = new URL(window.location.href);
    url.searchParams.delete('mes');
    url.searchParams.set('mes', mes);
    return url.pathname + '/mes/' + encodeURIComponent(mes) + url.search;
  }

  function marcar(cabecalho, conteudo, aberto) {
    cabecalho.setAttribute('aria-expanded', aberto ? 'true' : 'false');
    conteudo.hidden = !aberto;
  }

  function carregando(conteudo) {
    conteudo.innerHTML =
      '<p class="logs-mes-carregando">Carregando registros do mês…</p>';
  }

  function montarErro(conteudo, mensagem) {
    conteudo.innerHTML = '';
    var p = document.createElement('p');
    p.className = 'logs-mes-erro';
    p.textContent = mensagem;
    conteudo.appendChild(p);
  }

  function abrir(cabecalho) {
    var mes = cabecalho.parentElement.dataset.mes;
    var conteudo = cabecalho.nextElementSibling;

    marcar(cabecalho, conteudo, cabecalho.getAttribute('aria-expanded') !== 'true');
    if (conteudo.hidden || conteudo.dataset.carregado === '1') { return; }

    if (pedidos[mes]) { return; }
    carregando(conteudo);
    pedidos[mes] = fetch(urlDoMes(mes), {
      headers: { 'X-Requested-With': 'fetch' },
    })
      .then(function (resposta) {
        if (!resposta.ok) { throw new Error('HTTP ' + resposta.status); }
        return resposta.json();
      })
      .then(function (dados) {
        conteudo.innerHTML = dados.html;
        conteudo.dataset.carregado = '1';
        pedidos[mes] = null;
      })
      .catch(function () {
        pedidos[mes] = null;
        // Sem rede ou sem servidor: volta ao link, que funciona sem JS.
        montarErro(
          conteudo,
          'Não foi possível carregar este mês. Clique para tentar de novo pela página.'
        );
      });
  }

  area.addEventListener('click', function (evento) {
    var cabecalho = evento.target.closest('.logs-mes-cabecalho');
    if (!cabecalho) { return; }
    evento.preventDefault();
    abrir(cabecalho);
  });
})();
