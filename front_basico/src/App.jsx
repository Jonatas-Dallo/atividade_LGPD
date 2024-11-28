import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/loginpage";
import UserPage from "./pages/userpage";
import TermosPage from "./pages/termospage"; // Importe a página de termos

const App = () => {
  const [user, setUser] = useState(null);

  return (
    <Router>
      <Routes>
        {/* Rota de login */}
        <Route path="/" element={<LoginPage setUserId={setUser} />} />
        
        {/* Rota de termos, onde o usuário aceita os termos obrigatórios */}
        <Route path="/termos" element={<TermosPage />} />
        
        {/* Verifica se o usuário está autenticado */}
        <Route
          path="/user"
          element={user ? <UserPage user={user} setUserId={setUser} /> : <Navigate to="/" />}
        />

        {/* Redireciona para o login se a URL não corresponder a nenhuma rota */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
};

export default App;
