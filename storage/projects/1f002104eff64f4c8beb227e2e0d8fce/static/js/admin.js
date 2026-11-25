document
  .getElementById("formCadastroAdmin")
  .addEventListener("submit", async function (event) {
    event.preventDefault();

    const nome = document.querySelector("[name='nome']").value.trim();
    const email = document.querySelector("[name='email']").value.trim();
    const senha = document.querySelector("[name='senha']").value.trim();

    if (!nome || !email || !senha) {
      alert("Todos os campos são obrigatórios.");
      return;
    }

    const dados = {
      nome: nome,
      email: email,
      senha: senha,
    };

    try {
      const resposta = await fetch("/adm/cadastro/admin", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(dados),
      });

      const resultado = await resposta.json();

      if (resposta.ok) {
        alert("Administrador cadastrado com sucesso!");
        window.location.href = "/";
      } else {
        alert(resultado.erro);
      }
    } catch (erro) {
      alert("Erro ao conectar com o servidor.");
    }
  });
