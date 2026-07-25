import { useState, useEffect } from "react"
import { supabase } from "./supabaseClient"
import EventosPage from "./pages/EventosPage"

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

  return <EventosPage sessao={sessao} />
}

export default App