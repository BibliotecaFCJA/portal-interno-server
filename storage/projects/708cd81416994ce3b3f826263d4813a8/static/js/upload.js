/* Digitaliza FCJA — upload com drag-and-drop e controle de duplicatas. */
(function () {
  'use strict';

  var obra = window.FCJA_OBRA;
  if (!obra) { return; }

  var area = document.getElementById('area-upload');
  var entrada = document.getElementById('entrada-arquivos');
  var feedback = document.getElementById('feedback-upload');

  // Modal de duplicatas (decisão do usuário: substituir ou não).
  var duplicatas = [];
  var arquivosPendentes = [];

  function criarModalDuplicatas() {
    var modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'modal-duplicatas';
    modal.hidden = true;
    modal.innerHTML =
      '<div class="modal-caixa" role="dialog" aria-modal="true">' +
      '  <h2>Página já adicionada</h2>' +
      '  <p id="texto-duplicatas"></p>' +
      '  <p>Deseja substituir a(s) página(s) existente(s) pela(s) nova(s)?</p>' +
      '  <div class="grupo-botoes modal-acoes">' +
      '    <button type="button" class="botao botao-contorno" id="dup-nao">Não</button>' +
      '    <button type="button" class="botao botao-primario" id="dup-sim">Sim, substituir</button>' +
      '  </div>' +
      '</div>';
    document.body.appendChild(modal);

    modal.querySelector('#dup-sim').addEventListener('click', function () {
      modal.hidden = true;
      enviar(arquivosPendentes, true);
    });
    modal.querySelector('#dup-nao').addEventListener('click', function () {
      modal.hidden = true;
      enviar(arquivosPendentes.filter(function (arquivo) {
        return duplicatas.indexOf(normalizarNome(arquivo.name)) === -1;
      }), false);
    });
    return modal;
  }

  var modal = criarModalDuplicatas();

  function normalizarNome(nome) {
    return (nome || '').toLowerCase().replace(/\\/g, '/').split('/').pop();
  }

  function nomesJaExistentes() {
    var nomes = [];
    document.querySelectorAll('.cartao-pagina .nome-arquivo').forEach(function (el) {
      nomes.push(normalizarNome(el.getAttribute('title') || el.textContent));
    });
    return nomes;
  }

  function mostrarMensagem(texto, tipo) {
    var div = document.createElement('div');
    div.className = 'flash flash-' + tipo;
    div.setAttribute('role', 'alert');
    div.textContent = texto;
    feedback.appendChild(div);
  }

  function validarExtensao(nome) {
    return /\.(jpe?g|png|tiff?|tif)$/i.test(nome || '');
  }

  function coletarArquivos(lista) {
    var validos = [];
    var invalidos = 0;
    for (var i = 0; i < lista.length; i++) {
      var arquivo = lista[i];
      if (validarExtensao(arquivo.name)) {
        validos.push(arquivo);
      } else {
        invalidos++;
      }
    }
    if (invalidos) {
      mostrarMensagem(invalidos + ' arquivo(s) ignorado(s): formato não suportado.', 'erro');
    }
    return validos;
  }

  function enviar(arquivos, substituir) {
    if (!arquivos.length) {
      mostrarMensagem('Nenhum arquivo novo para adicionar.', 'info');
      return;
    }
    var dados = new FormData();
    arquivos.forEach(function (arquivo) { dados.append('arquivos', arquivo); });
    if (substituir) { dados.append('substituir', '1'); }

    mostrarMensagem('Enviando ' + arquivos.length + ' imagem(ns)…', 'info');

    fetch(obra.uploadUrl, { method: 'POST', body: dados, credentials: 'same-origin' })
      .then(function (resposta) { return resposta.json(); })
      .then(function (corpo) {
        feedback.innerHTML = '';
        if (corpo.erro) {
          mostrarMensagem(corpo.erro, 'erro');
          return;
        }
        (corpo.mensagens || []).forEach(function (texto) {
          var tipo = texto.indexOf('sucesso') !== -1 ? 'sucesso'
            : (texto.indexOf('Atenção') !== -1 || texto.indexOf('ignorado') !== -1) ? 'erro'
            : 'info';
          mostrarMensagem(texto, tipo);
        });
        // Recarrega para atualizar as miniaturas e contadores.
        setTimeout(function () { window.location.reload(); }, 1200);
      })
      .catch(function () {
        feedback.innerHTML = '';
        mostrarMensagem('Falha de comunicação com o servidor. Tente novamente.', 'erro');
      });
  }

  function iniciarUpload(lista) {
    var arquivos = coletarArquivos(lista);
    if (!arquivos.length) { return; }

    var existentes = nomesJaExistentes();
    duplicatas = [];
    arquivos.forEach(function (arquivo) {
      var nome = normalizarNome(arquivo.name);
      if (existentes.indexOf(nome) !== -1 && duplicatas.indexOf(nome) === -1) {
        duplicatas.push(nome);
      }
    });

    if (duplicatas.length) {
      arquivosPendentes = arquivos;
      modal.querySelector('#texto-duplicatas').textContent =
        duplicatas.length + ' arquivo(s) já existe(m) nesta obra: ' +
        duplicatas.slice(0, 5).join(', ') + (duplicatas.length > 5 ? '…' : '');
      modal.hidden = false;
      return;
    }
    enviar(arquivos, false);
  }

  // Entrada padrão de arquivos.
  if (entrada) {
    entrada.addEventListener('change', function () {
      iniciarUpload(entrada.files);
      entrada.value = '';
    });
  }

  // Drag and drop -----------------------------------------------------
  if (area) {
    ['dragenter', 'dragover'].forEach(function (evento) {
      area.addEventListener(evento, function (e) {
        e.preventDefault();
        e.stopPropagation();
        area.classList.add('arrastando');
        var titulo = area.querySelector('.area-upload-titulo');
        if (titulo) { titulo.textContent = 'SOLTE OS ARQUIVOS AQUI'; }
      });
    });
    ['dragleave', 'drop'].forEach(function (evento) {
      area.addEventListener(evento, function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (evento === 'dragleave' && area.contains(e.relatedTarget)) { return; }
        area.classList.remove('arrastando');
        var titulo = area.querySelector('.area-upload-titulo');
        if (titulo) { titulo.textContent = 'Arraste as imagens aqui'; }
      });
    });
    area.addEventListener('drop', function (e) {
      if (e.dataTransfer && e.dataTransfer.files) {
        iniciarUpload(e.dataTransfer.files);
      }
    });
  }
})();