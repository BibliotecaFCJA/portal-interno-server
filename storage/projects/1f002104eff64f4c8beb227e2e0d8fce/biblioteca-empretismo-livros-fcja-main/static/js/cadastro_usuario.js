document.getElementById("btnCancelar").onclick = () => {
  window.location.href = "/usuarios-listagem";
};

document.getElementById("btnSalvar").onclick = async () => {
  const dados = {
    nome: document.getElementById("nome").value.trim(),
    email: document.getElementById("email").value.trim(),
    telefone: document.getElementById("telefone").value.trim(),
    endereco: document.getElementById("endereco").value.trim(),
    matricula: document.getElementById("matricula").value.trim(),
    tipo: document.getElementById("tipo").value.toLowerCase(),
    setor: document.getElementById("setor").value.trim(),
  };

  if (
    !dados.nome ||
    !dados.email ||
    !dados.telefone ||
    !dados.endereco ||
    !dados.matricula ||
    !dados.tipo ||
    !dados.setor
  ) {
    alert("Preencha todos os campos");
    return;
  }

  try {
    const resposta = await fetch("/usuarios", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(dados),
    });

    const resultado = await resposta.json();

    if (resposta.ok) {
      alert("Usuário cadastrado com sucesso");

      window.location.href = "/usuarios-listagem";
    } else {
      alert(resultado.erro);
    }
  } catch (erro) {
    alert("Erro ao cadastrar usuário");
  }
};
