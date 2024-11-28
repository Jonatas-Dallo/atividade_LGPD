import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const LoginPage = ({ setUserId }) => {
  const [formData, setFormData] = useState({ email: "", senha: "" });
  const [registerData, setRegisterData] = useState({ nome: "", email: "", senha: "" });
  const [termos, setTermos] = useState([]);
  const [termosAceitos, setTermosAceitos] = useState({});
  const navigate = useNavigate();

  // Fetch terms from the API
  useEffect(() => {
    const fetchTermos = async () => {
      try {
        const response = await fetch("http://localhost:5000/termos");
        if (response.ok) {
          const data = await response.json();
          setTermos(data.termo);
        } else {
          console.error("Erro ao buscar os termos");
        }
      } catch (error) {
        console.error("Erro ao conectar ao backend:", error);
      }
    };
    fetchTermos();
  }, []);

  const handleChangeLogin = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleChangeRegister = (e) => {
    const { name, value } = e.target;
    setRegisterData({ ...registerData, [name]: value });
  };

  const handleTermChange = (item, value) => {
    setTermosAceitos({ ...termosAceitos, [item]: value });
  };

  const handleSubmitLogin = async (e) => {
    e.preventDefault();
  
    try {
      const response = await fetch("http://localhost:5000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
  
      if (response.ok) {
        const data = await response.json();
        if (data.mensagem && data.mensagem.includes("Novo termo de consentimento")) {
          // Redireciona para a página de termos, passando o id do usuário
          navigate("/termos", { state: { id: data.id } });
        } else if (data.id) {
          setUserId(data);
          navigate("/user");
        } else {
          alert("Resposta inesperada do servidor");
        }
      } else {
        alert("Email ou senha incorretos");
      }
    } catch (error) {
      console.error("Erro ao conectar ao backend:", error);
      alert("Erro ao fazer login");
    }
  };
  

  const handleSubmitRegister = async (e) => {
    e.preventDefault();

    // Validate mandatory terms
    const obrigatoriosNaoAceitos = termos
      .filter((termo) => termo.obrigatorio)
      .some((termo) => !termosAceitos[termo.item]);

    if (obrigatoriosNaoAceitos) {
      alert("Você deve aceitar todos os termos obrigatórios.");
      return;
    }

    try {
      // Create user
      const userResponse = await fetch("http://localhost:5000/usuario/criar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(registerData),
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        console.log("Usuário cadastrado:", userData);

        // Send user consent
        const consentDecisions = termos.map((termo) => ({
          item_numero: termo.item,
          autorizado: !!termosAceitos[termo.item],
        }));

        const consentResponse = await fetch(
          `http://localhost:5000/autorizacao_usuario/${userData.id}`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ decisoes: consentDecisions }),
          }
        );

        if (consentResponse.ok) {
          console.log("Decisões de consentimento registradas.");
          setUserId(userData);
          navigate("/user");
        } else {
          alert("Erro ao registrar consentimento.");
        }
      } else {
        alert("Erro ao cadastrar usuário");
      }
    } catch (error) {
      console.error("Erro ao conectar ao backend:", error);
      alert("Erro ao fazer cadastro");
    }
  };

  return (
    <div>
      <h1>Login</h1>
      <form onSubmit={handleSubmitLogin}>
        <input
          type="email"
          name="email"
          placeholder="Email"
          value={formData.email}
          onChange={handleChangeLogin}
          required
        />
        <input
          type="password"
          name="senha"
          placeholder="Senha"
          value={formData.senha}
          onChange={handleChangeLogin}
          required
        />
        <button type="submit">Entrar</button>
      </form>

      <hr />

      <h1>Cadastro</h1>
      <form onSubmit={handleSubmitRegister}>
        <input
          type="text"
          name="nome"
          placeholder="Nome"
          value={registerData.nome}
          onChange={handleChangeRegister}
          required
        />
        <input
          type="email"
          name="email"
          placeholder="Email"
          value={registerData.email}
          onChange={handleChangeRegister}
          required
        />
        <input
          type="password"
          name="senha"
          placeholder="Senha"
          value={registerData.senha}
          onChange={handleChangeRegister}
          required
        />

        <h2>Termos de Uso</h2>
        {termos.map((termo) => (
          <div key={termo.item}>
            <label>
              <input
                type="checkbox"
                checked={termosAceitos[termo.item] || false}
                onChange={(e) => handleTermChange(termo.item, e.target.checked)}
                required={termo.obrigatorio === 1}
              />
              {termo.mensagem} {termo.obrigatorio ? "*" : ""}
            </label>
          </div>
        ))}

        <button type="submit">Cadastrar</button>
      </form>
    </div>
  );
};

export default LoginPage;
