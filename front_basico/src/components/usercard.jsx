import React from "react";

const UserCard = ({ user, onEdit, onDelete, onLogout }) => {

  console.log(user)

  return (
    <div style={{ border: "1px solid #ccc", padding: "20px", textAlign: "center" }}>
      <h3>Bem-vindo, {user.nome}</h3>
      <p>Email: {user.email}</p>
      <p>Senha: {user.senha}</p>
      <div>
        <button onClick={onEdit}>Editar</button>
        <button onClick={onDelete}>Deletar Conta</button>
        <button onClick={onLogout}>Deslogar</button>
      </div>
    </div>
  );
};

export default UserCard;
