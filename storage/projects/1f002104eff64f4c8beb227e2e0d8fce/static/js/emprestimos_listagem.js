document.addEventListener("DOMContentLoaded", carregarEmprestimos);

function carregarEmprestimos() {
  fetch("/usuarios/emprestimos")
    .then((response) => response.json())
    .then((dados) => {
      const tabela = document.getElementById("tabelaEmprestimos");
      tabela.innerHTML = "";

      dados.sort((a, b) => {
        if (a.data_devolucao && !b.data_devolucao) return 1;
        if (!a.data_devolucao && b.data_devolucao) return -1;
        const dataA = new Date(a.data_prevista_devolucao);
        const dataB = new Date(b.data_prevista_devolucao);

        return dataA - dataB;
      });

      dados.forEach((e) => {
        let prazo;

        if (e.data_devolucao) {
          prazo = "Devolvido";
        } else {
          prazo = new Date(e.data_prevista_devolucao).toLocaleDateString();
        }

        const linha = `
      <tr>
          <td>${e.usuario_nome}</td>
          <td>${e.livro_titulo}</td>
          <td>${e.livro_autor}</td>
          <td>${prazo}</td>

          <td>
              <button class="btn-emprestimo" onclick="verDetalhes(${e.id})">
                  Detalhes
              </button>

              <button class="btn-emprestimo" onclick="estenderEmprestimo(${e.id})">
                  Estender Empréstimo
              </button>

              <button class="btn-emprestimo" onclick="devolverEmprestimo(${e.id})">
                  Devolver Livro
              </button>
          </td>
      </tr>
  `;

        tabela.innerHTML += linha;
      });
    });
}

function verDetalhes(id) {
  fetch(`/usuarios/emprestimos/${id}`)
    .then((res) => res.json())
    .then((d) => {
      document.getElementById("detNome").value = d.usuario.nome;
      document.getElementById("detEmail").value = d.usuario.email;
      document.getElementById("detTelefone").value = d.usuario.telefone;
      document.getElementById("detEndereco").value = d.usuario.endereco;
      document.getElementById("detMatricula").value = d.usuario.matricula;
      document.getElementById("detTipo").value = d.usuario.tipo.charAt(0).toUpperCase() + d.usuario.tipo.slice(1);
      document.getElementById("detSetor").value = d.usuario.setor;

      document.getElementById("detTitulo").value = d.livro.titulo;
      document.getElementById("detAutor").value = d.livro.autor;
      document.getElementById("detEditora").value = d.livro.editora;
      document.getElementById("detEdicao").value = d.livro.edicao;
      document.getElementById("detLocal").value = d.livro.local;
      document.getElementById("detOrigem").value = d.livro.origem;
      document.getElementById("detAno").value = d.livro.ano;
      document.getElementById("detObs").value = d.livro.observacao;

      document.getElementById("detPrazo").value = new Date(
        d.data_prevista_devolucao,
      ).toLocaleDateString();

      document.getElementById("modalDetalhes").style.display = "flex";
    });
}

function fecharModal() {
  document.getElementById("modalDetalhes").style.display = "none";
}

function estenderEmprestimo(id) {
  fetch(`/usuarios/emprestimos/${id}/renovar`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ dias: 7 }),
  })
    .then((res) => res.json())
    .then((resposta) => {
      alert(resposta.mensagem);
      carregarEmprestimos();
    });
}

function devolverEmprestimo(id) {
  if (!confirm("Deseja realmente registrar a devolução?")) return;

  fetch(`/usuarios/emprestimos/${id}/devolucao`, {
    method: "PATCH",
  })
    .then((res) => res.json())
    .then((resposta) => {
      if (resposta.mensagem) {
        alert(resposta.mensagem);

        carregarEmprestimos();
      } else {
        alert(resposta.erro || "Erro ao registrar devolução.");
      }
    })
    .catch(() => {
      alert("Erro ao conectar com o servidor.");
    });
}

function exportarDados() {
  fetch("/usuarios/exportar/completo")
    .then((response) => response.blob())
    .then((blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");

      a.href = url;
      a.download = "backup.xlsx";
      a.click();

      window.URL.revokeObjectURL(url);
    })
    .catch(() => {
      alert("Erro ao exportar dados.");
    });
}

document.getElementById("btnExportar").onclick = () => {
  window.location.href = "/usuarios/exportar/completo";
};
