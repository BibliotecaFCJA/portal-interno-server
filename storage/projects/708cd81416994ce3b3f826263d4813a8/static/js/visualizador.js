/* Digitaliza FCJA — visualizador de páginas: navegação, zoom e modos. */
(function () {
  'use strict';

  var conf = window.FCJA_VISUALIZADOR;
  if (!conf || !conf.paginas || !conf.paginas.length) { return; }

  var paginas = conf.paginas;
  var indice = 0;
  var modo = 'original';
  var zoom = 100; // 100 = ajustado à tela

  var quadro = document.getElementById('visualizador-quadro');
  var imagem = document.getElementById('imagem-visualizador');
  var caixaErro = document.getElementById('visualizador-erro');
  var indicadorPagina = document.getElementById('indicador-pagina');
  var indicadorZoom = document.getElementById('indicador-zoom');
  var botaoAnterior = document.getElementById('botao-anterior');
  var botaoProximo = document.getElementById('botao-proximo');
  var entradaIr = document.getElementById('ir-pagina');
  var botaoIr = document.getElementById('botao-ir');
  var botaoZoomMais = document.getElementById('botao-zoom-mais');
  var botaoZoomMenos = document.getElementById('botao-zoom-menos');
  var botaoAjustar = document.getElementById('botao-ajustar');
  var botaoOriginal = document.getElementById('botao-original');
  var botaoProcessada = document.getElementById('botao-processada');
  var botaoTelaCheia = document.getElementById('botao-tela-cheia');
  var listaPulos = document.querySelectorAll('.pulo-pagina');

  function aplicarZoom() {
    if (!imagem) { return; }
    if (zoom === 100) {
      imagem.style.maxWidth = '100%';
      imagem.style.maxHeight = '';
      imagem.style.width = 'auto';
    } else {
      imagem.style.maxWidth = 'none';
      imagem.style.maxHeight = 'none';
      imagem.style.width = (zoom / 100 * 100) + '%';
    }
    if (indicadorZoom) { indicadorZoom.textContent = zoom === 100 ? 'Ajustada' : zoom + '%'; }
  }

  function atualizar() {
    var pagina = paginas[indice];
    var url = (modo === 'processada' && pagina.processada)
      ? pagina.processada : pagina.original;
    if (caixaErro) { caixaErro.hidden = true; }
    if (imagem) {
      imagem.onerror = function () {
        if (caixaErro) { caixaErro.hidden = false; }
      };
      imagem.onload = function () {
        if (caixaErro) { caixaErro.hidden = true; }
      };
      imagem.src = url;
    }
    if (indicadorPagina) {
      indicadorPagina.textContent = 'Página ' + (indice + 1) + ' / ' + paginas.length;
    }
    if (entradaIr) { entradaIr.value = String(indice + 1); }
    listaPulos.forEach(function (botao) {
      botao.classList.toggle('ativo',
        parseInt(botao.dataset.indice, 10) === indice);
    });
    if (botaoProcessada) {
      var disponivel = !!pagina.processada;
      botaoProcessada.disabled = !disponivel;
      if (!disponivel && modo === 'processada') {
        modo = 'original';
        botaoOriginal.classList.add('ativo-modo');
        botaoProcessada.classList.remove('ativo-modo');
      }
    }
    quadro.scrollTop = 0;
    quadro.scrollLeft = 0;
  }

  function irPara(novoIndice) {
    indice = Math.max(0, Math.min(paginas.length - 1, novoIndice));
    atualizar();
  }

  if (botaoAnterior) {
    botaoAnterior.addEventListener('click', function () { irPara(indice - 1); });
  }
  if (botaoProximo) {
    botaoProximo.addEventListener('click', function () { irPara(indice + 1); });
  }
  if (botaoIr && entradaIr) {
    botaoIr.addEventListener('click', function () {
      var numero = parseInt(entradaIr.value, 10);
      if (!isNaN(numero)) { irPara(numero - 1); }
    });
    entradaIr.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { botaoIr.click(); }
    });
  }
  if (botaoZoomMais) {
    botaoZoomMais.addEventListener('click', function () {
      zoom = Math.min(400, zoom === 100 ? 150 : zoom + 25);
      aplicarZoom();
    });
  }
  if (botaoZoomMenos) {
    botaoZoomMenos.addEventListener('click', function () {
      zoom = Math.max(25, zoom === 100 ? 75 : zoom - 25);
      aplicarZoom();
    });
  }
  if (botaoAjustar) {
    botaoAjustar.addEventListener('click', function () { zoom = 100; aplicarZoom(); });
  }
  if (botaoOriginal) {
    botaoOriginal.addEventListener('click', function () {
      modo = 'original';
      botaoOriginal.classList.add('ativo-modo');
      botaoProcessada.classList.remove('ativo-modo');
      atualizar();
    });
  }
  if (botaoProcessada) {
    botaoProcessada.addEventListener('click', function () {
      modo = 'processada';
      botaoProcessada.classList.add('ativo-modo');
      botaoOriginal.classList.remove('ativo-modo');
      atualizar();
    });
  }
  if (botaoTelaCheia && quadro) {
    botaoTelaCheia.addEventListener('click', function () {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else if (quadro.requestFullscreen) {
        quadro.requestFullscreen();
      }
    });
  }

  // Navegação por teclado (setas).
  document.addEventListener('keydown', function (e) {
    if (e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement) {
      return;
    }
    if (e.key === 'ArrowLeft') { irPara(indice - 1); }
    if (e.key === 'ArrowRight') { irPara(indice + 1); }
  });

  // Miniaturas de navegação.
  listaPulos.forEach(function (botao) {
    botao.addEventListener('click', function () {
      irPara(parseInt(botao.dataset.indice, 10));
    });
  });

  atualizar();
})();