const form = document.getElementById("formEmprestimo");

if (form) {
  const usuarioId = form.dataset.usuarioId;

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    const dataDevolucao = new Date(formData.get("prazo_devolucao"));
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    dataDevolucao.setHours(0, 0, 0, 0);
    const diffTempo = dataDevolucao - hoje;
    const prazoDias = Math.ceil(diffTempo / (1000 * 60 * 60 * 24));

    if (prazoDias <= 0) {
      alert("A data de devolução deve ser futura.");
      return;
    }

    const dados = {
      usuario_id: usuarioId,
      titulo: formData.get("titulo"),
      autor: formData.get("autor"),
      edicao: formData.get("edicao"),
      editora: formData.get("editora"),
      local: formData.get("local"),
      origem: formData.get("origem"),
      ano: formData.get("ano"),
      observacao: formData.get("observacao"),
      prazo_dias: prazoDias,
    };

    try {
      const resposta = await fetch("/livros/emprestar", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(dados),
      });

      const resultado = await resposta.json();

      if (resposta.ok) {
        alert("Empréstimo registrado com sucesso!");
        window.location.href = "/emprestimos-listagem";
      } else {
        alert(resultado.erro);
      }
    } catch (erro) {
      alert("Erro ao conectar com o servidor.");
    }
  });
}

function cancelar() {
  window.location.href = "/usuarios-listagem";
}
