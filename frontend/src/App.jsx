import { useState, useEffect } from "react"
import { BrowserRouter, Routes, Route } from "react-router-dom"
import { supabase } from "./supabaseClient"
import EventosPage from "./pages/EventosPage"
import MinhasInteracoesPage from "./pages/MinhasInteracoesPage"

function App() {
  const [sessao, setSessao] = useState(null)
  const [carregandoSessao, setCarregandoSessao] = useState(true)

  useEffect(() => {
    // Verifica se já existe uma sessão salva (ex: usuário logou antes,
    // ou acabou de voltar do redirecionamento do Google)
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSessao(session)
      setCarregandoSessao(false)
    })

    // Fica "escutando" mudanças de login/logout daqui pra frente
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_evento, session) => {
        setSessao(session)
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  if (carregandoSessao) {
    return <div className="text-white p-8">Carregando...</div>
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<EventosPage sessao={sessao} />} />
        <Route path="/minhas-interacoes" element={<MinhasInteracoesPage sessao={sessao} />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App