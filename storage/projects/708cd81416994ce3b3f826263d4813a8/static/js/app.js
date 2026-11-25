/* Digitaliza FCJA — utilidades globais (JS puro, sem frameworks). */
(function () {
  'use strict';

  // Confirmação genérica para formulários com data-confirmar.
  document.addEventListener('submit', function (evento) {
    var form = evento.target;
    if (form instanceof HTMLFormElement && form.dataset.confirmar) {
      if (!window.confirm(form.dataset.confirmar)) {
        evento.preventDefault();
      }
    }
  });

  // Flash temporário: some após 8 segundos (não bloqueia leitura por teclado).
  document.querySelectorAll('.flash').forEach(function (flash) {
    setTimeout(function () {
      flash.style.transition = 'opacity .6s';
      flash.style.opacity = '0';
      setTimeout(function () { flash.remove(); }, 700);
    }, 8000);
  });

  // Fecha modais com a tecla ESC.
  document.addEventListener('keydown', function (evento) {
    if (evento.key === 'Escape') {
      document.querySelectorAll('.modal:not([hidden])').forEach(function (modal) {
        modal.hidden = true;
      });
    }
  });

  // Modal de exclusão de obra: exige digitar o código da obra.
  var botaoExcluir = document.getElementById('botao-excluir');
  var modalExcluir = document.getElementById('modal-excluir');
  if (botaoExcluir && modalExcluir) {
    var campoCodigo = document.getElementById('confirmar-codigo');
    var campoConfirmar = document.getElementById('campo-confirmar');
    var botaoConfirmar = document.getElementById('confirmar-exclusao');
    var botaoCancelar = document.getElementById('cancelar-exclusao');

    botaoExcluir.addEventListener('click', function () {
      modalExcluir.hidden = false;
      if (campoCodigo) { campoCodigo.focus(); }
    });
    if (botaoCancelar) {
      botaoCancelar.addEventListener('click', function () {
        modalExcluir.hidden = true;
      });
    }
    modalExcluir.addEventListener('click', function (e) {
      if (e.target === modalExcluir) { modalExcluir.hidden = true; }
    });
    if (campoCodigo) {
      campoCodigo.addEventListener('input', function () {
        var esperado = (campoCodigo.getAttribute('data-codigo')
          || document.querySelector('#modal-excluir code')
          || {}).textContent;
        if (campoConfirmar && botaoConfirmar) {
          var valido = campoCodigo.value.trim().toUpperCase()
            === (esperado || '').trim().toUpperCase();
          campoConfirmar.value = valido
            ? campoCodigo.value.trim().toUpperCase() : '';
          botaoConfirmar.disabled = !valido;
        }
      });
    }
  }

  /* ---------- Tema (sistema / escuro / claro) ---------- */
  var CHAVE_TEMA = 'tema';
  var CONSULTA = window.matchMedia
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : null;

  // Rótulos por estado: o título descreve o estado atual e o
  // aria-label descreve para onde o próximo clique leva.
  var ESTADOS_TEMA = {
    sistema: { titulo: 'Tema: automático (sistema)', proximo: 'escuro', acao: 'Usar tema escuro' },
    escuro: { titulo: 'Tema: escuro', proximo: 'claro', acao: 'Usar tema claro' },
    claro: { titulo: 'Tema: claro', proximo: 'sistema', acao: 'Seguir o tema do sistema' }
  };

  function preferenciaDoSistema() {
    return (CONSULTA && CONSULTA.matches) ? 'escuro' : 'claro';
  }

  // Estado escolhido pelo usuário. Ausente = automático.
  function temaEscolhido() {
    var valor = null;
    try { valor = window.localStorage.getItem(CHAVE_TEMA); } catch (e) {}
    return ESTADOS_TEMA[valor] ? valor : 'sistema';
  }

  // 'sistema' não é gravado: assim a preferência do sistema continua
  // válida e o navegador volta a ajustá-la sozinho.
  function gravarTema(estado) {
    try {
      if (estado === 'sistema') { window.localStorage.removeItem(CHAVE_TEMA); }
      else { window.localStorage.setItem(CHAVE_TEMA, estado); }
    } catch (e) {}
  }

  function aplicarTema(estado) {
    var escuro = (estado === 'sistema' ? preferenciaDoSistema() : estado) === 'escuro';
    var raiz = document.documentElement;

    raiz.classList.toggle('dark', escuro);
    raiz.style.colorScheme = escuro ? 'dark' : 'light';
    raiz.setAttribute('data-tema', estado);

    var info = ESTADOS_TEMA[estado];
    document.querySelectorAll('[data-tema-botao]').forEach(function (botao) {
      botao.setAttribute('title', info.titulo);
      botao.setAttribute('aria-label', info.acao);
    });
  }

  document.querySelectorAll('[data-tema-botao]').forEach(function (botao) {
    botao.addEventListener('click', function () {
      var estado = ESTADOS_TEMA[temaEscolhido()].proximo;
      gravarTema(estado);
      aplicarTema(estado);
    });
  });

  // Sincroniza com o <head>, que já tinha resolvido o tema na 1ª pintura.
  aplicarTema(temaEscolhido());

  // Só reage à mudança do sistema se o usuário não tiver escolhido um tema.
  if (CONSULTA && CONSULTA.addEventListener) {
    CONSULTA.addEventListener('change', function () {
      if (temaEscolhido() === 'sistema') { aplicarTema('sistema'); }
    });
  }
})();
