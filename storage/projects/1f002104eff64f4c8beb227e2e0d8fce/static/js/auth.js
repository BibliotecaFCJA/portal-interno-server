document
  .getElementById("formLogin")
  .addEventListener("submit", async function (event) {
    event.preventDefault();

    const email = document.querySelector("[name='email']").value.trim();
    const senha = document.querySelector("[name='senha']").value.trim();

    if (!email || !senha) {
      alert("Preencha email e senha.");
      return;
    }

    const dados = {
      email: email,
      senha: senha,
    };

    try {
      const resposta = await fetch("/login/adm", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(dados),
      });

      const resultado = await resposta.json();

      if (resposta.ok) {
        alert("Login realizado com sucesso!");

        window.location.href = "/usuarios-listagem";
      } else {
        alert(resultado.erro);
      }
    } catch (erro) {
      alert("Erro ao conectar com o servidor.");
    }
  });
