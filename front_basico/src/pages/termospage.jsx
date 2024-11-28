import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";

const TermosPage = () => {
  const navigate = useNavigate();
  const location = useLocation(); // Usado para pegar o id do usuário da navegação
  const [termosAceitos, setTermosAceitos] = useState({});
  const [termos, setTermos] = useState([]);

  // Pega o id do usuário da navegação
  const userId = location.state?.id;

  console.log(userId)

  useEffect(() => {
    const fetchTermos = async () => {
      try {
        const response = await fetch("http://localhost:5000/termos");
        const data = await response.json();
        setTermos(data.termo); // Assumindo que 'termo' é a lista de itens
      } catch (error) {
        console.error("Erro ao carregar os termos:", error);
      }
    };

    fetchTermos();
  }, []);

  const handleTermChange = (item, value) => {
    setTermosAceitos({ ...termosAceitos, [item]: value });
  };

  const handleSubmitTermos = async () => {
    // Verifica se todos os termos obrigatórios foram aceitos
    const termosObrigatoriosNaoAceitos = termos.filter(
      (termo) => termo.obrigatorio === 1 && !termosAceitos[termo.item]
    );

    if (termosObrigatoriosNaoAceitos.length > 0) {
      // Exibe uma mensagem informando que os termos obrigatórios precisam ser selecionados
      alert("Por favor, aceite todos os termos obrigatórios antes de continuar.");
      return; // Impede o envio caso algum termo obrigatório não tenha sido aceito
    }

    // Completa os termos opcionais não selecionados com valor 0
    const consentDecisions = termos.map((termo) => ({
      item_numero: termo.item,
      autorizado: termosAceitos[termo.item] === true ? 1 : 0, // Registra como 1 (aceito) ou 0 (não aceito)
    }));

    // Envia as decisões de consentimento para o backend, utilizando o userId
    try {
      const consentResponse = await fetch(`http://localhost:5000/autorizacao_usuario/${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decisoes: consentDecisions }),
      });

      if (consentResponse.ok) {
        console.log("Consentimentos registrados.");
        navigate("/login"); // Redireciona para a página do usuário após aceitar os termos
      } else {
        alert("Erro ao registrar consentimentos.");
      }
    } catch (error) {
      console.error("Erro ao conectar ao backend:", error);
      alert("Erro ao registrar consentimentos.");
    }
  };

  return (
    <div>
      <h1>Novos Termos de Uso! Aceite para Continuar</h1>
      {termos.map((termo) => (
        <div key={termo.item}>
          <label>
            <input
              type="checkbox"
              checked={termosAceitos[termo.item] || false}
              onChange={(e) => handleTermChange(termo.item, e.target.checked)}
              required={termo.obrigatorio === 1}
            />
            {termo.mensagem} {termo.obrigatorio === 0 ? "(opcional)" : ""}
          </label>
        </div>
      ))}

      <button onClick={handleSubmitTermos}>Aceitar e Continuar</button>
    </div>
  );
};

export default TermosPage;
