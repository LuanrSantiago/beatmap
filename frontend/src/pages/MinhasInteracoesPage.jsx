// src/pages/MinhasInteracoesPage.jsx

import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import StatusButtons from "../components/StatusButtons"
import { supabase } from "../supabaseClient"
import { API_URL } from "../config"

function MinhasInteracoesPage({ sessao }) {

  const [interacoes, setInteracoes] = useState([])
  const [carregando, setCarregando] = useState(true)

  async function entrarComGoogle() {
    await supabase.auth.signInWithOAuth({ provider: "google" })
  }

  useEffect(() => {
    if (!sessao) {
      setCarregando(false)
      return
    }

    fetch(`${API_URL}/status/detalhado/`, {
      headers: {
        Authorization: `Bearer ${sessao.access_token}`
      }
    })
      .then(r => r.json())
      .then(dados => {
        const ordenados = dados.sort(
          (a, b) => new Date(b.event.event_date) - new Date(a.event.event_date)
        )
        setInteracoes(ordenados)
        setCarregando(false)
      })
  }, [sessao])

  function atualizarStatus(eventoId, novoStatus) {
    setInteracoes(anterior =>
      anterior.map(item =>
        item.event_id === eventoId ? { ...item, status: novoStatus } : item
      )
    )
  }

  function formatarData(dataISO) {
    return new Date(dataISO).toLocaleString("pt-BR", {
      day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    })
  }

  function eventoJaPassou(dataISO) {
    return new Date(dataISO) < new Date()
  }


  // ─── Não logado ──────────────────────────────────────────────

  if (!carregando && !sessao) {
    return (
      <div className="bg-gray-900 min-h-screen p-8 flex flex-col items-center justify-center gap-4">
        <p className="text-gray-300">Você precisa estar logado para ver suas interações.</p>
        <button
          onClick={entrarComGoogle}
          className="text-sm text-purple-400 hover:text-purple-300 underline"
        >
          Entrar com Google
        </button>
        <Link to="/" className="text-xs text-gray-500 hover:text-gray-300 underline mt-4">
          ← Voltar para eventos
        </Link>
      </div>
    )
  }


  // ─── Loading ─────────────────────────────────────────────────

  if (carregando) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <p className="text-white text-xl">Carregando suas interações...</p>
      </div>
    )
  }


  // ─── Tela principal ──────────────────────────────────────────

  return (
    <div className="bg-gray-900 min-h-screen p-8">

      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">🎟️ Minhas Interações</h1>
          <p className="text-gray-400">{interacoes.length} evento(s) marcado(s)</p>
        </div>
        <Link to="/" className="text-sm text-gray-300 hover:text-white underline">
          ← Voltar para eventos
        </Link>
      </div>

      {interacoes.length === 0 ? (
        <p className="text-gray-500">Você ainda não marcou nenhum evento.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {interacoes.map(item => {
            const passou = eventoJaPassou(item.event.event_date)

            return (
              <div
                key={item.id}
                className={`bg-gray-800 rounded-xl p-5 border border-gray-700 ${passou ? "opacity-60" : ""}`}
              >
                {passou && (
                  <span className="text-xs text-gray-500 uppercase tracking-wide">Evento passado</span>
                )}

                <h2 className="text-white font-semibold text-lg mb-2 mt-1">
                  {item.event.name}
                </h2>

                <p className="text-purple-400 text-sm mb-1">
                  📍 {item.event.venue?.name} — {item.event.venue?.city}/{item.event.venue?.state}
                </p>

                <p className="text-gray-400 text-sm mb-1">
                  📅 {formatarData(item.event.event_date)}
                </p>

                {item.event.ticket_url && (
                  <a
                    href={item.event.ticket_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-purple-400 text-xs hover:underline"
                  >
                    🎟️ Ver ingressos
                  </a>
                )}

                <StatusButtons
                  eventoId={item.event_id}
                  statusAtual={item.status}
                  aoAtualizar={atualizarStatus}
                  sessao={sessao}
                  aoExigirLogin={entrarComGoogle}
                />
              </div>
            )
          })}
        </div>
      )}

    </div>
  )
}

export default MinhasInteracoesPage