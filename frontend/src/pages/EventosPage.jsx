// src/pages/EventosPage.jsx

import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import StatusButtons from "../components/StatusButtons"
import CityFilter from "../components/CityFilter"
import DateFilter from "../components/DateFilter"
import { supabase } from "../supabaseClient"
import { API_URL } from "../config"

function EventosPage({ sessao }) {

  // ─── ESTADOS ───────────────────────────────────────────────

  const [eventos, setEventos] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [cidadeSelecionada, setCidadeSelecionada] = useState("Todas")
  const [periodoSelecionado, setPeriodoSelecionado] = useState("")
  const [statusMap, setStatusMap] = useState({})


  // ─── AUTENTICAÇÃO ────────────────────────────────────────────

  async function entrarComGoogle() {
    await supabase.auth.signInWithOAuth({ provider: "google" })
  }

  async function sair() {
    await supabase.auth.signOut()
    setStatusMap({}) // limpa status ao deslogar, já que eram do usuário anterior
  }


  // ─── BUSCA DE DADOS ────────────────────────────────────────

  useEffect(() => {
    // Eventos são públicos — sempre busca, logado ou não
    fetch(`${API_URL}/events/?limit=200`)
      .then(r => r.json())
      .then(dadosEventos => {
        const ordenados = dadosEventos.sort(
          (a, b) => new Date(a.event_date) - new Date(b.event_date)
        )
        setEventos(ordenados)
        setCarregando(false)
      })
  }, [])

  useEffect(() => {
    // Status só é buscado se o usuário estiver logado
    if (!sessao) {
      setStatusMap({})
      return
    }

    fetch(`${API_URL}/status/`, {
      headers: {
        Authorization: `Bearer ${sessao.access_token}`
      }
    })
      .then(r => r.json())
      .then(dadosStatus => {
        const mapa = {}
        dadosStatus.forEach(s => { mapa[s.event_id] = s.status })
        setStatusMap(mapa)
      })
  }, [sessao])


  // ─── ATUALIZAÇÃO DE STATUS ─────────────────────────────────

  function atualizarStatus(eventoId, novoStatus) {
    setStatusMap(anterior => ({
      ...anterior,
      [eventoId]: novoStatus
    }))
  }


  // ─── LÓGICA DE FILTRO ──────────────────────────────────────

  const eventosFiltrados = eventos
    .filter(e => cidadeSelecionada === "Todas" || e.venue?.city === cidadeSelecionada)
    .filter(e => {
      if (periodoSelecionado === "") return true
      const d = new Date(e.event_date)
      return `${d.getMonth() + 1}/${d.getFullYear()}` === periodoSelecionado
    })

  function formatarData(dataISO) {
    return new Date(dataISO).toLocaleString("pt-BR", {
      day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    })
  }


  // ─── TELA DE LOADING ───────────────────────────────────────

  if (carregando) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <p className="text-white text-xl">Carregando eventos...</p>
      </div>
    )
  }


  // ─── TELA PRINCIPAL ────────────────────────────────────────

  return (
    <div className="bg-gray-900 min-h-screen p-8">

      {/* Cabeçalho */}
      <div className="flex justify-between items-start mb-2">
        <div>
          <h1 className="text-3xl font-bold text-white">🎵 BeatMap</h1>
          <p className="text-gray-400">{eventosFiltrados.length} eventos encontrados</p>
        </div>

        {/* Link para Minhas Interações + Indicador de login no topo */}
        <div className="flex items-center gap-4">
          <Link to="/minhas-interacoes" className="text-sm text-gray-300 hover:text-white underline">
            🎟️ Minhas Interações
          </Link>

          {sessao ? (
            <div className="flex items-center gap-3">
              {sessao.user.user_metadata?.avatar_url && (
                <img
                  src={sessao.user.user_metadata.avatar_url}
                  alt="Avatar"
                  className="w-8 h-8 rounded-full"
                />
              )}
              <span className="text-gray-300 text-sm">
                Olá, {sessao.user.user_metadata?.full_name || sessao.user.email}
              </span>
              <button
                onClick={sair}
                className="text-xs text-gray-400 hover:text-white underline"
              >
                Sair
              </button>
            </div>
          ) : (
            <button
              onClick={entrarComGoogle}
              className="text-sm text-gray-300 hover:text-white underline"
            >
              Entrar com Google
            </button>
          )}
        </div>
      </div>

      {/* Filtro por cidade */}
      <p className="text-gray-500 text-xs uppercase tracking-widest mb-2 mt-6">Cidade</p>
      <CityFilter
        eventos={eventos}
        cidadeSelecionada={cidadeSelecionada}
        aoSelecionar={setCidadeSelecionada}
      />

      {/* Filtro por mês */}
      <p className="text-gray-500 text-xs uppercase tracking-widest mb-2 mt-6">Data</p>
      <DateFilter
        eventos={eventos}
        periodoSelecionado={periodoSelecionado}
        aoSelecionar={setPeriodoSelecionado}
      />

      {/* Grid de cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
        {eventosFiltrados.map(evento => (
          <div
            key={evento.id}
            className="bg-gray-800 rounded-xl p-5 border border-gray-700"
          >
            <h2 className="text-white font-semibold text-lg mb-2">
              {evento.name}
            </h2>

            <p className="text-purple-400 text-sm mb-1">
              📍 {evento.venue?.name} — {evento.venue?.city}/{evento.venue?.state}
            </p>

            <p className="text-gray-400 text-sm mb-1">
              📅 {formatarData(evento.event_date)}
            </p>

            {evento.ticket_url && (
              <a
                href={evento.ticket_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-purple-400 text-xs hover:underline"
              >
                🎟️ Ver ingressos
              </a>
            )}

            <StatusButtons
              eventoId={evento.id}
              statusAtual={statusMap[evento.id]}
              aoAtualizar={atualizarStatus}
              sessao={sessao}
              aoExigirLogin={entrarComGoogle}
            />
          </div>
        ))}
      </div>

    </div>
  )
}

export default EventosPage