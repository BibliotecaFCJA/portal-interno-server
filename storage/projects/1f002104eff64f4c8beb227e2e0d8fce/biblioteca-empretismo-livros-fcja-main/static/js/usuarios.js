let usuarios = [];
let paginaAtual = 0;
const usuariosPorPagina = 10;

async function carregarUsuarios() {
  const resposta = await fetch("/usuarios");
  usuarios = await resposta.json();

  renderizarTabela();
}

function renderizarTabela() {
  const tabela = document.getElementById("tabelaUsuarios");
  tabela.innerHTML = "";

  const inicio = paginaAtual * usuariosPorPagina;
  const fim = inicio + usuariosPorPagina;

  const usuariosPagina = usuarios.slice(inicio, fim);

  usuariosPagina.forEach((usuario) => {
    const linha = document.createElement("tr");

    linha.innerHTML = `
      <td>${usuario.nome}</td>
      <td>${usuario.email}</td>
      <td>${usuario.telefone}</td>
      <td>${usuario.endereco}</td>
      <td>${usuario.matricula}</td>
      <td>
        <button class="btn-emprestimo" onclick="registrarEmprestimo(${usuario.id})">
          Registrar Empréstimo
        </button>
      </td>
    `;

    tabela.appendChild(linha);
  });
}

document.getElementById("paginaAnterior").onclick = () => {
  if (paginaAtual > 0) {
    paginaAtual--;
    renderizarTabela();
  }
};

document.getElementById("proximaPagina").onclick = () => {
  if ((paginaAtual + 1) * usuariosPorPagina < usuarios.length) {
    paginaAtual++;
    renderizarTabela();
  }
};

document.getElementById("pesquisaEmail").addEventListener("input", function () {
  const valor = this.value.toLowerCase();

  const filtrados = usuarios.filter((usuario) =>
    usuario.email.toLowerCase().includes(valor),
  );

  const tabela = document.getElementById("tabelaUsuarios");
  tabela.innerHTML = "";

  filtrados.forEach((usuario) => {
    const linha = document.createElement("tr");

    linha.innerHTML = `
      <td>${usuario.nome}</td>
      <td>${usuario.email}</td>
      <td>${usuario.telefone}</td>
      <td>${usuario.endereco}</td>
      <td>${usuario.matricula}</td>
      <td>
        <button class="btn-emprestimo" onclick="registrarEmprestimo(${usuario.id})">
          Registrar Empréstimo
        </button>
      </td>
    `;

    tabela.appendChild(linha);
  });
});

document.getElementById("btnCriarUsuario").onclick = () => {
  window.location.href = "/usuarios/novo";
};
function registrarEmprestimo(usuarioId) {
  window.location.href = `/emprestimos/novo/${usuarioId}`;
}
carregarUsuarios();
