import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import UserCard from "../components/usercard";

const apiUrl = "http://127.0.0.1:5000"; // Substitua pela sua URL

const UserPage = ({ user, setUser }) => {
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [updatedData, setUpdatedData] = useState({
    nome: user.nome,
    email: user.email,
    senha: user.senha, // Inicialmente vazia, pois não queremos exibir a senha
  });
  const [termos, setTermos] = useState([]);  // Armazenar os termos e decisões do usuário
  const [loading, setLoading] = useState(true);  // Indicador de carregamento dos dados

  // Função para capturar as alterações nos campos de edição
  const handleChange = (e) => {
    const { name, value } = e.target;
    setUpdatedData({ ...updatedData, [name]: value });
  };

  // Função que carrega os termos e consentimentos do usuário
  const fetchTermosUsuario = async () => {
    try {
      const response = await fetch(`${apiUrl}/termo_usuario/${user.id}`);
      const data = await response.json();

      if (response.ok) {
        // Atualiza o estado de termos com base nos dados retornados
        setTermos(data.termo.itens.map(item => ({
          ...item,
          autorizadoEmFrontend: item.autorizado === 1  // Marca como selecionado se autorizado = 1
        })));
      } else {
        alert("Erro ao carregar termos.");
      }
    } catch (error) {
      console.error("Erro ao carregar termos:", error);
      alert("Erro ao carregar termos.");
    } finally {
      setLoading(false);
    }
  };

  // Carregar os termos ao montar o componente
  useEffect(() => {
    fetchTermosUsuario();
  }, [user.id]);

  // Função que trata o envio da atualização de dados via PUT
  const handleEditSubmit = async () => {
    try {
      const response = await fetch(`${apiUrl}/usuario/${user.id}`, {
        method: "PUT", // Mude de POST para PUT
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nome: updatedData.nome,
          email: updatedData.email,
          senha: updatedData.senha,
        }),
      });
  
      console.log(response);
  
      if (response.ok) {
        const data = await response.json();
        alert(data.mensagem); // Mensagem de sucesso
        setUser({ ...user, ...updatedData }); // Atualiza o estado do usuário
        setIsEditing(false); // Fecha o formulário de edição
        window.location.reload();
      } else {
        alert("Erro ao atualizar usuário");
      }
    } catch (error) {
      console.error("Erro ao editar usuário:", error);
    }
  };

  const handleDelete = async () => {
    try {
      const response = await fetch(`${apiUrl}/usuario/${user.id}`, {
        method: "DELETE",
      });
      if (response.ok) {
        alert("Conta deletada com sucesso!");
        navigate("/");
      } else {
        alert("Erro ao deletar conta.");
      }
    } catch (error) {
      console.error(error);
      alert("Erro ao conectar ao backend.");
    }
  };

  const handleLogout = () => {
    navigate("/");
  };

  // Função que envia as alterações de consentimento
  const handleConsentimentoSubmit = async () => {
    // Filtra os itens não obrigatórios com alterações
    const decisoesAlteradas = termos.filter(item => !item.obrigatorio && item.autorizado !== item.autorizadoEmFrontend);
    
    if (decisoesAlteradas.length === 0) {
      alert("Nenhuma alteração válida.");
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/termos/update/${user.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          decisoes: decisoesAlteradas.map(item => ({
            item_numero: item.item_numero,
            autorizado: item.autorizadoEmFrontend
          })),
        }),
      });

      if (response.ok) {
        const data = await response.json();
        alert(data.mensagem); // Mensagem de sucesso
        fetchTermosUsuario(); // Recarrega os termos após atualização
      } else {
        alert("Erro ao atualizar consentimentos.");
      }
    } catch (error) {
      console.error("Erro ao atualizar consentimentos:", error);
      alert("Erro ao atualizar consentimentos.");
    }
  };

  // Alteração do consentimento do item
  const handleConsentimentoChange = (item_numero, autorizadoEmFrontend) => {
    setTermos(termos.map(item => 
      item.item_numero === item_numero 
        ? { ...item, autorizadoEmFrontend } 
        : item
    ));
  };

  return (
    <div>
      {isEditing ? (
        <div>
          <h2>Editar Usuário</h2>
          <input
            type="text"
            name="nome"
            value={updatedData.nome}
            onChange={handleChange}
            placeholder="Novo Nome"
          />
          <input
            type="email"
            name="email"
            value={updatedData.email}
            onChange={handleChange}
            placeholder="Novo Email"
          />
          <input
            type="password"
            name="senha"
            value={updatedData.senha}
            onChange={handleChange}
            placeholder="Nova Senha"
          />
          <button onClick={handleEditSubmit}>Salvar alterações</button>
          <button onClick={() => setIsEditing(false)}>Cancelar</button>
        </div>
      ) : (
        <UserCard
          user={user}
          onEdit={() => setIsEditing(true)} // Abre o formulário de edição
          onDelete={handleDelete}
          onLogout={handleLogout}
        />
      )}
      
      {/* Exibir os termos e decisões do usuário */}
      {!loading && (
        <div>
          <h3>Consentimentos</h3>
          {termos.map(item => (
            <div key={item.item_numero}>
              <p>{item.mensagem}</p>
              <label>
                <input
                  type="checkbox"
                  checked={item.autorizadoEmFrontend}
                  disabled={item.obrigatorio} // Não permite alterar itens obrigatórios
                  onChange={(e) => handleConsentimentoChange(item.item_numero, e.target.checked)}
                />
                {item.obrigatorio ? "Obrigatório" : "Consentido"}
              </label>
            </div>
          ))}
          <button onClick={handleConsentimentoSubmit}>Salvar Consentimentos</button>
        </div>
      )}
    </div>
  );
};

export default UserPage;
