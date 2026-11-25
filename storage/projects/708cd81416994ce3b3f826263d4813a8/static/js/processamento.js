/* Digitaliza FCJA — pré-visualização, comparação e progresso do processamento. */
(function () {
  'use strict';

  var conf = window.FCJA_PROCESSAMENTO;
  if (!conf || !conf.temPaginas) { return; }

  var atualizarOpacidadeGlobal = function () {};
  window.atualizarOpacidade = function () { atualizarOpacidadeGlobal(); };

  /* ---------- Pré-visualização com ajustes em tempo real ---------- */
  var imagemPreview = document.getElementById('imagem-preview');
  var caixaErroPreview = document.getElementById('preview-erro');
  var carregando = document.getElementById('preview-carregando');
  var selecaoPagina = document.getElementById('prev-pagina');
  var selecaoPosicao = document.getElementById('prev-posicao');
  var selecaoTamanho = document.getElementById('prev-tamanho-modo');
  var campoPercentual = document.getElementById('campo-percentual');
  var faixaPercentual = document.getElementById('prev-percentual');
  var saidaPercentual = document.getElementById('saida-percentual');
  var faixaMargem = document.getElementById('prev-margem');
  var saidaMargem = document.getElementById('saida-margem');
  var faixaOpacidade = document.getElementById('prev-opacidade');
  var saidaOpacidade = document.getElementById('saida-opacidade');
  var temporizadorPreview = null;

  function montarUrlPreview(comTimestamp) {
    var params = new URLSearchParams();
    params.set('pagina', selecaoPagina ? selecaoPagina.value : '0');
    if (selecaoPosicao) { params.set('wm_posicao', selecaoPosicao.value); }
    if (selecaoTamanho) { params.set('wm_tamanho_modo', selecaoTamanho.value); }
    if (faixaPercentual) { params.set('wm_tamanho_percentual', faixaPercentual.value); }
    if (faixaMargem) { params.set('wm_margem_percentual', faixaMargem.value); }
    if (faixaOpacidade) { params.set('wm_opacidade', faixaOpacidade.value); }
    // Força o navegador a buscar a pré-visualização atualizada (sem cache).
    if (comTimestamp) { params.set('_ts', String(Date.now())); }
    return conf.urlPreview + '?' + params.toString();
  }

  function coletarConfig() {
    var cfg = {};
    if (selecaoPosicao) { cfg.wm_posicao = selecaoPosicao.value; }
    if (selecaoTamanho) { cfg.wm_tamanho_modo = selecaoTamanho.value; }
    if (faixaPercentual) { cfg.wm_tamanho_percentual = faixaPercentual.value; }
    if (faixaMargem) { cfg.wm_margem_percentual = faixaMargem.value; }
    if (faixaOpacidade) { cfg.wm_opacidade = faixaOpacidade.value; }
    return cfg;
  }

  function atualizarPreview(comTimestamp) {
    if (!imagemPreview && !imagemComparacao) { return; }
    if (carregando) { carregando.hidden = false; }
    if (caixaErroPreview) { caixaErroPreview.hidden = true; }
    var url = montarUrlPreview(comTimestamp);
    var imagem = new Image();
    imagem.onload = function () {
      if (imagemPreview) { imagemPreview.src = url; }
      if (carregando) { carregando.hidden = true; }
      atualizarComparacao(url);
    };
    imagem.onerror = function () {
      if (carregando) { carregando.hidden = true; }
      if (caixaErroPreview) { caixaErroPreview.hidden = false; }
      atualizarComparacao(url);
    };
    imagem.src = url;
  }

  function agendarPreview() {
    if (temporizadorPreview) { clearTimeout(temporizadorPreview); }
    temporizadorPreview = setTimeout(function () { atualizarPreview(false); }, 350);
  }

  [selecaoPagina, selecaoPosicao, selecaoTamanho].forEach(function (el) {
    if (el) { el.addEventListener('change', function () { atualizarPreview(false); }); }
  });
  if (selecaoTamanho && campoPercentual) {
    selecaoTamanho.addEventListener('change', function () {
      campoPercentual.hidden = selecaoTamanho.value === 'fixo';
    });
  }
  if (faixaPercentual) {
    faixaPercentual.addEventListener('input', function () {
      saidaPercentual.textContent = faixaPercentual.value + '%';
      agendarPreview();
    });
  }
  if (faixaMargem) {
    faixaMargem.addEventListener('input', function () {
      saidaMargem.textContent = faixaMargem.value + '%';
      agendarPreview();
    });
  }
  if (faixaOpacidade) {
    faixaOpacidade.addEventListener('input', function () {
      saidaOpacidade.textContent = faixaOpacidade.value + '%';
      agendarPreview();
    });
  }
  atualizarOpacidadeGlobal = agendarPreview;

  /* ---------- Comparação original × processada (deslizante) ---------- */
  var comparacao = document.getElementById('comparacao');
  var imagemComparacao = document.getElementById('imagem-comparacao');
  var imagemComparacaoOriginal = document.getElementById('imagem-comparacao-original');
  var caixaErroComparacao = document.getElementById('comparacao-erro');
  var controle = document.getElementById('comparacao-controle');

  function atualizarComparacao(urlPreview) {
    var idx = selecaoPagina ? parseInt(selecaoPagina.value, 10) : 0;
    var pagina = conf.paginas && conf.paginas[idx];
    var url = urlPreview || montarUrlPreview(false);
    if (caixaErroComparacao) { caixaErroComparacao.hidden = true; }
    if (imagemComparacaoOriginal && pagina) {
      imagemComparacaoOriginal.onerror = function () {
        if (caixaErroComparacao) { caixaErroComparacao.hidden = false; }
      };
      imagemComparacaoOriginal.src = pagina.original;
    }
    if (imagemComparacao) {
      imagemComparacao.onerror = function () {
        if (caixaErroComparacao) { caixaErroComparacao.hidden = false; }
      };
      imagemComparacao.onload = function () {
        if (caixaErroComparacao) { caixaErroComparacao.hidden = true; }
      };
      imagemComparacao.src = url;
    }
  }
  if (controle && imagemComparacao) {
    controle.addEventListener('input', function () {
      var posicao = parseInt(controle.value, 10);
      imagemComparacao.style.clipPath = 'inset(0 0 0 ' + posicao + '%)';
    });
  }

  /* ---------- Processamento em lote com progresso ---------- */
  var botaoProcessar = document.getElementById('botao-processar');
  var botaoCancelar = document.getElementById('botao-cancelar');
  var boxProgresso = document.getElementById('progresso-box');
  var barra = document.getElementById('barra-preenchimento');
  var barraAria = document.getElementById('barra-progresso');
  var numeros = document.getElementById('progresso-numeros');
  var statusTexto = document.getElementById('progresso-status');
  var paginaAtual = document.getElementById('progresso-pagina');
  var boxResultado = document.getElementById('resultado-box');
  var resultadoMensagem = document.getElementById('resultado-mensagem');
  var sondando = false;

  function mostrarResultado(estado) {
    boxResultado.hidden = false;
    boxResultado.classList.toggle('erro', !estado.sucesso);
    resultadoMensagem.textContent = estado.mensagem || 'Processamento finalizado.';
    botaoCancelar.hidden = true;
    botaoProcessar.disabled = false;
    botaoProcessar.textContent = 'Processar novamente';
    // Recarrega a pré-visualização/comparação sem cache, refletindo o
    // resultado do processamento mais recente.
    atualizarPreview(true);
  }

  function sondarStatus() {
    fetch(conf.urlStatus, { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (estado) {
        if (!estado || Object.keys(estado).length === 0) {
          // Nenhum processamento nesta sessão/servidor reiniciado.
          return;
        }
        var total = estado.total || 0;
        var concluidas = estado.concluidas || 0;
        var percentual = total ? Math.round((concluidas / total) * 100) : 0;

        if (estado.executando) {
          boxProgresso.hidden = false;
          barra.style.width = percentual + '%';
          barraAria.setAttribute('aria-valuenow', String(percentual));
          numeros.textContent = concluidas + ' / ' + total + ' páginas · ' + percentual + '%';
          statusTexto.textContent = estado.status || 'Processando…';
          paginaAtual.textContent = estado.pagina_atual
            ? ('Arquivo atual: ' + estado.pagina_atual) : '';
          setTimeout(sondarStatus, 1200);
        } else if (estado.concluido && !estado.finalizado) {
          estado.finalizado = true;
          boxProgresso.hidden = false;
          barra.style.width = percentual + '%';
          numeros.textContent = concluidas + ' / ' + total + ' páginas · ' + percentual + '%';
          statusTexto.textContent = estado.status || 'Concluído.';
          mostrarResultado(estado);
        }
      })
      .catch(function () { /* tenta de novo no próximo ciclo */ });
  }

  if (botaoProcessar) {
    botaoProcessar.addEventListener('click', function () {
      botaoProcessar.disabled = true;
      boxResultado.hidden = true;
      boxProgresso.hidden = false;
      statusTexto.textContent = 'Iniciando…';
      fetch(conf.urlIniciar, {
        method: 'POST', credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'fetch',
        },
        body: JSON.stringify(coletarConfig()),
      })
        .then(function (r) { return r.json().then(function (corpo) {
          return { ok: r.ok, corpo: corpo };
        }); })
        .then(function (resposta) {
          if (!resposta.ok) {
            botaoProcessar.disabled = false;
            statusTexto.textContent = resposta.corpo.erro || 'Não foi possível iniciar.';
            return;
          }
          botaoCancelar.hidden = false;
          if (!sondando) {
            sondando = true;
            sondarStatus();
          }
        })
        .catch(function () {
          botaoProcessar.disabled = false;
          statusTexto.textContent = 'Falha de comunicação com o servidor.';
        });
    });
  }

  if (botaoCancelar) {
    botaoCancelar.addEventListener('click', function () {
      fetch(conf.urlCancelar, {
        method: 'POST', credentials: 'same-origin',
        headers: { 'X-Requested-With': 'fetch' },
      }).then(function () {
        statusTexto.textContent = 'Cancelando após a página atual…';
      });
    });
  }

  // Retoma o acompanhamento se um processamento já estiver em execução.
  sondarStatus();
})();